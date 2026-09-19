# OpenShift

Two small files live here. The full walkthrough is in [docs/openshift.md](../../docs/openshift.md),
so this page is only a map.

| File | What it is for |
|---|---|
| `build.yaml` | An ImageStream and a BuildConfig for each image, so OpenShift can build the backend and the frontend itself from your local source. That way you don't need an external registry |
| `arbitrary-uid-test.yaml` | Helm values that make a plain Kubernetes cluster start every pod with a random user ID and group 0, the way OpenShift does. It lets you check the images on kind, without an OpenShift cluster |

The Helm values for OpenShift are in `deploy/helm/devops-insights/values-openshift.yaml`, and the
matching Argo CD application is `deploy/argocd/application-openshift.yaml`.

## The short version

After `oc login`, one command does everything: it creates the project, builds both images inside
the cluster, installs the chart with your cluster's domain, waits for the workloads and runs the
smoke test against the Routes.

```bash
make openshift-deploy
```

The guide explains how to get a cluster of your own on Windows, Linux or macOS with OpenShift
Local, and what to do when a step fails.

## Where things stand

The chart renders and lints cleanly for OpenShift, and every workload has been started with a
random user ID and group 0 on kind. The parts that need a real OpenShift (Routes, image builds
inside the cluster, the internal registry) haven't been run on one yet. `make openshift-deploy` is
there to do exactly that, and if something needs adjusting on your first run, this is the place to
look.
