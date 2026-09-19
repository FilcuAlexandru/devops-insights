# Development guide

Set up with `make setup`, then see [local-testing.md](local-testing.md#b-development-mode-without-docker-for-the-code)
for running the backend and frontend. `make help` lists every task.

## Conventions

- **Code, comments, commit messages and documentation are in English.**
- Python: formatted and linted by Ruff (`make format`, `make lint`), line length 100, type hints
  on function signatures, a one-line docstring on public functions and classes.
- JavaScript: ES modules, no build step, 4-space indent. Text from the API or GitHub is only ever
  inserted through the `html` tagged template (`core/html.js`), never with string concatenation.
- Every new behaviour comes with a test. Tests never call GitHub or Ollama: they use fakes,
  `httpx.MockTransport` and `monkeypatch`.
- Layering: `api` → `services`/`analytics`/`ai` → `models`/`schemas` → `core`. `analytics/trends.py`
  stays free of database access so it can be tested without a database.

## Track another technology or repository

Edit `backend/src/devops_insights/catalog/technologies.py` and add a `TechnologyDefinition`, or add
`"owner/name"` to an existing entry's `repositories`. The tests check that slugs and repositories
are unique and well formed. The next collection creates the technology and the repository; restart
nothing. Remember that one collection uses one GitHub request per repository.

## Add an API endpoint

1. Put the query or use case in `services/` (or `analytics/` if it is a pure calculation).
2. Add or extend a Pydantic schema in `schemas/`.
3. Add the route to a module in `api/routes/` (or a new module registered in `api/app.py`). Keep it
   thin: parse, call, return.
4. Add tests in `backend/tests/test_api_*.py` (use the `client` and `session` fixtures) and a test
   for the service.
5. Document it in `docs/urls-and-credentials.md`.

## Change the database

```bash
cd backend
../backend/.venv/bin/alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `migrations/versions/`, then `make migrate`. `alembic check` (part of
CI) fails when the models and migrations disagree. Migrations must keep working for databases that
already hold data: give new `NOT NULL` columns a `server_default`, and backfill.

## Add a page to the frontend

1. Create `frontend/public/assets/js/pages/<name>.js` exporting
   `render({ params, query })` that returns `{ title, content, mount? }`.
2. Register it in `frontend/public/assets/js/main.js` (`routes`) and, if it belongs in the menu,
   in `frontend/public/index.html`.
3. Shared building blocks are in `components/` (`ui.js`, `charts.js`, `collection.js`, ...).
4. Add unit tests for pure logic in `frontend/tests/` (`make test-frontend`).

## Change the Grafana dashboard

Edit `monitoring/grafana/dashboards/devops-insights.json` (you can build it in the Grafana UI and
export it), then run `make sync-monitoring` to copy it into the Helm chart.

## Change the Helm chart

`make helm-lint` lints the chart and renders it for kind and OpenShift. To check what a change
produces: `helm template devops-insights deploy/helm/devops-insights -f deploy/helm/devops-insights/values-kind.yaml`.

## Releasing a new version

`scripts/version.sh set X.Y.Z` writes the version into every file that carries it, and
`scripts/version.sh check` verifies them (CI runs it). The full procedure, including the tag that
publishes the images, is in [releasing.md](releasing.md).

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request: Ruff, migrations, `alembic check`
and pytest against PostgreSQL; the frontend tests; the version, Helm and monitoring checks; the
image builds. Pushes to `main` publish development images. `security.yml` runs CodeQL and Trivy,
and `release.yml` publishes tagged releases.
