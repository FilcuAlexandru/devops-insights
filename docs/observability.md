# Observability

Prometheus scrapes the backend and the collector, Grafana shows a provisioned dashboard.

| | Docker Compose | Kubernetes (kind) | Login |
|---|---|---|---|
| Prometheus | http://localhost:9090 | http://localhost:30900 | admin / admin |
| Grafana | http://localhost:3000 | http://localhost:30300 | admin / admin |
| Backend metrics | http://localhost:8000/metrics | in-cluster | none |
| Collector metrics | http://localhost:9102/metrics | in-cluster | none |

Prometheus is protected with basic authentication (`web.config.file`). Grafana reaches it with the
same credentials, configured in the provisioned datasource. Nothing has to be set up by hand.

## Scrape targets

| Job | Target | Source |
|---|---|---|
| `backend` | `backend:8000/metrics` | HTTP and application metrics of the API |
| `collector` | `collector:9102/metrics` | Collection metrics of the worker |
| `prometheus` | `localhost:9090/metrics` | Prometheus itself |

On Kubernetes the targets are discovered through the Services, so every replica is scraped
individually; the `job` label is the component name in both environments, which is what the
dashboard queries.

## Metrics

HTTP metrics come from `prometheus-fastapi-instrumentator` (`http_requests_total`,
`http_request_duration_seconds`, `http_request_duration_highr_seconds`, ...). Health and metrics
endpoints are excluded from them. Application metrics:

| Metric | Type | Meaning |
|---|---|---|
| `devops_insights_application_info` | gauge | Name, environment and version |
| `devops_insights_repositories_collected_total` | counter | Repositories collected successfully |
| `devops_insights_collection_errors_total` | counter | Repositories that failed to collect |
| `devops_insights_collection_runs_total{status}` | counter | Finished runs by status |
| `devops_insights_collection_duration_seconds` | histogram | Duration of a full run |
| `devops_insights_collection_last_success_timestamp_seconds` | gauge | When a run last finished without failures |
| `devops_insights_ai_analyses_total` | counter | Analyses generated |
| `devops_insights_ai_analysis_errors_total` | counter | Failed analyses |
| `devops_insights_ai_analysis_duration_seconds` | histogram | Time to generate an analysis |
| `devops_insights_database_query_duration_seconds` | histogram | Duration of each SQL statement |

Counters live in the process that increments them, so collection metrics appear on the
`collector` job for scheduled runs and on the `backend` job for runs started with "Collect now".
The dashboard sums both.

## The Grafana dashboard

*Dashboards → DevOps Insights → DevOps Insights* contains: service status, collection health
(runs, duration, errors, time since the last good run), HTTP traffic (requests by status and
endpoint, latency p50/p95/p99, 5xx), AI analyses (count, failures, duration), and database and
process metrics (statement duration, memory, CPU). Every panel query was checked against a running
Prometheus.

## Where the files are

| File | Purpose |
|---|---|
| `monitoring/prometheus/prometheus.yml` | Scrape configuration (Docker Compose) |
| `monitoring/prometheus/web.yml` | Basic auth users (bcrypt hash of `admin`) |
| `monitoring/grafana/provisioning/` | Datasource and dashboard provider |
| `monitoring/grafana/dashboards/devops-insights.json` | The dashboard |
| `deploy/helm/devops-insights/templates/prometheus/` | Prometheus on Kubernetes and OpenShift |
| `deploy/helm/devops-insights/templates/grafana/` | Grafana on Kubernetes and OpenShift |

The Helm chart needs its own copy of the dashboard (a chart can only read files inside itself).
After editing the dashboard run `make sync-monitoring`; CI fails if the copies differ.

## Changing the password

The bcrypt hash of `admin` is in `monitoring/prometheus/web.yml` and in
`deploy/helm/devops-insights/values.yaml` (`prometheus.auth`). To use another password:

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'NEW_PASSWORD', bcrypt.gensalt()).decode())"
```

Put the hash in both places, and update the datasource password (`basicAuthPassword`) and the
Prometheus scrape job for itself.
