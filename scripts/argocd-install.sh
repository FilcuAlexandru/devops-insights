#!/bin/sh
# Install Argo CD into a Kubernetes cluster and make it reachable with the login admin / admin.
#
#   scripts/argocd-install.sh <kube-context>
#
# - the UI is published as a NodePort (https://localhost:30443 on a kind cluster created from
#   deploy/kubernetes/kind/cluster.yaml)
# - an existing installation is upgraded to ARGOCD_VERSION unless SKIP_INSTALL=1
# - the admin password is set to "admin" by writing a bcrypt hash into argocd-secret
#
# This changes the cluster you point it at, so the context is a required argument.
set -eu

ARGOCD_VERSION="${ARGOCD_VERSION:-v3.5.3}"
NODE_PORT="${ARGOCD_NODE_PORT:-30443}"
# bcrypt hash of "admin" (single quotes on purpose: the hash contains literal $ characters)
# shellcheck disable=SC2016
ADMIN_PASSWORD_HASH='$2b$10$xttjzDKs7mGl.C/e5j/ZAeFwuhTqig.e2uD7Xj7S6HSXtD0Y4iOdi'

if [ $# -ne 1 ]; then
    echo "usage: $0 <kube-context>" >&2
    echo "available contexts:" >&2
    kubectl config get-contexts -o name >&2
    exit 2
fi

CONTEXT="$1"
KUBECTL="kubectl --context $CONTEXT"

# Ask before changing a cluster, unless running non-interactively or ASSUME_YES=1.
if [ -t 0 ] && [ "${ASSUME_YES:-}" != "1" ]; then
    printf "Install Argo CD %s into '%s' and set its admin password to 'admin'? [y/N] " "$ARGOCD_VERSION" "$CONTEXT"
    read -r answer
    [ "$answer" = "y" ] || { echo "Aborted."; exit 1; }
fi

echo "Installing Argo CD $ARGOCD_VERSION into context '$CONTEXT'"

# SKIP_INSTALL=1 keeps an existing Argo CD as it is and only sets the password and the NodePort.
if [ "${SKIP_INSTALL:-}" != "1" ]; then
    $KUBECTL create namespace argocd --dry-run=client -o yaml | $KUBECTL apply -f -
    $KUBECTL apply -n argocd --server-side --force-conflicts \
        -f "https://raw.githubusercontent.com/argoproj/argo-cd/$ARGOCD_VERSION/manifests/install.yaml"
fi

echo "Waiting for the Argo CD server..."
$KUBECTL -n argocd rollout status deployment/argocd-server --timeout=300s

$KUBECTL -n argocd patch secret argocd-secret --type merge -p \
    "{\"stringData\":{\"admin.password\":\"$ADMIN_PASSWORD_HASH\",\"admin.passwordMtime\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"

$KUBECTL -n argocd patch service argocd-server --type merge -p \
    "{\"spec\":{\"type\":\"NodePort\",\"ports\":[{\"name\":\"http\",\"port\":80,\"targetPort\":8080},{\"name\":\"https\",\"port\":443,\"targetPort\":8080,\"nodePort\":$NODE_PORT}]}}"

echo
echo "Argo CD is ready:  https://localhost:$NODE_PORT   (login: admin / admin)"
echo "The certificate is self-signed, so the browser will show a warning."
