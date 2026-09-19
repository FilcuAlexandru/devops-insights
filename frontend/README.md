# Frontend

The web interface of DevOps Insights. It is a static single-page app: plain HTML, CSS and
JavaScript modules with no build step, so there is no `npm install`, no bundler and nothing to
compile. Chart.js is included in the repository, so the page works without internet access.

## Pages

| Route | Page |
|---|---|
| `#/` | Dashboard: totals, charts, top and fastest-growing repositories, AI summaries, *Collect now* |
| `#/technologies` and `#/technologies/<slug>` | The tracked technologies and their repositories |
| `#/repositories` and `#/repositories/<id>` | Searchable list, then metrics, trend charts, snapshots and AI analysis |
| `#/platform` | Every component of the deployment with its address and login |

## Running it

```bash
make run-frontend    # http://localhost:8080
```

That starts `dev_server.py`, a small Python server that serves `public/` and forwards `/api` to the
backend on port 8000, exactly what nginx does in the container. Start the backend first
(`make run-backend`), otherwise every page shows an error such as "Request failed with HTTP 502".

```bash
make test-frontend   # unit tests for the pure logic, run in Docker so you don't need Node
```

## How the code is organised

```
public/
├── index.html
└── assets/
    ├── css/        tokens (colours), base, layout, components
    ├── js/
    │   ├── main.js        the list of routes
    │   ├── core/          router, API client, HTML escaping, formatting, Markdown
    │   ├── components/    charts, tables, toasts, the collect and analysis widgets
    │   └── pages/         one module per page
    └── vendor/     Chart.js (MIT licensed, license file included)
```

A page is a module that exports `render({ params, query })` and returns a title, the HTML, and an
optional `mount` function for things that need the DOM, such as charts and click handlers.
Adding a page means writing that module and adding one line to `main.js`.

One rule matters more than the others: **text from the API is never glued into HTML by hand.**
Repository names and descriptions come from GitHub, so every template goes through the `html`
tag in `core/html.js`, which escapes everything by default. The Markdown of the AI analysis is
escaped first and formatted second.

## In the container

nginx serves `public/` on port 8080, forwards `/api` to `BACKEND_URL` and answers `/healthz`.
When it starts, it generates `/config.js` from `PLATFORM_ENVIRONMENT` and the `LINK_*` variables,
which is how the Platform page knows the Grafana or Argo CD address of the environment it runs
in. Because of that, one image works on Docker Compose, Kubernetes and OpenShift. It runs as an
unprivileged user and works with any user ID in group 0.
