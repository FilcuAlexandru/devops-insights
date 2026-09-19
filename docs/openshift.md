# OpenShift

Getting this project onto OpenShift was one of the goals from the start, so the Helm chart is
built for it rather than adapted afterwards. The same chart that runs on a plain Kubernetes
cluster runs on OpenShift; `values-openshift.yaml` only switches a few things: Routes instead of
NodePorts, images built inside the cluster, and no fixed user IDs.

That last point is the one that matters. OpenShift refuses to start a container as a user of its
own choosing and instead assigns a random high user ID that always belongs to group 0. Many
images break when that happens (the official PostgreSQL image is the classic example). Every
image used here works with an arbitrary user ID, and the chart never asks for a specific one.

This guide shows how to get a real OpenShift on your own computer (Windows, Linux or macOS),
deploy the project onto it, and check that everything works.

## What has been tested and what hasn't

I would rather tell you this up front than have you find out halfway through.

| What | Status |
|---|---|
| `helm lint` and `helm template` with `values-openshift.yaml` | Passed |
| Manifests checked with kubeconform | Passed (Route objects have no public schema, so they are skipped) |
| All seven workloads started with a random user ID (`1000680000`) and group 0, the way OpenShift's `restricted-v2` policy starts containers, on a kind cluster | Passed: migrations, collection, Prometheus, Grafana and the Ollama model download all worked |
| `scripts/openshift-deploy.sh` with a simulated `oc` and a real `helm template` | Passed: right order of commands, right image paths, right route hosts |
| `scripts/smoke-test.sh` against Docker Compose and Kubernetes | Passed, and it fails correctly when a component is down |
| Routes, TLS, image builds inside the cluster, the internal registry, on a real OpenShift | **Not run yet** |

The last row is the honest gap. Installing a real cluster needs a Red Hat account (for the pull
secret) and administrator rights on the machine, which are yours to give and not mine. The steps
below get you there, and one command then does the whole deployment and the checking.

You can repeat the random-user-ID test on any Kubernetes cluster, no OpenShift required:

```bash
make kind-load
helm install uid-test deploy/helm/devops-insights \
  -f deploy/helm/devops-insights/values-openshift.yaml \
  -f deploy/openshift/arbitrary-uid-test.yaml -n uid-test --create-namespace
```

## Choosing a cluster

| Option | Good for | Things to know |
|---|---|---|
| **OpenShift Local** (also called CRC), `openshift` preset | Real OpenShift on your own machine, Windows, Linux and macOS (including Apple silicon) | Free, but needs a Red Hat account for the pull secret |
| **OpenShift Local**, `okd` preset | The same, without any Red Hat account | The community version of OpenShift. Not available on Apple silicon Macs |
| **Red Hat Developer Sandbox** | Nothing to install | Free and hosted, but its quota is small (check the current limits) and you get no cluster-admin rights. Disable the AI runtime with `OLLAMA=false` if it doesn't fit |
| A full OpenShift 4 cluster | Work or team environments | Works the same way as below |

OpenShift Local runs the whole cluster as a single virtual machine on your computer. It needs
**4 physical CPU cores, 10.5 GB of free memory and 35 GB of disk** at the very least, and it
cannot run inside another virtual machine (no nested virtualisation). This project plus the AI
model wants a bit more, so give it around 14 GB if you can, and close Docker Desktop while it
runs. A machine with 16 GB of RAM is tight; 32 GB is comfortable.

## Installing OpenShift Local

The details follow Red Hat's own documentation (https://crc.dev/docs/installing/). One rule
applies everywhere: **run `crc` as your normal user, never as root or as an administrator.** It
asks for elevated rights itself when it needs them. Also turn off any VPN before starting.

### Get the download and the pull secret

1. Go to https://console.redhat.com/openshift/create/local and sign in, or create a free
   account.
2. Download OpenShift Local for your operating system.
3. On the same page, copy (or download) your **pull secret**. You paste it when `crc start`
   asks for it. Only the `openshift` preset needs one; with the `okd` preset you can skip this
   step and the account entirely.

### macOS

You need macOS 15 (Sequoia) or newer. Apple silicon and Intel Macs are both supported.

1. Open the downloaded `.pkg` and follow the installer. It asks for your macOS password.
2. Open a new Terminal window and check that it worked:

```bash
crc version
```

### Linux

Red Hat's supported systems are RHEL, CentOS and Fedora. Ubuntu and Debian are not officially
supported: they usually work, but expect to do some set-up by hand.

1. Install the two things `crc` depends on.

   On Fedora, CentOS or RHEL:

