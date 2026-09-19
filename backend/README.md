# Backend

This is the part that does the work: it collects data from GitHub, stores it, calculates the
numbers, serves the API and talks to the local AI model. It is a FastAPI application plus a small
worker process, both built from the same Python package (`devops_insights`).

## Three ways it runs

| Entry point | What it does |
|---|---|
| `devops_insights.api.app:create_app` | The HTTP API, started with uvicorn. Swagger UI is at `/api/docs` |
| `python -m devops_insights.worker` | The collector. Collects right away, then every `COLLECTION_INTERVAL_SECONDS` (six hours by default) and serves its own metrics on port 9102. `--once` collects a single time and exits |
| `python -m devops_insights.migrate` | Waits until PostgreSQL accepts connections, then applies the migrations. Safe to run from several places at once |

## Working on it

From the repository root:

```bash
make setup        # virtualenv in backend/.venv, installs the package and the dev tools
make db-up        # PostgreSQL and Ollama in Docker
make migrate
make run-backend  # http://localhost:8000/api/docs, reloads when you save a file
make collect      # fetch all repositories once
make test-backend
```

The tests need PostgreSQL but never touch your real data: they create a separate
`devops_insights_test` database and roll back every test.

## What is where

| Folder | What it holds |
|---|---|
| `api/` | HTTP only. Routers parse the request, call a service and return a schema |
| `services/` | The use cases: syncing the catalogue, running a collection, querying repositories |
| `analytics/` | Pure calculations (totals, rankings, growth). `trends.py` has no database code at all |
| `collectors/` | The GitHub client. It only fetches and validates |
| `pipelines/` | Normalise the fetched data and store it, one file per step |
| `catalog/` | Which technologies and repositories are tracked |
| `ai/` | The prompt, the Ollama client, response validation and saving analyses |
| `models/`, `schemas/` | Database models and API/Pydantic contracts |
| `observability/` | The Prometheus metrics |
| `core/` | Settings, database session, logging |
| `migrations/` | Alembic migrations |

The reasoning behind this layout is in [docs/architecture.md](../docs/architecture.md), and
[docs/development.md](../docs/development.md) shows how to add a technology, an endpoint or a
migration.

## Configuration

Everything comes from environment variables, and every one has a sensible default. `.env.example`
lists them all with comments. The ones you are most likely to touch:

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://admin:admin@localhost:5432/devops_insights` | Where the data lives |
| `GITHUB_TOKEN` | empty | Optional. Raises GitHub's limit from 60 to 5000 requests an hour |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | `http://localhost:11434`, `qwen3:1.7b` | The local AI model |
| `COLLECTION_INTERVAL_SECONDS` | `21600` | Time between scheduled collections |
| `COLLECTION_ON_STARTUP` | `true` | Collect immediately when the worker starts |

## The container

The image is built in two stages, runs as a non-root user and works with any user ID in group 0,
which is what OpenShift needs. It is published for `linux/amd64` and `linux/arm64`.
