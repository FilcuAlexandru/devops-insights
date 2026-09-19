# URLs, ports and credentials

Every component that has a login uses **username `admin`, password `admin`**. This is intentional:
DevOps Insights is a personal lab project and nothing here is secret. Do not reuse this setup
for anything exposed to the internet.

Every component listens on its own port. The **Platform** page of the web application shows the
table for the environment it is running in, and `make urls-compose`, `make urls-kind` and
`make urls-openshift` print it in the terminal.

## Docker Compose

| Component | Address | Login | Container |
|---|---|---|---|
| Web application | http://localhost:8080 | none | `devops-insights-frontend` |
| Backend API (Swagger UI) | http://localhost:8000/api/docs | none | `devops-insights-backend` |
| Grafana | http://localhost:3000 | admin / admin | `devops-insights-grafana` |
| Prometheus | http://localhost:9090 | admin / admin (basic auth) | `devops-insights-prometheus` |
| PostgreSQL | `localhost:5432`, database `devops_insights` | admin / admin | `devops-insights-postgres` |
| Ollama | http://localhost:11434 | none | `devops-insights-ollama` |
| Collector metrics | http://localhost:9102/metrics | none | `devops-insights-collector` |

Connect to the database from your machine:

```bash
docker exec -it devops-insights-postgres psql -U admin -d devops_insights
# or, with a local psql client:
psql postgresql://admin:admin@localhost:5432/devops_insights
```

## Kubernetes (kind)

Published by NodePort services and the port mappings in `deploy/kubernetes/kind/cluster.yaml`
(or by `make k8s-forward` on a cluster without mappings).

| Component | Address | Login |
|---|---|---|
| Web application | http://localhost:30080 | none |
| Backend API (Swagger UI) | http://localhost:30800/api/docs | none |
| Grafana | http://localhost:30300 | admin / admin |
| Prometheus | http://localhost:30900 | admin / admin (basic auth) |
| Argo CD | https://localhost:30443 (self-signed certificate) | admin / admin |
| PostgreSQL | `localhost:30432`, database `devops_insights` | admin / admin |
| Ollama | http://localhost:31434 | none |

## OpenShift

Routes are created by the Helm chart with the host `<component>-<project>.<apps domain>`.
For the project `devops-insights` on OpenShift Local (`apps-crc.testing`):

| Component | Address | Login |
|---|---|---|
| Web application | https://frontend-devops-insights.apps-crc.testing | none |
| Backend API | https://backend-devops-insights.apps-crc.testing/api/docs | none |
| Grafana | https://grafana-devops-insights.apps-crc.testing | admin / admin |
| Prometheus | https://prometheus-devops-insights.apps-crc.testing | admin / admin |
| Argo CD | `oc get route openshift-gitops-server -n openshift-gitops` | see [openshift.md](openshift.md) |

`make urls-openshift` prints the real hosts of the current project.

## Application API

Base URL: the backend address above; through the web application the same paths are available
under `/api`. Interactive documentation: `/api/docs`, machine-readable schema: `/api/openapi.json`.

| Method and path | Purpose |
|---|---|
| `GET /health` | Liveness (used by probes) |
| `GET /health/ready` | Readiness: checks the database |
| `GET /metrics` | Prometheus metrics |
| `GET /api/status` | Version, database state, Ollama state, last collection |
| `GET /api/dashboard?technology=<slug>` | All dashboard figures, optionally for one technology |
| `GET /api/technologies` | Technologies with repository count and total stars |
| `GET /api/technologies/{slug}` | One technology with its repositories |
| `GET /api/repositories?technology=&search=&sort=&order=` | Repositories; `sort` is `stars`, `forks`, `issues`, `activity` or `name` |
| `GET /api/repositories/{id}` | One repository |
| `GET /api/repositories/{id}/snapshots` | Statistics history, oldest first |
| `GET /api/repositories/{id}/trend` | Deterministic change between first and last snapshot |
| `GET /api/collection/runs?limit=` | Recent collection runs, newest first |
| `POST /api/collection/run` | Start a collection in the background (`202`, or `409` if one is running) |
| `GET /api/ai/health` | Is Ollama reachable and the model installed? |
| `POST /api/ai/repositories/{id}/analyze` | Generate and store an AI analysis (can take a minute or two) |
| `GET /api/ai/repositories/{id}/analyses` | Stored analyses, newest first |
