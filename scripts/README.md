# Scripts

Small shell scripts that back the `make` targets. You usually run them through `make`, but they
work on their own too.

| Script | What it does |
|---|---|
| `urls.sh compose\|kind\|openshift` | Prints every address and login for an environment (`make urls-compose`, and so on) |
| `argocd-install.sh <kube-context>` | Installs Argo CD into a cluster, sets the admin password to `admin` and publishes the UI on port 30443. It asks before touching a cluster and is safe to run again |
| `k8s-port-forward.sh [namespace] [release]` | Publishes the deployed components on localhost with `kubectl port-forward`, on the same ports a kind cluster would use. For clusters that were created without port mappings |
| `sync-monitoring.sh [--check]` | Copies the Grafana dashboard from `monitoring/` into the Helm chart. `--check` only verifies that they match (CI uses it) |
| `smoke-test.sh` | Checks a running deployment from the outside: the web app, the API, the database connection, Grafana and Prometheus logins, scrape targets and the last collection. `FRONTEND_URL` is required, the rest is optional (`make smoke-test`, `make smoke-test-kind`) |
| `openshift-deploy.sh` | Builds the images inside OpenShift, installs the chart with your cluster's domain and runs the smoke test against the Routes (`make openshift-deploy`) |
| `version.sh get\|set X.Y.Z\|check` | Keeps the version consistent across the package, the chart, the image tags and the Makefile |

A few notes:

- `argocd-install.sh` needs the kube context as an argument on purpose, so it can never change
  the wrong cluster by accident. With `SKIP_INSTALL=1` it leaves an existing Argo CD alone and
  only sets the password and the port.
- All scripts are checked with ShellCheck.
