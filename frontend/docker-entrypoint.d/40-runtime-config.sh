#!/bin/sh
# Generate /tmp/runtime/config.js from environment variables so the same image can be used
# with Docker Compose, Kubernetes and OpenShift. /tmp is writable under any user ID.
set -eu

: "${PLATFORM_ENVIRONMENT:=Local}"
: "${LINK_API_DOCS:=}"
: "${LINK_GRAFANA:=}"
: "${LINK_PROMETHEUS:=}"
: "${LINK_ARGOCD:=}"
: "${LINK_OLLAMA:=}"
: "${LINK_POSTGRES:=}"
export PLATFORM_ENVIRONMENT LINK_API_DOCS LINK_GRAFANA LINK_PROMETHEUS LINK_ARGOCD LINK_OLLAMA LINK_POSTGRES

mkdir -p /tmp/runtime
# The variable list is quoted on purpose: envsubst must receive it unexpanded.
# shellcheck disable=SC2016
envsubst '${PLATFORM_ENVIRONMENT} ${LINK_API_DOCS} ${LINK_GRAFANA} ${LINK_PROMETHEUS} ${LINK_ARGOCD} ${LINK_OLLAMA} ${LINK_POSTGRES}' \
    < /etc/nginx/config.js.template > /tmp/runtime/config.js

echo "40-runtime-config.sh: wrote /tmp/runtime/config.js"
