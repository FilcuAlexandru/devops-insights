# Argo CD

Two Application manifests that tell Argo CD to deploy the Helm chart from this repository.

| File | Cluster | Values file |
|---|---|---|
| `application-kind.yaml` | A local kind cluster with Argo CD installed by `scripts/argocd-install.sh` | `values-kind.yaml` |
| `application-openshift.yaml` | OpenShift with the *Red Hat OpenShift GitOps* operator | `values-openshift.yaml` |

Both use automated sync with pruning and self-healing, so whatever is in Git is what runs.

## Things to know before applying them

- **Argo CD reads from GitHub, not from your disk.** Push your changes first.
- **Pin a release if you want stability.** `targetRevision` is `main`, which follows every merge.
  Change it to a tag such as `v0.2.0` to deploy exactly that version.
- **The kind application uses locally built images**, so run `make kind-load` first. Don't also run
  `make k8s-deploy`; once Argo CD owns the release, let it stay that way.
- **On OpenShift** the target project must be labelled so the operator may deploy into it:
  `oc label namespace devops-insights argocd.argoproj.io/managed-by=openshift-gitops`.

Installing Argo CD on kind, its login (admin / admin) and how to open it are covered in
[docs/kubernetes.md](../../docs/kubernetes.md).
