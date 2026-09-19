# OpenShift

The same Helm chart deploys to OpenShift. `values-openshift.yaml` turns on Routes and removes every
fixed user ID, so the `restricted-v2` SecurityContextConstraint can assign its own.

## What was verified, and what was not

| Check | Result |
|---|---|
| `helm lint` and `helm template` with `values-openshift.yaml` | passed |
| Manifests validated with kubeconform | passed (Route objects have no public schema and are skipped) |
| All seven workloads started with a **random user ID (1000680000) and group 0**, the way `restricted-v2` starts containers, on a kind cluster (`deploy/openshift/arbitrary-uid-test.yaml`) | passed: migration, collection, Prometheus, Grafana and the Ollama model download all worked |
| `scripts/openshift-deploy.sh` logic with a simulated `oc` and a real `helm template` | passed: right order of commands, right image paths, route hosts and switches |
| `scripts/smoke-test.sh` against Docker Compose and Kubernetes | passed, and it fails correctly when a component is down |
| Route creation, TLS, BuildConfig builds, the internal registry, SCC admission on a real OpenShift | **not run yet**. Installing a real cluster needs a free Red Hat account (for the pull secret) and your macOS administrator password, which I cannot provide. The steps below get you there, and one command runs the whole check |

You can repeat the arbitrary-user-ID check without OpenShift:

```bash
make kind-load
helm install uid-test deploy/helm/devops-insights \
  -f deploy/helm/devops-insights/values-openshift.yaml \
  -f deploy/openshift/arbitrary-uid-test.yaml -n uid-test --create-namespace
```

## Choose a cluster

| Cluster | Notes |
|---|---|
| **OpenShift Local** (CRC) | Free, runs on your machine. Needs about 4 CPUs, 10 GB memory and 35 GB disk on top of Docker Desktop. Apps domain: `apps-crc.testing`. https://developers.redhat.com/products/openshift-local |
| **Developer Sandbox** | Free, hosted by Red Hat, no installation. Its quota (about 7 GiB memory, 15 GiB storage) is just enough for this chart; use `--set ollama.enabled=false` if it does not fit. No cluster-admin rights, which is fine because the chart only creates namespaced objects. https://developers.redhat.com/developer-sandbox |
| Any OpenShift 4.x | Works the same way |

## OpenShift Local (CRC) on a Mac, step by step

This is the way to get a real OpenShift on your own machine. It needs about 14 GB of memory for
the cluster, so on an 18 GB Mac **quit Docker Desktop while it runs**.

1. **Get the installer and the pull secret** (free). Sign in, or create a Red Hat account, at
   https://console.redhat.com/openshift/create/local and download *OpenShift Local* for macOS and
   copy the **pull secret**.
2. **Install it.** Open the downloaded `.pkg` (macOS asks for your administrator password).
3. **Size the VM** (once):

```bash
crc config set memory 14336
```

```bash
crc config set cpus 6
```

```bash
crc config set disk-size 60
```

4. **Prepare the machine** (asks for your password, it sets up a DNS resolver):

```bash
crc setup
```

5. **Start the cluster.** The first start downloads about 4 GB and takes 10 to 20 minutes. When it
   asks, paste the pull secret. At the end it prints the console URL and the `kubeadmin` password:

```bash
crc start
```

6. **Put `oc` in your shell and log in** (`developer` / `developer` is a regular user and is
   enough for this project):

```bash
eval $(crc oc-env)
```

```bash
oc login -u developer -p developer https://api.crc.testing:6443
```

7. **Deploy and verify, in one command.** The first time, skip the AI to keep memory low:

```bash
OLLAMA=false make openshift-deploy
```

It creates the project, builds both images inside the cluster, installs the chart with the right
domain, waits for every workload and runs the smoke test against the Routes. A green
`All checks passed.` means the deployment works on OpenShift. Then add the AI runtime (needs about
4 GiB more): `make openshift-deploy` (use `SKIP_BUILD=1` to reuse the images).

8. **Look at it in a browser:** `make urls-openshift` prints the Routes. The login for Grafana and
   Prometheus is admin / admin.
9. **Afterwards:** `crc stop` pauses the cluster, `crc delete` removes it.

If any step fails, send me the message, the script prints what it was doing.

The details of each step, and the manual version of the deployment, follow.

## Deploy

