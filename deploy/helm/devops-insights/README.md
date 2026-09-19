# Helm chart

One chart that deploys the whole platform on Kubernetes or OpenShift: the backend, the collector,
the frontend, PostgreSQL, Ollama, Prometheus and Grafana. Every login is `admin / admin`.

```bash
helm install devops-insights deploy/helm/devops-insights \
  -f deploy/helm/devops-insights/values-kind.yaml \
  -n devops-insights --create-namespace
```

Once a release is published, the chart is also available from GitHub's registry:

```bash
helm install devops-insights oci://ghcr.io/filcualexandru/charts/devops-insights \
  --version 0.2.0 -n devops-insights --create-namespace
```

## Values files

| File | Purpose |
|---|---|
| `values.yaml` | Defaults that work anywhere |
| `values-kind.yaml` | Local kind cluster: NodePorts (30080, 30800, 30300, 30900, 30432, 31434) and locally built images |
| `values-openshift.yaml` | OpenShift: Routes, images from the internal registry, and no fixed user IDs |

## The options you will actually change

| Value | Default | What it does |
|---|---|---|
| `backend.image.*`, `frontend.image.*` | GitHub registry images | Where the images come from. The tag defaults to the chart's `appVersion` |
| `collector.intervalSeconds` | `21600` | How often the collector runs |
| `collector.githubToken` | empty | Optional GitHub token for a higher rate limit |
| `ollama.enabled`, `ollama.model` | `true`, `qwen3:1.7b` | Turn the AI off or pick another model. It is the heaviest part (1 GiB requested, 4 GiB limit) |
| `postgresql.enabled`, `externalDatabase.url` | `true` | Use the bundled database or your own |
| `*.persistence.enabled`, `*.persistence.size` | on | Storage for the database, Ollama, Prometheus and Grafana |
| `*.service.type`, `*.service.nodePort` | `ClusterIP` | How each component is exposed |
| `ingress.enabled`, `ingress.host` | off | An Ingress for the web application |
| `route.enabled`, `route.appsDomain` | off | OpenShift Routes named `<component>-<project>.<apps domain>` |
| `links.*` | empty | Addresses shown on the Platform page. Filled in automatically when Routes are on |

## What it creates

| Component | Kind | Worth knowing |
|---|---|---|
| backend | Deployment, Service, Secret | An init container waits for PostgreSQL and applies the migrations |
| collector | Deployment (one replica), Service | Owns the schedule, so scaling the backend never multiplies GitHub requests |
| frontend | Deployment, Service | nginx on port 8080 forwarding `/api` to the backend |
| postgresql | StatefulSet, Service, Secret | Red Hat's image, which runs with any user ID |
| ollama | Deployment, Service, PVC | Downloads the model on its first start |
| prometheus | Deployment, Service, PVC, Role | Finds the backend and the collector through their Services |
| grafana | Deployment, Service, PVC, ConfigMaps | Datasource and dashboard are provisioned |

## Design choices

- The chart never sets `runAsUser` unless an image absolutely needs it (Prometheus and Ollama on
  plain Kubernetes). That is what lets the same chart pass OpenShift's security constraints.
- Migrations run in an init container under a database lock, so nothing depends on Helm hook
  ordering, and Argo CD needs no special handling.
- Prometheus is behind basic auth, so its probes send the `Authorization` header.
- The Grafana dashboard under `files/` is a copy of `monitoring/grafana/dashboards/`; keep it in
  sync with `make sync-monitoring`.

More on Kubernetes in [docs/kubernetes.md](../../../docs/kubernetes.md) and on OpenShift in
[docs/openshift.md](../../../docs/openshift.md).
