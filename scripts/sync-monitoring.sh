#!/bin/sh
# The Grafana dashboard and dashboard provider are stored once in monitoring/ (used by Docker
# Compose) and copied into the Helm chart, because a chart can only read files inside itself.
# Run this after editing them; CI fails when the copies are out of date (--check).
set -eu

cd "$(dirname "$0")/.."

CHART_FILES=deploy/helm/devops-insights/files/grafana

if [ "${1:-}" = "--check" ]; then
    diff -u monitoring/grafana/dashboards/devops-insights.json "$CHART_FILES/dashboards/devops-insights.json"
    diff -u monitoring/grafana/provisioning/dashboards/dashboards.yml "$CHART_FILES/dashboards.yml"
    echo "Monitoring files are in sync."
    exit 0
fi

mkdir -p "$CHART_FILES/dashboards"
cp monitoring/grafana/dashboards/devops-insights.json "$CHART_FILES/dashboards/devops-insights.json"
cp monitoring/grafana/provisioning/dashboards/dashboards.yml "$CHART_FILES/dashboards.yml"
echo "Copied monitoring files into the Helm chart."
