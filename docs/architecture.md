# Architecture

## Data flow

```
                    ┌────────────┐   fetch    ┌──────────────┐
                    │ GitHub API │◄───────────│  collector   │  python -m devops_insights.worker
                    └────────────┘            │  (worker)    │  scheduled, one replica
                                              └──────┬───────┘
                                                     │ normalize, store, snapshot
                                                     ▼
 browser ──► frontend ──/api──► backend ───────► PostgreSQL
            (nginx + SPA)      (FastAPI)  ▲
                                  │       └── deterministic analytics (Python + SQL)
                                  │
                                  └──► Ollama ── structured context ──► analysis text
                                        (optional)

 backend, collector ──/metrics──► Prometheus ──► Grafana
```

1. **Collect.** The collector reads the *catalog* (technologies and their GitHub repositories),
   fetches each repository, and runs it through an ETL pipeline: **extract**
   (`collectors/github.py`), **transform** (`pipelines/normalize.py`), **load**
   (`pipelines/store.py`). The repository row holds the latest values; every run also appends a
   `repository_snapshots` row, so history is never overwritten.
2. **Track runs.** Every run is recorded in `collection_runs` with its status
   (`succeeded`, `partial`, `failed`) and the reason for each failed repository. The UI shows the
   last run, so a failure is visible instead of silent.
3. **Analyze.** `analytics/` computes totals, rankings and trends with SQL and Python only.
4. **Explain.** For an AI analysis, the backend builds a structured context from PostgreSQL,
   wraps it in a strict prompt, and sends it to Ollama. The response must contain the four
   required sections or it is rejected (with one retry) and never stored.

## Repository layout

The code is organized by responsibility, and dependencies point in one direction:
`api` → `services` / `analytics` / `ai` → `models` / `schemas` → `core`.

| Package | Responsibility |
|---|---|
| `api/` | HTTP only: parses requests, calls a service, returns a schema. No business logic |
| `services/` | Use cases: catalog sync, collection runs, repository/technology queries |
| `analytics/` | Pure deterministic calculations (`trends.py` is free of database code) |
| `collectors/` | Talks to external sources; nothing else |
| `pipelines/` | Extract, transform, load for one source |
| `catalog/` | Data: which technologies and repositories are tracked |
| `ai/` | Prompt, Ollama client, response validation, persistence of analyses |
| `models/`, `schemas/` | SQLAlchemy models; Pydantic contracts |
| `observability/` | Metric definitions and recording helpers |
| `core/` | Settings, database engine and session, logging |

The frontend is a separate application in `frontend/`. Its only contract with the backend is the
JSON API under `/api`.

## Data model

| Table | Content |
|---|---|
| `technologies` | Tracked tools: name, slug, category, description, website |
| `repositories` | Latest state: description, language, license, archived flag, stars, forks, open issues, and the GitHub dates `created_at`, `updated_at`, `pushed_at`, plus `last_collected_at` |
| `repository_snapshots` | Stars, forks and open issues at one point in time, indexed by `(repository_id, collected_at)` |
| `collection_runs` | One row per collection: trigger, status, counts, errors |
| `ai_analyses` | Model, prompt, structured context, response and creation time of each analysis |

`created_at`, `updated_at` and `pushed_at` on `repositories` are the dates reported by GitHub.
Snapshots and analyses are deleted together with their repository.

GitHub's `open_issues` count includes pull requests; the platform stores the number as GitHub
reports it.

## Design decisions

- **Static frontend, no build step.** HTML, CSS and JavaScript modules served by nginx. There is
  nothing to compile, and Chart.js is vendored, so the UI works offline. All text from GitHub is
  HTML-escaped by a tagged template (`core/html.js`), and the analysis text goes through a
  Markdown renderer that escapes before formatting.
- **nginx proxies `/api`.** The browser only talks to one origin, so there is no CORS
  configuration, and the same image works behind Compose, a NodePort, an Ingress or an OpenShift
  Route. Runtime links (Grafana, Argo CD, ...) are injected at container start into `/config.js`.
- **A separate collector process.** Scheduled work does not run inside API replicas, so scaling
  the API never multiplies GitHub requests. The collector exposes its own metrics on port 9102.
  `POST /api/collection/run` lets a person start a run on demand.
- **Migrations are safe to run concurrently.** `python -m devops_insights.migrate` waits for
  PostgreSQL, then upgrades under a PostgreSQL advisory lock. Compose runs it as a one-shot
  service and Kubernetes runs it as an init container of the backend and the collector, so no
  Helm hook ordering is needed and Argo CD works without special handling.
- **Catalog as code.** The tracked technologies are a Python data structure with a test, not
  free-form configuration. Adding a repository is a one-line change.
- **AI is optional.** Nothing depends on Ollama. If it is missing, the rest of the platform works
  and the UI explains what is unavailable.
- **Every container runs as an arbitrary non-root user.** All images work with any user ID in
  group 0, which is what OpenShift requires and Kubernetes allows.

## Metrics

Both processes expose Prometheus metrics; see [observability.md](observability.md).
