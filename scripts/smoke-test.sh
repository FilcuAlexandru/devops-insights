#!/bin/sh
# Check that a running DevOps Insights deployment works, end to end, from the outside.
#
#   FRONTEND_URL=http://localhost:8080 \
#   GRAFANA_URL=http://localhost:3000 PROMETHEUS_URL=http://localhost:9090 \
#   scripts/smoke-test.sh
#
# FRONTEND_URL is required, the others are optional and add checks. Logins are admin / admin.
#   INSECURE=1              accept self-signed certificates (OpenShift Local, Argo CD, ...)
#   WAIT_FOR_COLLECTION=1   wait until the collector's first run has finished (up to 5 minutes)
# Exit status: 0 when every check passes, 1 otherwise.
set -u

: "${FRONTEND_URL:?Set FRONTEND_URL, for example http://localhost:8080}"
CURL="curl -s --max-time 20"
[ "${INSECURE:-}" = "1" ] && CURL="$CURL -k"

failures=0

pass() { printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; failures=$((failures + 1)); }

# check <description> <expected substring> <curl arguments...>: the response body must contain it
check_body() {
    description="$1"; expected="$2"; shift 2
    # shellcheck disable=SC2086
    body=$($CURL "$@" 2>/dev/null) || body=""
    case "$body" in *"$expected"*) pass "$description" ;; *) fail "$description (expected: $expected)" ;; esac
}

# check_status <description> <expected HTTP status> <curl arguments...>
check_status() {
    description="$1"; expected="$2"; shift 2
    # shellcheck disable=SC2086
    status=$($CURL -o /dev/null -w '%{http_code}' "$@" 2>/dev/null) || status="000"
    if [ "$status" = "$expected" ]; then
        pass "$description"
    else
        fail "$description (HTTP $status, expected $expected)"
    fi
}

echo "Web application  $FRONTEND_URL"
check_status "health endpoint answers"              200 "$FRONTEND_URL/healthz"
check_body   "the page is served"                   "DevOps Insights" "$FRONTEND_URL/"
check_status "runtime config is generated"          200 "$FRONTEND_URL/config.js"
check_status "API docs are reachable through nginx" 200 "$FRONTEND_URL/api/docs"
check_body   "backend is connected to the database" '"database_ok":true' "$FRONTEND_URL/api/status"
check_status "dashboard endpoint works"             200 "$FRONTEND_URL/api/dashboard"
check_status "technologies endpoint works"          200 "$FRONTEND_URL/api/technologies"
check_status "repositories endpoint works"          200 "$FRONTEND_URL/api/repositories"
check_status "unknown repository is a clean 404"    404 "$FRONTEND_URL/api/repositories/00000000-0000-0000-0000-000000000000"

if [ "${WAIT_FOR_COLLECTION:-}" = "1" ]; then
    echo "Waiting for the first collection (up to 5 minutes)..."
    attempts=0
    while [ $attempts -lt 60 ]; do
        runs=$($CURL "$FRONTEND_URL/api/collection/runs?limit=1" 2>/dev/null || echo "[]")
        case "$runs" in *'"status":"running"'*|"[]") sleep 5; attempts=$((attempts + 1)) ;; *) break ;; esac
    done
fi

runs=$($CURL "$FRONTEND_URL/api/collection/runs?limit=1" 2>/dev/null || echo "[]")
case "$runs" in
    *'"status":"succeeded"'*) pass "last collection succeeded" ;;
    "[]") echo "  INFO  no collection has run yet (not a failure)" ;;
    *'"status":"running"'*) echo "  INFO  a collection is still running" ;;
    *) fail "last collection did not succeed: $runs" ;;
esac

if [ -n "${GRAFANA_URL:-}" ]; then
    echo "Grafana  $GRAFANA_URL"
    check_status "health endpoint answers"           200 "$GRAFANA_URL/api/health"
    check_status "login admin / admin works"         200 -u admin:admin "$GRAFANA_URL/api/org"
    check_status "a wrong password is rejected"      401 -u admin:wrong "$GRAFANA_URL/api/org"
    check_body   "Prometheus datasource is healthy"  '"status":"OK"' -u admin:admin "$GRAFANA_URL/api/datasources/uid/prometheus/health"
    check_body   "the DevOps Insights dashboard exists" "devops-insights" -u admin:admin "$GRAFANA_URL/api/search?query=DevOps"
fi

if [ -n "${PROMETHEUS_URL:-}" ]; then
    echo "Prometheus  $PROMETHEUS_URL"
    check_status "requires a login"                  401 "$PROMETHEUS_URL/-/healthy"
    check_status "login admin / admin works"         200 -u admin:admin "$PROMETHEUS_URL/-/healthy"
    targets=$($CURL -u admin:admin "$PROMETHEUS_URL/api/v1/targets" 2>/dev/null || echo "")
    for job in backend collector; do
        case "$targets" in
            *"\"job\":\"$job\""*) pass "target '$job' is discovered" ;;
            *) fail "target '$job' is not discovered" ;;
        esac
    done
    case "$targets" in *'"health":"down"'*) fail "a scrape target is down" ;; *) pass "no scrape target is down" ;; esac
fi

echo
if [ $failures -eq 0 ]; then
    printf '\033[32mAll checks passed.\033[0m\n'
else
    printf '\033[31m%d check(s) failed.\033[0m\n' $failures
    exit 1
fi
