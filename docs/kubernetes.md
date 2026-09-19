# Kubernetes, Helm and Argo CD

The Helm chart in `deploy/helm/devops-insights` deploys the whole platform in one go: the
backend, the collector, the frontend, PostgreSQL, Ollama, Prometheus and Grafana. Every login is
**admin / admin**, like everywhere else in the project.

I tested it on a kind cluster running Kubernetes 1.37: installation, migrations, a full
collection, Prometheus finding its targets, Grafana loading its dashboard, an AI analysis, and
Argo CD with the login `admin / admin`.

## What the chart creates

| Component | Kind of object | Worth knowing |
|---|---|---|
| backend | Deployment and Service | An init container waits for PostgreSQL and applies the migrations |
| collector | Deployment (one replica) and Service | Owns the schedule; exposes metrics on 9102 |
| frontend | Deployment and Service | nginx on 8080, forwards `/api` to the backend |
| postgresql | StatefulSet, Service and Secret | Red Hat's image, which runs as any user; 2 Gi of storage |
| ollama | Deployment, Service and PVC | Downloads the model the first time it starts; 5 Gi of storage |
| prometheus | Deployment, Service, PVC and Role | Finds the backend and the collector through their Services |
| grafana | Deployment, Service, PVC and ConfigMaps | The datasource and the dashboard are provisioned |

On top of that there is an optional Ingress (`ingress.enabled=true`) and, for OpenShift, Routes
(`route.enabled=true`). The values files are `values.yaml` (the defaults), `values-kind.yaml` and
`values-openshift.yaml`; the chart has its own [README](../deploy/helm/devops-insights/README.md)
with the options you are most likely to change.

Ollama is by far the heaviest part (it asks for 1 Gi and may use 4 Gi). If you don't need the AI,
leave it out with `--set ollama.enabled=false`.

## Option 1: a new kind cluster (recommended)

```bash
make kind-up      # the cluster, with every port mapped to your machine
make kind-load    # build both images and load them into the cluster
make k8s-deploy   # helm upgrade --install, waits until it is ready
make urls-kind    # print every address
```

`make k8s-deploy` works on whatever your **current kubectl context** is. `kind create cluster`
switches to the new cluster by itself, but it never hurts to check with
`kubectl config current-context`.

The first start takes a few minutes. The node has to pull the Grafana, Ollama and PostgreSQL
images, and then Ollama downloads the model (1.4 GB). `make k8s-status` shows how far it got.

The ports come from `deploy/kubernetes/kind/cluster.yaml`, and they match the NodePorts in
`values-kind.yaml`:

| Component | Address |
|---|---|
| Web application | http://localhost:30080 |
| Backend API | http://localhost:30800/api/docs |
| Grafana | http://localhost:30300 |
| Prometheus | http://localhost:30900 |
| Argo CD | https://localhost:30443 |
| PostgreSQL | `localhost:30432` |
| Ollama | http://localhost:31434 |

### Check that it works

The quickest way is the smoke test, which runs 21 checks against the deployment:

```bash
make smoke-test-kind
```

You can also look around by hand:

```bash
kubectl get pods -n devops-insights          # everything Running, 1/1
curl http://localhost:30080/healthz          # ok
curl -u admin:admin http://localhost:30900/api/v1/targets
```

The last one should list `backend`, `collector` and `prometheus`, all with `"health":"up"`. After
that, go through the checklist in [local-testing.md](local-testing.md#3-look-at-every-component)
using the `30xxx` addresses.

### After changing some code

```bash
make kind-load
kubectl rollout restart deployment -n devops-insights -l app.kubernetes.io/name=devops-insights
```

### Removing it

```bash
make k8s-undeploy
kubectl delete pvc --all -n devops-insights    # this deletes the data too
make kind-down
```

## Option 2: use a kind cluster you already have

Port mappings can only be chosen when a cluster is created, so an existing cluster can't publish
the components on its own. Instead, `kubectl port-forward` publishes them on the same `30xxx`
ports:

```bash
kubectl config use-context kind-devops-insights   # your cluster
make kind-load                                    # KIND_CLUSTER defaults to "devops-insights"
make k8s-deploy
make k8s-forward                                  # leave this terminal open
```

### If you ran the previous version of this project

The previous version was installed as a Helm release that was **also called `devops-insights`**,
from a different chart, and it left PersistentVolumeClaims behind with the old database. Remove
both first. Otherwise Helm tries to upgrade the old release, and PostgreSQL finds old data
belonging to a different user.

```bash
helm uninstall devops-insights -n devops-insights
kubectl delete pvc --all -n devops-insights    # deletes the old data
```

Or install into another namespace and leave the old one alone:
`make k8s-deploy NAMESPACE=devops-insights-v2`.

## Argo CD

### Installing it

```bash
make argocd-install                               # uses the context kind-$(KIND_CLUSTER)
scripts/argocd-install.sh kind-devops-insights    # or name the context yourself
```

The script installs Argo CD (version `v3.5.3` unless you say otherwise), sets the admin password
to `admin` by writing a bcrypt hash into `argocd-secret`, and publishes the UI on port `30443`. It
asks for confirmation before it touches a cluster, and you can run it as many times as you like.
If Argo CD is already installed and you only want the password and the port, run it with
`SKIP_INSTALL=1`.

Open **https://localhost:30443**, accept the browser's warning about the self-signed certificate,
and log in with **admin / admin**. On a cluster without port mappings, `make k8s-forward`
publishes it on the same port.

### Deploying the application through Argo CD

Argo CD pulls from Git, not from your disk, so the repository has to be on GitHub first:

```bash
git push origin main
kubectl apply -f deploy/argocd/application-kind.yaml
```

That Application points at `deploy/helm/devops-insights` with `values-kind.yaml`, and turns on
automatic sync, pruning and self-healing. `values-kind.yaml` uses locally built images, so load
them into the cluster first (`make kind-load`). Don't also run `make k8s-deploy`: once Argo CD
owns the release, let it be the only one.

## A few choices worth explaining

- **No fixed user IDs.** Pods run as non-root, drop every capability and forbid privilege
  escalation, but the chart doesn't ask for a specific `runAsUser`. The exceptions are Prometheus
  and Ollama on plain Kubernetes, whose images have a non-numeric user. This is what allows the
  same chart to run on OpenShift.
- **Migrations run in an init container**, in both the backend and the collector, under a
  PostgreSQL lock. So nothing depends on Helm hooks running in the right order, and Argo CD
  needs no special treatment.
- **Prometheus authenticates its own probes.** Its UI sits behind basic auth, so the liveness and
  readiness probes send the `Authorization` header.
- **The secrets are plain values.** Everything is `admin / admin` on purpose. A real deployment
  would take them from an external secret store.
