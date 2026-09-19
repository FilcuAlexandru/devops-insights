# Kubernetes lab manifests

These are small workloads for practising how Kubernetes behaves: what happens when a container
hits its CPU limit, when it runs out of memory, when it needs storage, or when you just want a
pod to `curl` things from inside the cluster.

They are **not** part of DevOps Insights and the Helm chart never installs them. They all live in
the `devops-insights` namespace.

| File | What it teaches |
|---|---|
| `cpu-stress.yaml` | A busy loop with a 500m CPU limit. Watch it get throttled with `kubectl top pod` |
| `memory-stress.yaml` | Allocates memory until it passes its 32Mi limit and is killed (`OOMKilled`, then `CrashLoopBackOff`) |
| `storage-pvc.yaml`, `storage-test.yaml` | A PersistentVolumeClaim and a pod that mounts it at `/data`, for trying out persistence |
| `curl-client.yaml` | A pod with `curl`, handy for testing Services and DNS from inside the cluster |

```bash
kubectl apply -f deploy/kubernetes/base/namespace.yaml
kubectl apply -f deploy/kubernetes/lab/cpu-stress.yaml
```

Clean up with `kubectl delete -f deploy/kubernetes/lab/`.
