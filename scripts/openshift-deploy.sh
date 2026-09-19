#!/bin/sh
# Build the images inside OpenShift, install the Helm chart and verify the result.
#
#   oc login ...                     (see docs/openshift.md for OpenShift Local)
#   scripts/openshift-deploy.sh      or:  make openshift-deploy
#
# Options (environment variables):
#   PROJECT=devops-insights   OpenShift project to use (created if missing)
#   APPS_DOMAIN=...           apps domain; detected from the console URL when not set
#   OLLAMA=false              skip the AI runtime (saves about 4 GiB of memory)
#   SKIP_BUILD=1              reuse images that were already built
#   SMOKE_TEST=0              do not run scripts/smoke-test.sh at the end
#
# Safe to run again: it upgrades the existing release.
set -eu

cd "$(dirname "$0")/.."

PROJECT="${PROJECT:-devops-insights}"
RELEASE="${RELEASE:-devops-insights}"
CHART=deploy/helm/devops-insights
REGISTRY=image-registry.openshift-image-registry.svc:5000

for tool in oc helm; do
    command -v "$tool" >/dev/null || { echo "'$tool' is required but was not found in PATH." >&2; exit 1; }
done

oc whoami >/dev/null 2>&1 || { echo "You are not logged in. Run 'oc login ...' first." >&2; exit 1; }

echo "Cluster : $(oc whoami --show-server)"
echo "User    : $(oc whoami)"
echo "Project : $PROJECT"

if oc get project "$PROJECT" >/dev/null 2>&1; then
    oc project "$PROJECT" >/dev/null
else
    oc new-project "$PROJECT" >/dev/null
fi

if [ -z "${APPS_DOMAIN:-}" ]; then
    APPS_DOMAIN=$(oc whoami --show-console | sed -E 's#^https?://console-openshift-console\.##')
fi
echo "Domain  : $APPS_DOMAIN"

if [ "${SKIP_BUILD:-}" != "1" ]; then
    echo "==> Building images in the cluster"
    oc apply -f deploy/openshift/build.yaml
    oc start-build devops-insights-backend --from-dir=backend --follow
    oc start-build devops-insights-frontend --from-dir=frontend --follow
fi

echo "==> Installing the Helm chart"
# Not "helm --wait": wait for the workloads ourselves so a slow model download does not fail the install.
helm upgrade --install "$RELEASE" "$CHART" \
    -f "$CHART/values-openshift.yaml" \
    --set route.appsDomain="$APPS_DOMAIN" \
    --set backend.image.repository="$REGISTRY/$PROJECT/devops-insights-backend" \
    --set frontend.image.repository="$REGISTRY/$PROJECT/devops-insights-frontend" \
    --set ollama.enabled="${OLLAMA:-true}" \
    --namespace "$PROJECT"

echo "==> Waiting for the workloads to become ready"
for deployment in backend collector frontend prometheus grafana; do
    oc rollout status "deployment/$RELEASE-$deployment" --timeout=600s
done
oc rollout status "statefulset/$RELEASE-postgresql" --timeout=600s

echo
echo "Routes (every login is admin / admin):"
oc get routes -o custom-columns='COMPONENT:.metadata.name,ADDRESS:.spec.host' --no-headers |
    while read -r name host; do printf '  %-12s https://%s\n' "$name" "$host"; done

if [ "${SMOKE_TEST:-1}" != "0" ]; then
    echo
    echo "==> Smoke test"
    INSECURE=1 WAIT_FOR_COLLECTION=1 \
        FRONTEND_URL="https://frontend-$PROJECT.$APPS_DOMAIN" \
        GRAFANA_URL="https://grafana-$PROJECT.$APPS_DOMAIN" \
        PROMETHEUS_URL="https://prometheus-$PROJECT.$APPS_DOMAIN" \
        scripts/smoke-test.sh
fi
