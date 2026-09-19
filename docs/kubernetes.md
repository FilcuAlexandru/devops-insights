# Kubernetes, Helm and Argo CD

The chart in `deploy/helm/devops-insights` deploys the whole platform: backend, collector,
frontend, PostgreSQL, Ollama, Prometheus and Grafana. Every login is **admin / admin**.

It was verified on Kubernetes 1.37 with kind: install, migration, collection, Prometheus discovery,
Grafana provisioning, the AI analysis, and Argo CD with login `admin / admin`.

## What the chart creates

| Component | Kind | Notes |
|---|---|---|
| backend | Deployment + Service | Init container waits for PostgreSQL and runs migrations |
| collector | Deployment (1 replica) + Service | Scheduled collection, metrics on 9102 |
| frontend | Deployment + Service | nginx on 8080, proxies `/api` to the backend |
| postgresql | StatefulSet + Service + Secret | Red Hat image, works with any user ID; PVC 2 Gi |
| ollama | Deployment + Service + PVC | Downloads the model on first start; PVC 5 Gi |
| prometheus | Deployment + Service + PVC + Role | Discovers backend and collector through their Services |
| grafana | Deployment + Service + PVC + ConfigMaps | Datasource and dashboard provisioned |

Optional: an Ingress (`ingress.enabled=true`) and OpenShift Routes (`route.enabled=true`).
Values files: `values.yaml` (defaults), `values-kind.yaml`, `values-openshift.yaml`.

Ollama is the heaviest part (request 1 Gi, limit 4 Gi). To run without AI:
`--set ollama.enabled=false`.

## Option 1: a new kind cluster (recommended)

```bash
make kind-up        # cluster with port mappings
make kind-load      # build both images and load them into the cluster
make k8s-deploy     # helm upgrade --install ... --wait
make urls-kind
```

`make k8s-deploy` runs on your **current kubectl context**; `kind create cluster` selects the new
cluster automatically. Check with `kubectl config current-context`.

The first start takes several minutes because the node pulls Grafana, Ollama and PostgreSQL images
and Ollama then downloads the model (1.4 GB). Watch it with `make k8s-status`.

Ports are mapped by `deploy/kubernetes/kind/cluster.yaml` and match the NodePorts in
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

### Verify

```bash
kubectl get pods -n devops-insights       # all Running, 1/1
curl http://localhost:30080/healthz       # ok
curl -u admin:admin http://localhost:30900/api/v1/targets    # backend, collector, prometheus: up
```

Then work through the checklist in [local-testing.md](local-testing.md#3-verify-each-component)
using the `30xxx` addresses.

### Update after changing code

```bash
make kind-load
kubectl rollout restart deployment -n devops-insights -l app.kubernetes.io/name=devops-insights
```

### Remove

```bash
make k8s-undeploy
kubectl delete pvc --all -n devops-insights   # also deletes the data
make kind-down
```

## Option 2: reuse an existing kind cluster

Cluster port mappings can only be defined when a cluster is created, so an existing cluster
publishes the components with `kubectl port-forward` instead, on the same `30xxx` ports:

```bash
kubectl config use-context kind-devops-insights      # your cluster
make kind-load                                       # KIND_CLUSTER defaults to "devops-insights"
make k8s-deploy
make k8s-forward                                     # keep this terminal open
```

### Coming from the previous version of this project

The previous version was installed as a Helm release **also named `devops-insights`**, with a
different chart, and left PersistentVolumeClaims with the old database. Remove both before
installing this version, otherwise Helm tries to upgrade the old release and PostgreSQL finds old
data with a different user:

```bash
helm uninstall devops-insights -n devops-insights
kubectl delete pvc --all -n devops-insights          # deletes the old data
```

Or install into a different namespace: `make k8s-deploy NAMESPACE=devops-insights-v2`.

## Argo CD

### Install

```bash
make argocd-install                       # defaults to context kind-$(KIND_CLUSTER)
# or an explicit context:
scripts/argocd-install.sh kind-devops-insights
```

The script installs Argo CD (`v3.5.3` by default), sets the admin password to `admin` by writing a
bcrypt hash into `argocd-secret`, and publishes the UI on NodePort `30443`. It asks for
confirmation before changing a cluster and can be run repeatedly. If Argo CD is already installed
and you only want the password and the port, run it with `SKIP_INSTALL=1`.

Open **https://localhost:30443** (self-signed certificate: accept the browser warning) and log in
with **admin / admin**. On a cluster without port mappings, `make k8s-forward` publishes it on the
same port.

### Deploy the application through Argo CD (GitOps)

Argo CD pulls from Git, not from your disk, so the repository must be on GitHub first:

```bash
git push origin main
kubectl apply -f deploy/argocd/application-kind.yaml
```

`deploy/argocd/application-kind.yaml` points at `deploy/helm/devops-insights` with
`values-kind.yaml`, automated sync, pruning and self-healing. Load the images into the cluster
(`make kind-load`) because `values-kind.yaml` uses locally built images. Do not also run
`make k8s-deploy`: Argo CD owns the release.

## Design notes

- **No fixed user IDs.** Pods set `runAsNonRoot`, drop all capabilities and forbid privilege
  escalation, but never a `runAsUser` (except where an image's user is not numeric: Prometheus
  and Ollama on plain Kubernetes). This is what lets the same chart run on OpenShift.
- **Migrations run in an init container** of both the backend and the collector, under a
  PostgreSQL advisory lock, so ordering does not depend on Helm hooks.
- **Prometheus authenticates its probes.** Its UI is behind basic auth, so the probes send the
  `Authorization` header.
- **Secrets are plain values.** Everything is `admin / admin` by design; a real deployment would
  use an external secret store.
