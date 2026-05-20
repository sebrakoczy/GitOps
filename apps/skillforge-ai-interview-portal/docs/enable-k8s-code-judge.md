# Enable the Kubernetes Code Judge

The portal ships with the judge disabled by default. This is intentional because executing user code requires a sandbox.

## Enable in homelab

Edit `k8s/base/api-configmap.yaml` or create a Kustomize patch:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: skillforge-api-config
  namespace: skillforge
data:
  ENABLE_K8S_JUDGE: "true"
  JUDGE_NAMESPACE: skillforge
  JUDGE_TIMEOUT_SECONDS: "20"
```

Then apply:

```bash
kubectl apply -k k8s/overlays/homelab
kubectl -n skillforge rollout restart deploy/skillforge-api
kubectl -n skillforge logs deploy/skillforge-api -f
```

## Verify RBAC

```bash
kubectl -n skillforge auth can-i create jobs --as=system:serviceaccount:skillforge:skillforge-api
kubectl -n skillforge auth can-i get pods/log --as=system:serviceaccount:skillforge:skillforge-api
```

## Verify NetworkPolicy

The included policy denies all egress for pods labeled:

```yaml
app.kubernetes.io/name: skillforge-judge
```

This requires a CNI that enforces NetworkPolicy, such as Cilium, Calico, Antrea, or another compatible CNI. If your CNI does not enforce NetworkPolicy, do not enable the judge for untrusted users.

## Security baseline

Judge pods are created with:

- `automountServiceAccountToken: false`
- `runAsNonRoot: true`
- `runAsUser: 1000`
- `readOnlyRootFilesystem: true`
- `allowPrivilegeEscalation: false`
- dropped Linux capabilities
- CPU and memory limits
- job deadline and cleanup TTL
- NetworkPolicy default-deny egress

## Stronger production design

For a more production-grade version, run the judge in a dedicated namespace with:

- separate node pool or tainted worker nodes
- Kyverno/OPA admission policies
- gVisor or Kata Containers runtime class
- Falco runtime detection
- image allow-listing
- per-submission temporary namespace
- no shared writable volumes
- strict Pod Security Admission restricted profile