```bash
# 1. Log in and create the project (the login command comes from the console: "Copy login command")
oc login ...
oc new-project devops-insights

# 2. Build both images inside the cluster (no external registry needed)
oc apply -f deploy/openshift/build.yaml
oc start-build devops-insights-backend  --from-dir=backend  --follow
oc start-build devops-insights-frontend --from-dir=frontend --follow

# 3. Find the cluster's apps domain (the part after "console-openshift-console.")
DOMAIN=$(oc whoami --show-console | sed -E 's#https://console-openshift-console\.##')
echo "$DOMAIN"

# 4. Install
helm upgrade --install devops-insights deploy/helm/devops-insights \
  -f deploy/helm/devops-insights/values-openshift.yaml \
  --set route.appsDomain="$DOMAIN" \
  --namespace devops-insights --wait --timeout 15m

# 5. Addresses and automated check
make urls-openshift
INSECURE=1 FRONTEND_URL=https://frontend-devops-insights.$DOMAIN scripts/smoke-test.sh
```

`scripts/openshift-deploy.sh` (`make openshift-deploy`) does steps 1 to 5 for you.

The images are referenced as `image-registry.openshift-image-registry.svc:5000/devops-insights/...`.
If your project is not called `devops-insights`, pass
`--set backend.image.repository=image-registry.openshift-image-registry.svc:5000/<project>/devops-insights-backend`
and the same for `frontend.image.repository`.

Instead of building in the cluster you can use images published by the CI workflow:
`--set backend.image.repository=ghcr.io/<owner>/devops-insights-backend` (and `frontend`), with a
public package.

### Routes and logins

| Component | Route | Login |
|---|---|---|
| Web application | `https://frontend-<project>.<domain>` | none |
| Backend API | `https://backend-<project>.<domain>/api/docs` | none |
| Grafana | `https://grafana-<project>.<domain>` | admin / admin |
| Prometheus | `https://prometheus-<project>.<domain>` | admin / admin |

PostgreSQL and Ollama stay inside the cluster. To use the database from your machine:
`oc port-forward svc/devops-insights-postgresql 5432:5432`, then
`psql postgresql://admin:admin@localhost:5432/devops_insights`.

The first start takes several minutes: PostgreSQL, Grafana and Ollama images are pulled, then
Ollama downloads the model. Follow it with `oc get pods -w`.

### Verify

```bash
oc get pods                                  # all Running, 1/1
oc get routes
curl -k https://frontend-devops-insights.$DOMAIN/healthz
```

Then work through [local-testing.md](local-testing.md#3-verify-each-component) using the route
addresses.

## Argo CD on OpenShift

OpenShift's Argo CD comes from the **Red Hat OpenShift GitOps** operator (install it from
OperatorHub). It lives in the `openshift-gitops` namespace and is exposed as a route:

```bash
oc get route openshift-gitops-server -n openshift-gitops -o jsonpath='https://{.spec.host}{"\n"}'
```

The operator generates the `admin` password; read it with
`oc get secret openshift-gitops-cluster -n openshift-gitops -o jsonpath='{.data.admin\.password}' | base64 -d`.
Unlike on kind, **this password cannot be forced to `admin`**: the operator owns the secret and
would overwrite it. Everything else in the platform uses `admin / admin`.

To let this Argo CD deploy into your project and create the application:

```bash
oc label namespace devops-insights argocd.argoproj.io/managed-by=openshift-gitops
oc apply -f deploy/argocd/application-openshift.yaml    # set route.appsDomain in it first
```

The repository must be on GitHub, because Argo CD pulls from Git.

## How the chart adapts to OpenShift

| Concern | Handling |
|---|---|
| Random user ID | No `runAsUser` or `fsGroup` in `values-openshift.yaml`. Every image runs as any user in group 0 |
| Images that run as root by default | Ollama is started as a non-root user; PostgreSQL uses Red Hat's `sclorg` image instead of the upstream one |
| Non-numeric image user (Prometheus) | The fixed `runAsUser` of plain Kubernetes is removed; the SCC injects one |
| Exposure | `Route` objects with edge TLS and HTTP to HTTPS redirect, hosts `<component>-<project>.<apps domain>` |
| RBAC | Prometheus service discovery uses a namespaced `Role`, no `ClusterRole` |
| Storage | PersistentVolumeClaims with the cluster's default storage class |
| Capabilities and privilege escalation | All capabilities dropped, escalation forbidden, seccomp `RuntimeDefault` |

## Troubleshooting

| Symptom | Fix |
|---|---|
| Pods stuck in `ImagePullBackOff` for backend or frontend | The builds have not finished or the project name differs: `oc get builds`, `oc get imagestreams` |
| `Error: ... forbidden: unable to validate against any security context constraint` | An image needs a fixed user ID. Check that you used `values-openshift.yaml` |
| Grafana or Prometheus link is empty on the Platform page | `route.appsDomain` was not set: rerun step 4 with `--set route.appsDomain=...` |
| Ollama pod `OOMKilled` | The Sandbox limit is too low: `--set ollama.enabled=false` |
