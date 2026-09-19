#!/bin/sh
# Print the address and login of every component.
#
#   scripts/urls.sh compose      Docker Compose
#   scripts/urls.sh kind         local kind cluster (deploy/kubernetes/kind/cluster.yaml)
#   scripts/urls.sh openshift    routes of the current OpenShift project (needs "oc")
set -eu

row() { printf '  %-16s %-46s %s\n' "$1" "$2" "$3"; }

table() {
    printf '\n  %-16s %-46s %s\n' COMPONENT ADDRESS LOGIN
    row "Web application" "$1" "no login"
    row "API docs" "$2" "no login"
    row "Grafana" "$3" "admin / admin"
    row "Prometheus" "$4" "admin / admin"
    row "PostgreSQL" "$5" "admin / admin  (database devops_insights)"
    row "Ollama" "$6" "no login"
    [ -n "${7:-}" ] && row "Argo CD" "$7" "admin / admin"
    echo
}

case "${1:-compose}" in
    compose)
        table http://localhost:8080 http://localhost:8000/api/docs http://localhost:3000 \
            http://localhost:9090 localhost:5432 http://localhost:11434
        ;;
    kind)
        table http://localhost:30080 http://localhost:30800/api/docs http://localhost:30300 \
            http://localhost:30900 localhost:30432 http://localhost:31434 https://localhost:30443
        ;;
    openshift)
        command -v oc >/dev/null || { echo "The 'oc' command is required." >&2; exit 1; }
        echo
        oc get routes -o custom-columns='COMPONENT:.metadata.name,ADDRESS:.spec.host' --no-headers |
            while read -r name host; do
                case "$name" in
                    backend) row "API docs" "https://$host/api/docs" "no login" ;;
                    grafana | prometheus) row "$name" "https://$host" "admin / admin" ;;
                    *) row "$name" "https://$host" "no login" ;;
                esac
            done
        echo
        echo "  Argo CD (OpenShift GitOps): oc get route openshift-gitops-server -n openshift-gitops"
        echo
        ;;
    *)
        echo "usage: $0 compose|kind|openshift" >&2
        exit 2
        ;;
esac
