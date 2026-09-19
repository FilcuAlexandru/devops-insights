# DevOps Insights

**Collect. Analyze. Understand the DevOps ecosystem.**

[![CI](https://github.com/FilcuAlexandru/devops-insights/actions/workflows/ci.yml/badge.svg)](https://github.com/FilcuAlexandru/devops-insights/actions/workflows/ci.yml)
[![Security](https://github.com/FilcuAlexandru/devops-insights/actions/workflows/security.yml/badge.svg)](https://github.com/FilcuAlexandru/devops-insights/actions/workflows/security.yml)
[![Release](https://img.shields.io/github/v/release/FilcuAlexandru/devops-insights?sort=semver)](https://github.com/FilcuAlexandru/devops-insights/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

![Python](https://img.shields.io/badge/Python_3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Nginx](https://img.shields.io/badge/nginx-009639?logo=nginx&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-0F1689?logo=helm&logoColor=white)
![Argo CD](https://img.shields.io/badge/Argo_CD-EF7B4D?logo=argo&logoColor=white)
![OpenShift](https://img.shields.io/badge/OpenShift-EE0000?logo=redhatopenshift&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?logo=ollama&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

I wanted a way to see what is going on across the tools I work with every day: Kubernetes,
Docker, Terraform, Ansible, Prometheus, Argo CD and friends. Which projects are growing? Which
ones are quiet? What changed since last week? DevOps Insights answers that by collecting public
data from GitHub on a schedule, keeping the history in PostgreSQL, and showing it in a small
web dashboard.

It also has an AI corner, and I was careful about what that means. Every number you see is
calculated by plain Python and SQL. A small language model running **locally** through Ollama
only gets those finished numbers and is asked to explain them in words: a summary, the trends,
possible risks and recommendations. It never touches the database and it never does the maths.
No paid API, and no data leaves your machine.

It is a personal lab project. It is also meant to be run for real: everything is containerised,
has health checks and metrics, and the same code runs on Docker Compose, on Kubernetes with
Argo CD, and on OpenShift.

## What you get

- **A dashboard** with totals, stars per technology, main languages, the most popular
  repositories, the fastest growing ones and the latest AI summaries.
- **Fifteen technologies and nineteen repositories** tracked out of the box (Linux, Python,
  Docker, Kubernetes, Helm, OpenShift, Argo CD, Terraform, Ansible, PostgreSQL, Prometheus,
  Grafana, Git, GitHub Actions and Ollama). Adding another is a one-line change.
- **History.** Every collection appends a snapshot of stars, forks and open issues instead of
  overwriting them, so trends are real and not guessed.
- **A collector** that runs every six hours and can also be started from the UI with
  *Collect now*. When something goes wrong (a repository was renamed, GitHub's rate limit is
  used up) you see exactly what and why, instead of a silent gap.
- **AI analysis** per repository, stored so you can compare it with earlier ones.
- **Monitoring** with Prometheus and a ready-made Grafana dashboard.
- **Deployment** with Docker Compose, a Helm chart for Kubernetes and OpenShift, and Argo CD
  manifests.

## Try it

You need Docker Desktop (give it about 8 GB of memory), Git and `make`.

```bash
git clone git@github.com:FilcuAlexandru/devops-insights.git
cd devops-insights
make up
```

Open **http://localhost:8080**. About a minute later the first collection has finished and the
dashboard is full. The AI model (roughly 1.4 GB) downloads in the background; until it is there,
the AI button politely says so instead of failing.

Everything that has a login uses **admin / admin**. Yes, on purpose: this is a lab, and having
one credential everywhere makes it easy to explore. Please don't put it on the internet as it is
(see [SECURITY.md](SECURITY.md)).

For a guided tour that checks every component, including Kubernetes, Argo CD and OpenShift, read
[docs/local-testing.md](docs/local-testing.md).

## Where everything lives

Every component has its own port, so nothing collides.

| Component | What it is | Docker Compose | Kubernetes (kind) | Login |
|---|---|---|---|---|
| Web application | The UI (nginx serving a static app) | http://localhost:8080 | http://localhost:30080 | none |
| Backend API | FastAPI, Swagger UI at `/api/docs` | http://localhost:8000/api/docs | http://localhost:30800/api/docs | none |
| Grafana | Dashboards for the app's own metrics | http://localhost:3000 | http://localhost:30300 | admin / admin |
| Prometheus | Metrics storage | http://localhost:9090 | http://localhost:30900 | admin / admin |
| Argo CD | GitOps delivery | not used | https://localhost:30443 | admin / admin |
| PostgreSQL | Database `devops_insights` | `localhost:5432` | `localhost:30432` | admin / admin |
| Ollama | Local model runtime | http://localhost:11434 | http://localhost:31434 | none |
| Collector | Worker metrics for Prometheus | http://localhost:9102/metrics | inside the cluster | none |

On OpenShift the addresses are Routes, and `make urls-openshift` prints them. The **Platform**
page inside the app shows this same table for whichever environment it is running in, so you
never have to look anything up.

## How it works

```
   GitHub API ──► collector ──► PostgreSQL ◄── backend (FastAPI) ◄── frontend (nginx + SPA)
                     │                              │
                     └───────── metrics ────────────┼──► Prometheus ──► Grafana
                                                    │
                                                    └──► Ollama (local model, optional)
```

The **collector** reads a small catalogue of technologies and their GitHub repositories, fetches
each one, cleans the data up and stores it. The repository row always holds the latest values,
and every run also adds a snapshot, which is what makes trends possible. Each run is written to
a table of its own, with the reason for every failure.

The **backend** is a plain JSON API. It calculates totals, rankings and growth with SQL and
Python. For an AI analysis it builds a strict prompt from those numbers, sends it to Ollama and
checks that the answer really has the four sections it asked for. Small models sometimes ignore
instructions, so a bad answer is retried once and never stored.

The **frontend** is a static single-page app: HTML, CSS and JavaScript modules, no build step, no
CDN. nginx serves it and forwards `/api` to the backend, so the browser only ever talks to one
address. Everything that comes from GitHub is escaped before it reaches the page.

The longer story, including why things are the way they are, is in
[docs/architecture.md](docs/architecture.md).

## Technologies and why they are here

| Area | Technology | Why |
|---|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, httpx | Typed, small, and easy to test |
| Frontend | Plain JavaScript modules, Chart.js, nginx | Nothing to compile, nothing to break offline |
| Database | PostgreSQL 16 | History, JSON columns and solid migrations |
| AI | Ollama with `qwen3:1.7b` | Runs on a laptop CPU, no account needed. The model is configurable |
| Metrics | Prometheus, Grafana | The standard pairing, provisioned automatically |
| Containers | Docker, Docker Compose | One command to run everything locally |
| Orchestration | Kubernetes (kind), Helm | Real manifests, tested on a local cluster |
| GitOps | Argo CD | Deployments described in Git |
| Enterprise Kubernetes | OpenShift | Routes, and containers that run with any user ID |
| Quality | pytest, Ruff, Node's test runner, GitHub Actions, CodeQL, Trivy | Every change is tested and scanned |

## Repository layout

```
devops-insights/
├── backend/        Python: API, collector, database, AI (own Dockerfile and tests)
├── frontend/       The web app, its nginx setup and its tests (own Dockerfile)
├── deploy/
│   ├── helm/           One chart for Kubernetes and OpenShift
│   ├── kubernetes/     kind cluster with every port mapped, plus lab manifests
│   ├── argocd/         Argo CD applications
│   └── openshift/      In-cluster image builds and notes
├── monitoring/     Prometheus and Grafana configuration
├── docs/           The guides
├── scripts/        Small operational scripts
├── docker-compose.yml
└── Makefile        `make help` lists everything you can do
```

Backend and frontend are separate on purpose. The only thing they share is the JSON API, so
either one can change without touching the other.

## Beyond your laptop

- **Kubernetes:** `make kind-up`, `make kind-load`, `make k8s-deploy`, and optionally
  `make argocd-install`. See [docs/kubernetes.md](docs/kubernetes.md).
- **OpenShift:** the same chart with `values-openshift.yaml`. The images were checked to run
  with the random user IDs OpenShift assigns; a real OpenShift cluster is the one thing I
  haven't run it on yet. `make openshift-deploy` deploys and verifies it in one command, and
  [docs/openshift.md](docs/openshift.md) says exactly what was and wasn't verified.
- **Releases:** tagged versions publish multi-architecture images and the Helm chart to GitHub's
  registry. See [docs/releasing.md](docs/releasing.md).

## Good to know

- GitHub allows 60 anonymous API requests per hour and one collection uses 19. That is plenty
  for the six-hour schedule but not for pressing *Collect now* all afternoon. A token with no
  scopes lifts the limit: set `GITHUB_TOKEN`.
- A 1.7-billion-parameter model is small. Its analyses are useful as a readable summary, but they
  can be shallow or slightly off. That is exactly why the numbers are not the model's job.
- GitHub's *open issues* count includes pull requests. The app shows the number as GitHub
  reports it.
- GitHub is the only data source so far.

## What I want to add next

GitHub releases (so you can see release cadence), CVE data from the NVD, and RSS/Atom feeds from
project blogs. None of these exist yet.

## Documentation

| Guide | What is in it |
|---|---|
| [Local testing](docs/local-testing.md) | Run everything and check that it works |
| [URLs and credentials](docs/urls-and-credentials.md) | Every address, port and login, and the API |
| [Architecture](docs/architecture.md) | Data flow, data model, design decisions |
| [Kubernetes](docs/kubernetes.md) | kind, Helm and Argo CD |
| [OpenShift](docs/openshift.md) | Deploying on OpenShift |
| [Observability](docs/observability.md) | Metrics, Prometheus, Grafana |
| [Development](docs/development.md) | Working on the code |
| [Releasing](docs/releasing.md) | Repository setup and cutting a release |

## Contributing

Issues and pull requests are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) explains the workflow
and the commit style, and [CHANGELOG.md](CHANGELOG.md) lists what changed in each version.

## License

MIT, see [LICENSE](LICENSE).

## Author

Alexandru Filcu, DevOps / infrastructure engineer, working mostly with Linux, automation,
Python, Kubernetes and GitOps.
