# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-09-19

### Added
- Scheduled collector worker with a run history (`collection_runs`), a "Collect now" action and
  clear reporting of GitHub rate limits and per-repository failures.
- Catalog of 15 technologies and 19 GitHub repositories with descriptions and websites.
- Repository metadata: license, archived flag, last push and last collection time.
- Single-page frontend (dashboard, technologies, repositories, repository detail, platform),
  served by nginx, with vendored Chart.js and HTML-escaped rendering of external data.
- Prometheus and Grafana provisioning with a new dashboard and basic-auth protected Prometheus.
- Helm chart for Kubernetes and OpenShift (Routes, arbitrary user IDs), Argo CD applications,
  kind cluster definition with per-component ports, and OpenShift image builds.
- `scripts/smoke-test.sh` (21 end-to-end checks) and `scripts/openshift-deploy.sh` (build in the
  cluster, install the chart and verify), with a step-by-step guide for OpenShift Local.
- Documentation, `Makefile`, operational scripts and a CI/CD and release pipeline.

### Changed
- Repository split into `backend/`, `frontend/`, `deploy/`, `monitoring/` and `docs/`.
- `created_at` and `updated_at` of repositories now hold the GitHub dates instead of the local
  write time.
- Every component with a login uses `admin` / `admin`.
- The Helm chart no longer depends on the Bitnami PostgreSQL chart.

### Fixed
- AI analysis: reasoning blocks emitted by qwen3 are removed, request timeouts are handled and
  invalid responses are retried once.
- Snapshots are deleted together with their repository.

[Unreleased]: https://github.com/FilcuAlexandru/devops-insights/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/FilcuAlexandru/devops-insights/releases/tag/v0.2.0
