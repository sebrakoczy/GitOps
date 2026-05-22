# Secure Runner Design

The runner is the highest-risk part of this platform because it may eventually execute untrusted code.

## Controls required before enabling live execution

1. Use a dedicated namespace such as `skillforge-runners`.
2. Apply default-deny ingress and egress NetworkPolicies.
3. Use a dedicated ServiceAccount with only the permissions required to create, watch, log, and delete Jobs.
4. Set `automountServiceAccountToken: false` on runner Jobs unless a test explicitly needs Kubernetes API access.
5. Never mount production secrets into runner pods.
6. Use `runAsNonRoot`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, dropped Linux capabilities, and `seccompProfile: RuntimeDefault`.
7. Set CPU/memory requests and limits.
8. Use `activeDeadlineSeconds` for wall-clock timeout.
9. Use `ttlSecondsAfterFinished` for cleanup.
10. Use image allowlists and immutable image digests for runner images.
11. Do not allow privileged pods, host networking, host PID, host IPC, or hostPath.
12. Store only sanitized logs/results.

## Recommended runner tiers

### Tier 1: Static validation

Safe for first MVP. Uses regex, keyword, and structure checks.

### Tier 2: Tool-only validation

Runs non-networked tools such as:

- `terraform fmt -check`
- `terraform validate` against mocked providers
- `yamllint`
- `kubeconform`
- `ansible-lint`
- `shellcheck`

### Tier 3: Ephemeral sandbox execution

Executes code in short-lived Jobs with no secrets, no egress, strict resource limits, and aggressive cleanup.

### Tier 4: Disposable cluster labs

For real Kubernetes troubleshooting labs, use a disposable namespace or disposable lightweight cluster environment. Do not run destructive labs in the management namespace.
