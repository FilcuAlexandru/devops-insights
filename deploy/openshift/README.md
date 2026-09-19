# OpenShift

Two small files live here. The full walkthrough is in [docs/openshift.md](../../docs/openshift.md);
this page is just a map.

| File | What it is for |
|---|---|
| `build.yaml` | An ImageStream and a BuildConfig for each image, so OpenShift can build the backend and the frontend itself from your local source. That way you don't need an external registry |
| `arbitrary-uid-test.yaml` | Helm values that make a plain Kubernetes cluster start every pod with a random user ID and group 0, the way OpenShift does. It lets you check the images on kind, without an OpenShift cluster |

The Helm values for OpenShift are `deploy/helm/devops-insights/values-openshift.yaml`, and the
matching Argo CD application is `deploy/argocd/application-openshift.yaml`.

## The short version

```bash
oc new-project devops-insights
oc apply -f deploy/openshift/build.yaml
oc start-build devops-insights-backend  --from-dir=backend  --follow
oc start-build devops-insights-frontend --from-dir=frontend --follow
```

Then install the chart with your cluster's apps domain, as described in the guide.

## One command

After `oc login`, `make openshift-deploy` does all of the above and verifies the result. The
step-by-step guide for OpenShift Local on a Mac is in [docs/openshift.md](../../docs/openshift.md).

## An honest note

The chart renders and lints cleanly for OpenShift, and every workload was started with a random
user ID and group 0 on kind. Routes, BuildConfig builds and the internal registry were not tested
on a real OpenShift cluster yet; `make openshift-deploy` is there to do exactly that. If something needs adjusting on your first run, this is the place to
look.