```bash
sudo dnf install libvirt NetworkManager
```

   On Ubuntu or Debian:

```bash
sudo apt install qemu-kvm libvirt-daemon libvirt-daemon-system network-manager
```

2. Unpack the download and put `crc` somewhere on your `PATH`:

```bash
cd ~/Downloads && tar xvf crc-linux-amd64.tar.xz
```

```bash
mkdir -p ~/bin && cp ~/Downloads/crc-linux-*-amd64/crc ~/bin
```

```bash
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc && export PATH=$PATH:$HOME/bin
```

3. Check it:

```bash
crc version
```

### Windows

You need a fully updated **Windows 11**. Windows 10 and the **Home** edition are not supported.

1. Extract the download and run the guided installer. **Install it on your `C:` drive**; CRC does
   not work from a network drive.
2. Sign out and back in afterwards, so your account picks up the permissions the installer set
   up.
3. Open **PowerShell** as your normal user (not "Run as administrator") and check:

```powershell
crc version
```

### Prepare the machine, start the cluster

These commands are the same everywhere (in PowerShell on Windows). Start by sizing the virtual
machine. The values are the minimum defaults or higher, and they have to be set while the cluster
is stopped:

```bash
crc config set memory 14336
```

```bash
crc config set cpus 6
```

```bash
crc config set disk-size 60
```

If you want the OKD preset (no Red Hat account, not on Apple silicon), select it now:

```bash
crc config set preset okd
```

Then prepare the machine. This is the step that asks for your macOS or Linux password, or shows
a Windows administrator prompt, because it configures networking and the hypervisor:

```bash
crc setup
```

Finally start the cluster. The first start downloads roughly 4 GB and takes 10 to 20 minutes. When
it asks for the pull secret, paste it (not needed for OKD). At the end it prints the console
address and the login for the `kubeadmin` account:

```bash
crc start
```

Add the bundled `oc` command to your shell. On macOS and Linux:

```bash
eval $(crc oc-env)
```

On Windows PowerShell:

```powershell
crc oc-env | Invoke-Expression
```

Then log in as the ordinary `developer` user, which is all this project needs:

```bash
oc login -u developer -p developer https://api.crc.testing:6443
```

If you lose the credentials later, `crc console --credentials` prints them again.

## Deploying the project

You also need [Helm](https://helm.sh/docs/intro/install/) on your machine. On macOS,
`brew install helm`; on Windows, `winget install Helm.Helm`; on Linux, your package manager or the
installer from the Helm website.

From the repository, one command builds both images inside the cluster, installs the chart with
your cluster's domain, waits for everything to start and runs the smoke test against the Routes.
The first time, leave the AI runtime out to keep memory low:

```bash
OLLAMA=false make openshift-deploy
```

A final `All checks passed.` means the project works on OpenShift. To add the AI runtime later
(it needs about 4 GiB more memory), run it again without the switch; `SKIP_BUILD=1` reuses the
images you already built:

```bash
SKIP_BUILD=1 make openshift-deploy
```

`make openshift-deploy` prints the addresses when it finishes, and you can print them again with
`make urls-openshift`. Grafana and Prometheus use the usual **admin / admin**.

### On Windows

There is no `make` on Windows by default, and the scripts are written for a Unix shell. The
easiest way is **Git Bash**, which comes with Git for Windows. Open it, make sure `oc` and `helm`
are available (`crc oc-env` prepares `oc`, see above), and run the script directly:

```bash
OLLAMA=false sh scripts/openshift-deploy.sh
```

I could not try the Windows and Linux routes myself (my machine is a Mac), so they follow Red
Hat's documentation and the commands are the ones the project uses everywhere else. If something
needs adjusting on your system, please open an issue with the output.

### Doing it by hand

`scripts/openshift-deploy.sh` is only these steps in a row, so you can run them yourself to see
what happens.

Create a project and build the two images inside the cluster:

```bash
oc new-project devops-insights
```

```bash
oc apply -f deploy/openshift/build.yaml
```

```bash
oc start-build devops-insights-backend --from-dir=backend --follow
```

```bash
oc start-build devops-insights-frontend --from-dir=frontend --follow
```

Work out your cluster's domain from the console address (the part after
`console-openshift-console.`):

```bash
DOMAIN=$(oc whoami --show-console | sed -E 's#https://console-openshift-console\.##')
```

Install the chart:

```bash
helm upgrade --install devops-insights deploy/helm/devops-insights \
  -f deploy/helm/devops-insights/values-openshift.yaml \
  --set route.appsDomain="$DOMAIN" \
  --namespace devops-insights --wait --timeout 15m
```

