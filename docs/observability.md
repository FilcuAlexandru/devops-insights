# Observability

Prometheus collects metrics from the backend and the collector, and Grafana shows them on a
dashboard that is already set up. You don't need to configure anything by hand: start the stack
and both are ready.

| | Docker Compose | Kubernetes (kind) | Login |
|---|---|---|---|
| Prometheus | http://localhost:9090 | http://localhost:30900 | admin / admin |
| Grafana | http://localhost:3000 | http://localhost:30300 | admin / admin |
| Backend metrics | http://localhost:8000/metrics | inside the cluster | none |
| Collector metrics | http://localhost:9102/metrics | inside the cluster | none |

Prometheus asks for a login (basic authentication, through `web.config.file`), so that "admin /
admin everywhere" is true for it as well. Grafana reaches it with the same credentials, which are
part of the provisioned datasource. Even Prometheus scraping itself needs them.

## What Prometheus scrapes

| Job | Target | What it provides |
|---|---|---|
| `backend` | `backend:8000/metrics` | HTTP and application metrics of the API |
| `collector` | `collector:9102/metrics` | The collection metrics of the worker |
| `prometheus` | `localhost:9090/metrics` | Prometheus itself |

On Kubernetes the targets are found through the Services, so every replica is scraped on its own.
In both environments the `job` label is the name of the component, which is what the dashboard
queries rely on.

## The metrics

The HTTP metrics come from `prometheus-fastapi-instrumentator` (`http_requests_total`,
`http_request_duration_seconds` and friends). The health and metrics endpoints are left out of them
on purpose. The application's own metrics are:

| Metric | Type | What it tells you |
|---|---|---|
| `devops_insights_application_info` | gauge | The name, environment and version |
| `devops_insights_repositories_collected_total` | counter | Repositories collected successfully |
| `devops_insights_collection_errors_total` | counter | Repositories that failed to collect |
| `devops_insights_collection_runs_total{status}` | counter | Finished runs, by status |
| `devops_insights_collection_duration_seconds` | histogram | How long a full run takes |
| `devops_insights_collection_last_success_timestamp_seconds` | gauge | When a run last finished without any failure |
| `devops_insights_ai_analyses_total` | counter | Analyses generated |
| `devops_insights_ai_analysis_errors_total` | counter | Analyses that failed |
| `devops_insights_ai_analysis_duration_seconds` | histogram | How long an analysis takes |
| `devops_insights_database_query_duration_seconds` | histogram | The duration of every SQL statement |

A counter lives in the process that increments it. Scheduled collections therefore show up under
the `collector` job, and the ones started with **Collect now** under the `backend` job. The
dashboard adds the two together.

## The Grafana dashboard

You find it under *Dashboards → DevOps Insights → DevOps Insights*. It shows the state of the
services, the health of the collection (runs, duration, errors and how long ago the last good run
was), the HTTP traffic (requests by status and by endpoint, latency at p50, p95 and p99, and 5xx
errors), the AI analyses (how many, how many failed, how long they take), and the database and
process metrics (statement duration, memory and CPU). I checked every panel's query against a
running Prometheus with real data.

## Where the files live

| File | What it does |
|---|---|
| `monitoring/prometheus/prometheus.yml` | What to scrape (Docker Compose) |
| `monitoring/prometheus/web.yml` | The login, as a bcrypt hash of `admin` |
| `monitoring/grafana/provisioning/` | The datasource and the dashboard provider |
| `monitoring/grafana/dashboards/devops-insights.json` | The dashboard itself |
| `deploy/helm/devops-insights/templates/prometheus/` | Prometheus on Kubernetes and OpenShift |
| `deploy/helm/devops-insights/templates/grafana/` | Grafana on Kubernetes and OpenShift |

A Helm chart can only read files inside its own folder, so the chart carries a copy of the
dashboard. After you edit it, run `make sync-monitoring`. The CI fails when the two copies differ, so
they can't drift apart without you noticing.

## Changing the password

The bcrypt hash of `admin` is in `monitoring/prometheus/web.yml` and in
`deploy/helm/devops-insights/values.yaml` (under `prometheus.auth`). To use a different password,
generate a new hash:

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'NEW_PASSWORD', bcrypt.gensalt()).decode())"
```

Put the hash in both places. Then update the datasource password (`basicAuthPassword`) and the job
in which Prometheus scrapes itself.
