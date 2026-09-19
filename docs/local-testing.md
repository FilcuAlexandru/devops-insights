# Running and testing it on your machine

This is the guide I would want if I were opening the project for the first time: how to start
everything, what you should see, and how to tell that it really works. Pick the path that fits
what you want to do. They are independent, and **the first one is where to begin.**

| Path | When to use it | How long |
|---|---|---|
| [A. Docker Compose](#a-docker-compose-start-here) | Run the whole platform (everything except Argo CD) | about 5 minutes |
| [B. Development mode](#b-development-mode) | Change the backend or frontend with auto-reload | about 5 minutes |
| [C. Kubernetes and Argo CD](#c-kubernetes-and-argo-cd) | Test the Helm chart and GitOps delivery | about 15 minutes |
| [D. OpenShift](openshift.md) | Deploy on OpenShift | see that guide |

## What you need

| Tool | For | How to check |
|---|---|---|
| Docker Desktop with **8 GB of memory** | everything | `docker info` |
| Git and `make` | everything | `make --version` |
| Python 3.12 or newer | path B only | `python3 --version` |
| `kind`, `kubectl`, `helm` | path C only | `kind version`, `kubectl version --client`, `helm version` |
| `oc` | path D only | `oc version --client` |

The Compose stack uses these ports on your machine: 3000, 5432, 8000, 8080, 9090, 9102 and 11434.
The Kubernetes setup uses 30080, 30300, 30432, 30443, 30800, 30900 and 31434. If something is
already listening on one of them, `lsof -nP -iTCP:8080 -sTCP:LISTEN` shows what.

---

## A. Docker Compose (start here)

### 1. Start it

```bash
make up
```

That builds the images, starts everything and prints every address when it is done. Behind the
scenes it goes like this:

1. PostgreSQL, Ollama and Prometheus start.
2. A one-off `migrate` container waits for PostgreSQL, applies the database migrations and exits.
3. The backend and the collector start. The collector immediately fetches all repositories from
   GitHub.
4. The frontend and Grafana start.
5. In the background, `ollama-init` downloads the AI model and then exits. Nothing waits for it:
   until it has finished, the AI button simply says the model isn't there yet.

### 2. See that the containers are healthy

```bash
make ps
```

`backend`, `frontend`, `grafana`, `ollama`, `postgres` and `prometheus` should say `healthy`.
`collector` is `Up`, and `migrate` and `ollama-init` show `Exited (0)`, which is what they should
do.

### 3. Look at every component

Work through this list once. Everything that has a login uses **admin / admin**.

| # | Open | What you should see |
|---|---|---|
| 1 | http://localhost:8080 | The dashboard. After about a minute: 15 technologies, 19 repositories, totals, two charts and a green "succeeded" banner |
| 2 | http://localhost:8080/#/repositories | The 19 repositories. Try the search box and the sort menu |
| 3 | Click any repository | Its metrics, details and snapshots. The trend charts need two snapshots, see step 5 |
| 4 | http://localhost:8080/#/platform | Every component with its address and login. "database ok" next to the API, and "qwen3:1.7b ready" once the model has downloaded |
| 5 | The dashboard, then **Collect now** | A "Collection started" message, the button says "Collecting…", and then the page refreshes and *Snapshots* doubles (19 becomes 38) |
| 6 | http://localhost:8000/api/docs | The Swagger UI of the API |
| 7 | http://localhost:3000 | Grafana. If it offers to change the password, choose **Skip**. Then *Dashboards → DevOps Insights → DevOps Insights* |
| 8 | http://localhost:9090 | Prometheus. Under *Status → Targets*, `backend`, `collector` and `prometheus` are all **UP** |

And the database itself:

```bash
docker exec -it devops-insights-postgres psql -U admin -d devops_insights -c "select count(*) from repositories"
```

The answer should be `19`.

If you would rather let a script do the checking, `make smoke-test` runs 21 automated checks on
the same things (the web app, the API, the database connection, the Grafana and Prometheus
logins, the scrape targets and the last collection) and exits with an error if something is off.
It doesn't replace looking at the interface, but it finds a broken component in seconds.

One thing to keep in mind: GitHub allows 60 anonymous requests an hour and a collection uses 19,
so **Collect now** works about three times an hour. A `GITHUB_TOKEN` (see below) lifts that limit.

### 4. Try the AI analysis

1. Wait for the model to download. It is about 1.4 GB and happens once. You can follow it with
   `docker compose logs -f ollama-init`.
2. Check that it is ready:

```bash
curl http://localhost:8080/api/ai/health
```

   You want to see `"ready":true`.

3. Open any repository and press **Generate analysis**. On a laptop CPU it takes somewhere
   between 20 and 90 seconds.
4. You get four sections: Summary, Trends, Risks and Recommendations. The analysis is saved, so
   older ones stay under "earlier analyses", and the dashboard shows the latest summaries.

### 5. See the trends

Trends need at least two snapshots of a repository. Press **Collect now** again, or wait for the
collector's next run, and open a repository: three charts (stars, forks and open issues) appear.
The *Fastest growing* list on the dashboard fills in as soon as some stars have changed between two
snapshots.

### Handy commands

```bash
make logs                       # follow the logs of everything
docker compose logs -f collector
make down                       # stop, keep the data
make reset                      # stop and DELETE the data, including the AI model
```

You can adjust a few things in a `.env` file (copy `.env.example`): `GITHUB_TOKEN`,
`OLLAMA_MODEL`, `COLLECTION_INTERVAL_SECONDS` and `COLLECTION_ON_STARTUP`.

### Upgrading from an earlier version of the project

Earlier versions used the same Docker Compose project name, so you may already have volumes
called `devops-insights_postgres_data` and `devops-insights_grafana_data`, created with a
different database user and Grafana password. This version deliberately uses new volume names
(`devops-insights_database`, `devops-insights_grafana` and `devops-insights_prometheus`), so the
old data can't get in the way. The only volume that is shared is the one holding the Ollama model,
so you don't have to download it twice. Once you no longer need the old ones:

```bash
docker volume rm devops-insights_postgres_data devops-insights_grafana_data devops-insights_prometheus_data
```

---

## B. Development mode

Here PostgreSQL (and Ollama) run in Docker, and the backend and frontend run straight on your
machine, so changes show up as soon as you save. If the Compose stack is running, stop the
application containers first, otherwise they hold ports 8000 and 8080:

```bash
docker compose stop backend frontend collector
```

Then:

```bash
make setup         # once: creates backend/.venv and installs everything
make db-up         # PostgreSQL on :5432 and Ollama on :11434
make migrate       # apply the migrations

make run-backend   # terminal 1: the API on http://localhost:8000, reloads on save
make run-frontend  # terminal 2: the UI on http://localhost:8080, forwards /api to the backend
make collect       # terminal 3: fetch all repositories once
```

Edit files in `backend/src` (the server reloads by itself) or in `frontend/public` (refresh the
browser).

### Tests and quality checks

```bash
make test-backend    # needs PostgreSQL: make db-up
make test-frontend   # runs in Docker, so you don't need Node.js
make lint            # Ruff: lint and formatting
make check           # everything the CI runs
```

The backend tests never touch your real data. They create their own database, called
`devops_insights_test`, on the same PostgreSQL server, and every test runs inside a transaction
that is rolled back afterwards.

---

## C. Kubernetes and Argo CD

[kubernetes.md](kubernetes.md) has the whole story. On a new cluster it comes down to this:

```bash
make kind-up           # a kind cluster with every port mapped to localhost
make kind-load         # build the images and load them into the cluster
make k8s-deploy        # helm install, waits until everything is ready
make argocd-install    # optional: Argo CD with the login admin / admin
make urls-kind         # print every address
make smoke-test-kind   # automated end-to-end check
```

Then open http://localhost:30080 (the application), http://localhost:30300 (Grafana),
http://localhost:30900 (Prometheus) and https://localhost:30443 (Argo CD, with a self-signed
certificate). Everything that has a login uses admin / admin.

If you already have a kind cluster called `devops-insights`, know that port mappings can only be
chosen when a cluster is created. You can either create a second one next to it
(`make kind-up KIND_CLUSTER=devops-insights-lab`) or reuse yours with `make k8s-forward`.
[kubernetes.md](kubernetes.md) explains both, including how to remove the release of the
previous version of the project first.

---

## D. OpenShift

Everything is in [openshift.md](openshift.md), including how to install OpenShift Local on
Windows, Linux and macOS.

---

## When something doesn't work

| What you see | Why, and what to do |
|---|---|
| `port is already allocated` | Something else uses the port. `lsof -nP -iTCP:<port> -sTCP:LISTEN` shows what; stop it |
| The dashboard says "No data collected yet" | The first collection is still running (about a minute) or failed. Look at the banner and at `docker compose logs collector` |
| The banner shows "rate limit exceeded" | You used up GitHub's 60 requests for this hour. Wait for the time in the message, or put a `GITHUB_TOKEN` in `.env` and run `docker compose up -d` |
| "Ollama unreachable" or "model missing" | The model is still downloading (`docker compose logs -f ollama-init`), or Docker doesn't have enough memory: give it 8 GB |
| "The model returned an invalid analysis" | Small models sometimes ignore the requested format. The backend already retries once; press the button again |
| Grafana asks you to change the password | Choose **Skip**. The password stays `admin` |
| Grafana shows "No data" | Prometheus needs about a minute of scraping after a start. Check *Status → Targets* in Prometheus |
| `password authentication failed for user "admin"` | The PostgreSQL volume comes from an older version. `make reset` removes it (and all the data) |
| The backend can't reach PostgreSQL in development mode | Run `make db-up`, and check that `DATABASE_URL` (default `postgresql+psycopg://admin:admin@localhost:5432/devops_insights`) is right |