Then check it from the outside:

```bash
INSECURE=1 FRONTEND_URL=https://frontend-devops-insights.$DOMAIN scripts/smoke-test.sh
```

The images are referenced as `image-registry.openshift-image-registry.svc:5000/devops-insights/...`.
If your project has another name, add
`--set backend.image.repository=image-registry.openshift-image-registry.svc:5000/<project>/devops-insights-backend`
and the same for `frontend.image.repository`. (`openshift-deploy.sh` does this for you when you set
`PROJECT`.)

You can also skip the local build and use the images that the release pipeline publishes, once
they are public: set `backend.image.repository` to `ghcr.io/<owner>/devops-insights-backend` and
`frontend.image.repository` to `ghcr.io/<owner>/devops-insights-frontend`.

## What you get

| Component | Address | Login |
|---|---|---|
| Web application | `https://frontend-<project>.<domain>` | none |
| Backend API | `https://backend-<project>.<domain>/api/docs` | none |
| Grafana | `https://grafana-<project>.<domain>` | admin / admin |
| Prometheus | `https://prometheus-<project>.<domain>` | admin / admin |

PostgreSQL and Ollama stay inside the cluster. To reach the database from your computer, forward
the port and connect as usual:

```bash
oc port-forward svc/devops-insights-postgresql 5432:5432
```

Then `psql postgresql://admin:admin@localhost:5432/devops_insights` in another window.

## Argo CD on OpenShift

On OpenShift, Argo CD comes from the **Red Hat OpenShift GitOps** operator, which you install
from OperatorHub in the web console. It runs in the `openshift-gitops` namespace and is exposed
through a Route:

```bash
oc get route openshift-gitops-server -n openshift-gitops -o jsonpath='https://{.spec.host}{"\n"}'
```

The operator generates the `admin` password and keeps ownership of it, so unlike on kind this
one **cannot be set to `admin`**. Read it with:

```bash
oc get secret openshift-gitops-cluster -n openshift-gitops -o jsonpath='{.data.admin\.password}' | base64 -d
```

Everything else in the project keeps `admin / admin`. To let this Argo CD deploy into your
project and create the application (put your cluster's domain in the file first):

```bash
oc label namespace devops-insights argocd.argoproj.io/managed-by=openshift-gitops
```

```bash
oc apply -f deploy/argocd/application-openshift.yaml
```

Argo CD reads from GitHub, so the repository has to be pushed first.

## How the chart adapts to OpenShift

| Concern | What the chart does |
|---|---|
| Random user IDs | `values-openshift.yaml` sets no `runAsUser` or `fsGroup`, and every image runs as any user in group 0 |
| Images that insist on root | Ollama runs as a non-root user, and PostgreSQL is Red Hat's `sclorg` image instead of the upstream one |
| Images with a non-numeric user (Prometheus) | The fixed user ID used on plain Kubernetes is removed; OpenShift injects one |
| Exposure | Routes with edge TLS and an HTTP to HTTPS redirect, named `<component>-<project>.<apps domain>` |
| Permissions | Prometheus finds its targets with a namespaced `Role`, no cluster-wide rights needed |
| Storage | PersistentVolumeClaims with the cluster's default storage class |
| Hardening | All capabilities dropped, no privilege escalation, seccomp `RuntimeDefault` |

## When something goes wrong

| What you see | What to try |
|---|---|
| `crc setup` complains about virtualisation | Enable virtualisation in the BIOS/UEFI. CRC cannot run inside another virtual machine |
| `crc start` fails on DNS or networking | Turn off your VPN and try again; on Linux make sure `NetworkManager` is running |
| `ImagePullBackOff` on the backend or frontend | The builds are not finished or the project has another name: check `oc get builds` and `oc get imagestreams` |
| `unable to validate against any security context constraint` | An image needs a fixed user ID. Check that you installed with `values-openshift.yaml` |
| The Grafana or Prometheus link is empty on the Platform page | `route.appsDomain` wasn't set. Run the install again with `--set route.appsDomain=...` |
| The Ollama pod is `OOMKilled` | The cluster doesn't have enough memory. Give CRC more, or install with `OLLAMA=false` |

## Cleaning up

Pause the cluster and keep everything:

```bash
crc stop
```

Delete the cluster completely:

```bash
crc delete
```

Or only remove this project and keep the cluster:

```bash
helm uninstall devops-insights -n devops-insights
```

```bash
oc delete project devops-insights
```
