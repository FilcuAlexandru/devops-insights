# Running and testing locally

This guide takes you from a fresh checkout to a verified, working system. Pick the path you need;
they are independent, and **Path A is the one to start with**.

| Path | Use it to | Time |
|---|---|---|
| [A. Docker Compose](#a-docker-compose-recommended) | Run the whole stack (everything except Argo CD) | ~5 min |
| [B. Development mode](#b-development-mode-without-docker-for-the-code) | Edit and debug backend or frontend with auto-reload | ~5 min |
| [C. Kubernetes + Argo CD](#c-kubernetes-kind-and-argo-cd) | Test the Helm chart and GitOps delivery | ~15 min |
| [D. OpenShift](openshift.md) | Deploy on OpenShift | see guide |

## Prerequisites

| Tool | Needed for | Check |
|---|---|---|
| Docker Desktop, **8 GB memory** allocated to it | everything | `docker info` |
| Git and `make` | everything | `make --version` |
| Python 3.12+ | path B only | `python3 --version` |
| `kind`, `kubectl`, `helm` | path C only | `kind version`, `kubectl version --client`, `helm version` |
| `oc` | path D only | `oc version --client` |

Free host ports used by Compose: `3000 5432 8000 8080 9090 9102 11434`.
Kubernetes (kind) uses `30080 30300 30432 30443 30800 30900 31434`.
Check with `lsof -nP -iTCP:8080 -sTCP:LISTEN`.

---

## A. Docker Compose (recommended)

### 1. Start

```bash
make up
```

This runs `docker compose up -d --build`, then prints every URL and login. What starts, in order:

1. `postgres`, `ollama`, `prometheus` start.
2. `migrate` waits for PostgreSQL and applies the migrations, then exits (status `Exited (0)`).
3. `backend` and `collector` start. The collector immediately collects all repositories from GitHub.
4. `frontend` and `grafana` start.
5. `ollama-init` downloads the AI model in the background, then exits (`Exited (0)`). Nothing waits
   for it; AI features just report "model missing" until it finishes.

### 2. Check that everything is healthy

```bash
make ps
```

Expected: `backend`, `frontend`, `grafana`, `ollama`, `postgres`, `prometheus` show `(healthy)`;
`collector` is `Up`; `migrate` and `ollama-init` are `Exited (0)`.

### 3. Verify each component

Work through this list. Every login is **admin / admin**.

| # | Open | You should see |
|---|---|---|
| 1 | http://localhost:8080 | The dashboard. After about a minute: 15 technologies, 19 repositories, totals, two charts, a green "succeeded" collection banner |
| 2 | http://localhost:8080/#/repositories | 19 repositories; try the search box and the sort menu |
| 3 | Click any repository | Metrics, details, snapshots. Trend charts need two snapshots, see step 5 |
| 4 | http://localhost:8080/#/platform | Every component with its address and login; Backend API "database ok"; Ollama "qwen3:1.7b ready" once the model is downloaded |
| 5 | Dashboard, **Collect now** | A toast "Collection started", the button shows "Collecting…", then the page refreshes and *Snapshots* doubles (19 → 38) |
| 6 | http://localhost:8000/api/docs | Swagger UI for the API |
| 7 | http://localhost:3000 (admin / admin) | Grafana. Grafana may offer to change the password: choose **Skip**. Open *Dashboards → DevOps Insights → DevOps Insights* |
| 8 | http://localhost:9090 (admin / admin) | Prometheus. *Status → Targets*: `backend`, `collector` and `prometheus` are **UP** |
| 9 | `docker exec -it devops-insights-postgres psql -U admin -d devops_insights -c "select count(*) from repositories"` | `19` |

Prefer to let a script do the checking? `make smoke-test` runs 21 automated checks against the stack
(web app, API, database, Grafana and Prometheus logins, scrape targets, last collection) and exits
with a non-zero status when something is wrong. It does not replace looking at the UI, but it
catches a broken component in seconds.

GitHub allows 60 unauthenticated requests per hour and one collection uses 19, so **Collect now**
works about three times an hour. Set `GITHUB_TOKEN` (see below) to lift the limit.

### 4. Try the AI analysis

1. Wait for the model: `docker compose logs -f ollama-init` (about 1.4 GB, one time).
2. Confirm: `curl http://localhost:8080/api/ai/health` returns `"ready": true`.
3. Open any repository and press **Generate analysis**. On a laptop CPU this takes 20 to 90 seconds.
4. The result has four sections (Summary, Trends, Risks, Recommendations) and is stored; earlier
   analyses stay available under "earlier analyses". The dashboard shows the latest summaries.

### 5. See the trends

Trends need at least two snapshots per repository. Press **Collect now** again (or wait for the
collector's next scheduled run), then open a repository: three charts (stars, forks, open issues)
appear, and the dashboard's *Fastest growing* list fills once stars changed between snapshots.

### Useful commands

```bash
make logs                    # follow all logs
docker compose logs -f collector
make down                    # stop, keep data
make reset                   # stop and DELETE all data, including the AI model
```

Optional settings live in `.env` (copy `.env.example`): `GITHUB_TOKEN`, `OLLAMA_MODEL`,
`COLLECTION_INTERVAL_SECONDS`, `COLLECTION_ON_STARTUP`.

### Coming from an earlier version of this project?

Earlier versions used the same Docker Compose project name, so Docker may already have volumes
named `devops-insights_postgres_data` and `devops-insights_grafana_data`, created with a different
database user and Grafana password. This version deliberately uses **new volume names**
(`devops-insights_database`, `_grafana`, `_prometheus`) so the old data cannot get in the way. Only
the Ollama model volume is shared, so the model is not downloaded twice. Remove the old volumes
when you no longer need them: `docker volume rm devops-insights_postgres_data devops-insights_grafana_data devops-insights_prometheus_data`.

---

## B. Development mode (without Docker for the code)

Run PostgreSQL (and Ollama) in Docker, and the backend and frontend directly on your machine.
Stop the Compose `backend`, `frontend` and `collector` first if they are running
(`docker compose stop backend frontend collector`), otherwise ports 8000 and 8080 are taken.

```bash
make setup        # create backend/.venv and install the backend with dev tools (once)
make db-up        # PostgreSQL on :5432 and Ollama on :11434
make migrate      # apply migrations

make run-backend  # terminal 1: API with auto-reload on http://localhost:8000
make run-frontend # terminal 2: frontend on http://localhost:8080, proxies /api to the backend
make collect      # terminal 3: collect all repositories once
```

Edit files under `backend/src` (auto-reload) or `frontend/public` (refresh the browser).

### Tests and quality

```bash
make test-backend   # needs PostgreSQL: make db-up
make test-frontend  # runs in Docker, no Node.js needed locally
make lint           # Ruff: lint + format check
make check          # everything CI runs (lint, tests, Helm, monitoring sync)
```

The backend tests create and use a separate database named `devops_insights_test` on the same
PostgreSQL server, so your real data is never touched. Each test runs in a transaction that is
rolled back.

---

## C. Kubernetes (kind) and Argo CD

Full details are in [kubernetes.md](kubernetes.md). Short version, on a **new** cluster:

```bash
make kind-up          # kind cluster with every component's port mapped to localhost
make kind-load       # build the images and load them into the cluster
make k8s-deploy      # helm install (waits until ready)
make argocd-install  # optional: Argo CD with login admin / admin
make urls-kind       # print every address
make smoke-test-kind # automated end-to-end check
```

Then open http://localhost:30080 (application), http://localhost:30300 (Grafana),
http://localhost:30900 (Prometheus), https://localhost:30443 (Argo CD, self-signed certificate),
all with admin / admin where a login exists.

You already have a kind cluster named `devops-insights`? Port mappings can only be set when a
cluster is created, so either create a second one next to it
(`make kind-up KIND_CLUSTER=devops-insights-lab`, and add the same variable to the other `kind-`
targets) or reuse yours with `make k8s-forward`. See [kubernetes.md](kubernetes.md) for both, and
for removing the release of the previous project version first.

---

## D. OpenShift

See [openshift.md](openshift.md).

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `port is already allocated` | Another program uses the port. Find it with `lsof -nP -iTCP:<port> -sTCP:LISTEN` and stop it |
| Dashboard says "No data collected yet" | The first collection is still running (about a minute) or failed. Look at the banner and at `docker compose logs collector` |
| Collection banner shows "rate limit exceeded" | GitHub's 60 requests per hour are used up. Wait for the reset time in the message, or set `GITHUB_TOKEN` in `.env` and run `docker compose up -d` |
| "Ollama unreachable" or "model missing" on a repository | The model is still downloading: `docker compose logs -f ollama-init`. Or Docker has too little memory: give it 8 GB |
| Analysis fails with "The model returned an invalid analysis" | Small models sometimes ignore the format. The backend already retries once; press the button again |
| Grafana asks to change the password | Choose **Skip**; the password stays `admin` |
| Grafana shows "No data" | Prometheus needs about a minute of scraping after start. Check *Status → Targets* in Prometheus |
| `password authentication failed for user "admin"` | The PostgreSQL volume was created by an older version. Remove it: `make reset` (this deletes all data) |
| Backend cannot connect to PostgreSQL in development mode | Run `make db-up`, and check that `DATABASE_URL` (default `postgresql+psycopg://admin:admin@localhost:5432/devops_insights`) matches |
