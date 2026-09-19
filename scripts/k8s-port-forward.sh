#!/bin/sh
# Publish the deployed components on localhost using kubectl port-forward, on the same ports
# a kind cluster from deploy/kubernetes/kind/cluster.yaml would use. Handy for clusters that
# were created without port mappings.
#
#   scripts/k8s-port-forward.sh [namespace] [release]      (press Ctrl+C to stop)
set -eu

NAMESPACE="${1:-devops-insights}"
RELEASE="${2:-devops-insights}"

# Stop only the port-forwards started by this script.
trap 'kill $(jobs -p) 2>/dev/null || true' INT TERM EXIT

forward() {
    # forward <service> <local port> <service port> <label> [scheme]
    kubectl -n "$NAMESPACE" port-forward "svc/$RELEASE-$1" "$2:$3" >/dev/null &
    printf '  %-16s %s%s\n' "$4" "${5:+$5://}localhost:" "$2"
}

echo "Forwarding ($NAMESPACE / $RELEASE), every login is admin / admin:"
forward frontend 30080 8080 "Web application" http
forward backend 30800 8000 "API" http
forward grafana 30300 3000 "Grafana" http
forward prometheus 30900 9090 "Prometheus" http
forward postgresql 30432 5432 "PostgreSQL"
forward ollama 31434 11434 "Ollama" http

if kubectl -n argocd get svc argocd-server >/dev/null 2>&1; then
    kubectl -n argocd port-forward svc/argocd-server 30443:443 >/dev/null &
    printf '  %-16s %s\n' "Argo CD" "https://localhost:30443"
fi

echo "(press Ctrl+C to stop)"
wait
