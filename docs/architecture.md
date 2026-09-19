# Architecture

This page explains how DevOps Insights fits together and, more usefully, why it is built the way
it is. If you only want to run it, [local-testing.md](local-testing.md) is the better place to
start.

## The data flow

```
                    ┌────────────┐   fetch    ┌──────────────┐
                    │ GitHub API │◄───────────│  collector   │  python -m devops_insights.worker
                    └────────────┘            │  (worker)    │  scheduled, one replica
                                              └──────┬───────┘
                                                     │ normalise, store, snapshot
                                                     ▼
 browser ──► frontend ──/api──► backend ───────► PostgreSQL
            (nginx + SPA)      (FastAPI)  ▲
                                  │       └── deterministic analytics (Python + SQL)
                                  │
                                  └──► Ollama ── structured context ──► analysis text
                                        (optional)

 backend, collector ──/metrics──► Prometheus ──► Grafana
```

It all starts with the **collector**. It reads the catalogue, a list of technologies and the
GitHub repositories that represent them, and pushes each repository through a small ETL
pipeline: fetch it (`collectors/github.py`), tidy it up (`pipelines/normalize.py`) and store it
(`pipelines/store.py`). The repository row always holds the latest values. On top of that, every run
appends a row to `repository_snapshots`, and that is the whole reason trends exist: history is
never overwritten.

Every run is also written to its own table, `collection_runs`, with a status (`succeeded`,
`partial` or `failed`) and the reason each failed repository failed. The UI shows the last run,
so a problem is something you can see, not a silent gap in the charts.

The **backend** turns the stored data into numbers, and only Python and SQL are allowed to do
that (`analytics/`). When you ask for an AI analysis, it builds a structured context from
PostgreSQL, wraps it in a strict prompt and sends it to Ollama. The answer must contain the four
sections it asked for, in order, or it is rejected. That gets one retry, and a bad answer is never
stored.

## How the code is organised

Dependencies point in one direction: `api` calls `services`, `analytics` and `ai`, which use
`models` and `schemas`, which sit on top of `core`. Nothing lower knows about anything higher.

| Package | What it is responsible for |
|---|---|
| `api/` | HTTP and nothing else: read the request, call a service, return a schema |
| `services/` | The use cases: syncing the catalogue, running a collection, querying repositories |
| `analytics/` | Pure calculations. `trends.py` has no database code at all, so it is tested without one |
| `collectors/` | Talking to outside sources |
| `pipelines/` | Normalising and storing what a collector fetched |
| `catalog/` | Data only: which technologies and repositories are tracked |
| `ai/` | The prompt, the Ollama client, validating the answer and saving analyses |
| `models/`, `schemas/` | SQLAlchemy models, and the Pydantic contracts of the API |
| `observability/` | The Prometheus metrics |
| `core/` | Settings, the database session, logging |

The frontend is a separate application in `frontend/`. The only thing it shares with the backend
is the JSON API under `/api`.

## The data model

| Table | What it holds |
|---|---|
| `technologies` | The tools that are tracked: name, slug, category, description, website |
| `repositories` | The latest state: description, language, license, archived flag, stars, forks, open issues, the GitHub dates `created_at`, `updated_at` and `pushed_at`, and `last_collected_at` |
| `repository_snapshots` | Stars, forks and open issues at one moment, indexed by `(repository_id, collected_at)` |
| `collection_runs` | One row per collection: what triggered it, its status, counts and errors |
| `ai_analyses` | The model, the prompt, the structured context, the response and the time of each analysis |

`created_at`, `updated_at` and `pushed_at` in `repositories` are the dates GitHub reports, not the
moment a row was written. Snapshots and analyses are deleted together with their repository.

A small trap worth knowing: GitHub's `open_issues` count includes pull requests. The platform
stores the number exactly as GitHub reports it.

## Decisions, and the reasons behind them

**A static frontend with no build step.** The interface is plain HTML, CSS and JavaScript modules
served by nginx. There is nothing to compile, and Chart.js is included in the repository, so it
even works without internet access. Everything that comes from GitHub is escaped by a tagged
template (`core/html.js`) before it reaches the page, and the Markdown of an AI analysis is escaped
first and formatted second.

**nginx forwards `/api`.** The browser only ever talks to one address, so there is no CORS to
configure, and the same image works behind Compose, a NodePort, an Ingress or an OpenShift Route.
The links to Grafana, Argo CD and the rest are injected when the container starts, into `/config.js`.

**The collector is its own process.** Scheduled work doesn't run inside the API, so scaling the API
up can never multiply the requests sent to GitHub. It exposes its own metrics on port 9102, and
`POST /api/collection/run` lets a person start a run whenever they like.

**Migrations can run concurrently.** `python -m devops_insights.migrate` waits until PostgreSQL
accepts connections, then upgrades the database under a PostgreSQL advisory lock. Compose runs it
as a one-off service, and Kubernetes runs it as an init container of the backend and the collector.
No ordering of Helm hooks is involved, so Argo CD works without special handling.

**The catalogue is code.** The tracked technologies are a Python data structure with a test, not
free-form configuration. Adding a repository is a one-line change that CI validates.

**The AI is optional.** Nothing depends on Ollama. If it is missing, everything else works and the
interface tells you what is unavailable.

**Every container runs as an arbitrary non-root user.** All images work with any user ID in group
0. That is what OpenShift demands and Kubernetes allows.

## Metrics

Both the backend and the collector expose Prometheus metrics. They are described in
[observability.md](observability.md).
