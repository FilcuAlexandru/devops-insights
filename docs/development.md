# Working on the code

This is the guide for changing the project. Set things up with `make setup`, then follow
[local-testing.md](local-testing.md#b-development-mode) to run the backend and the frontend.
`make help` lists everything you can do.

## House rules

A few habits keep the project easy to live with:

- Code, comments, commit messages and documentation are written in English.
- Python is formatted and linted by Ruff (`make format`, `make lint`), with a line length of 100.
  Functions have type hints, and public functions and classes get a one-line docstring.
- JavaScript uses ES modules, four spaces of indentation and no build step. Text that comes from
  the API or from GitHub goes into the page only through the `html` tagged template in
  `core/html.js`, never through string concatenation. That single rule is what keeps the interface
  safe.
- Every new behaviour comes with a test. Tests never call GitHub or Ollama; they use fakes,
  `httpx.MockTransport` and `monkeypatch`.
- Layers only depend downwards: `api` calls `services`, `analytics` and `ai`, which use `models`
  and `schemas`, which sit on `core`. `analytics/trends.py` has no database code, so you can test
  it without a database.

## Tracking another technology or repository

Open `backend/src/devops_insights/catalog/technologies.py` and either add a new
`TechnologyDefinition`, or add an `"owner/name"` to the `repositories` of an existing one. The
tests check that slugs and repositories are unique and well formed. The next collection creates
the technology and the repository, and nothing needs restarting. Remember that one collection
costs one GitHub request per repository.

## Adding an API endpoint

1. Write the query or the use case in `services/`, or in `analytics/` if it is a pure
   calculation.
2. Add or extend a Pydantic schema in `schemas/`.
3. Add the route to a module in `api/routes/` (or create a module and register it in
   `api/app.py`). Keep the route thin: read the request, call the service, return the result.
4. Write tests: one for the service, and one in `backend/tests/test_api_*.py` for the route, using
   the `client` and `session` fixtures.
5. Add it to the table in [urls-and-credentials.md](urls-and-credentials.md).

## Changing the database

Let Alembic write the first draft:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
```

Read the generated file in `migrations/versions/` carefully, then apply it with `make migrate`.
CI runs `alembic check` and fails when the models and the migrations disagree. A migration must
work on a database that already holds data: give new `NOT NULL` columns a `server_default`, and
backfill where it makes sense.

## Adding a page to the frontend

1. Create `frontend/public/assets/js/pages/<name>.js` that exports `render({ params, query })` and
   returns `{ title, content, mount? }`.
2. Register it in `frontend/public/assets/js/main.js` (in `routes`) and, if it belongs in the
   menu, in `frontend/public/index.html`.
3. Reuse what is in `components/` (`ui.js`, `charts.js`, `collection.js` and so on).
4. Test the pure logic in `frontend/tests/` with `make test-frontend`.

## Changing the Grafana dashboard

Edit `monitoring/grafana/dashboards/devops-insights.json`. A good way is to build the panels in the
Grafana interface and export the JSON. Then run `make sync-monitoring` so the Helm chart gets the
same copy.

## Changing the Helm chart

`make helm-lint` lints the chart and renders it for kind and for OpenShift. To see exactly what a
change produces:

```bash
helm template devops-insights deploy/helm/devops-insights -f deploy/helm/devops-insights/values-kind.yaml
```

## New versions

The version number has to be the same in several places, so don't edit it by hand:
`scripts/version.sh set X.Y.Z` writes it into every one of them, and `scripts/version.sh check`
verifies them (the CI does that too). The whole procedure, including the tag that publishes the
images, is in [releasing.md](releasing.md).

## Continuous integration

Every push and pull request runs `.github/workflows/ci.yml`: Ruff, the migrations, `alembic check`
and pytest against a real PostgreSQL, the frontend tests, the version, Helm and monitoring checks,
and the image builds. Pushes to `main` publish development images. `security.yml` runs CodeQL and
Trivy, and `release.yml` publishes tagged releases.
