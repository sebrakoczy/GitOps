# Safe Code Judge Design

The MVP intentionally does not execute arbitrary candidate code on the API server. That is the correct security posture for a homelab and especially for a production-like platform.

## Recommended design

1. API receives a code submission.
2. API creates a Kubernetes `Job` in a dedicated `skillforge-runner` namespace.
3. Each job uses a language-specific runner image such as `python-runner`, `go-runner`, or `node-runner`.
4. Runner pod mounts a ConfigMap or projected volume containing candidate code and test cases.
5. Pod has strict limits:
   - `runAsNonRoot: true`
   - `allowPrivilegeEscalation: false`
   - `readOnlyRootFilesystem: true`
   - `capabilities.drop: ["ALL"]`
   - CPU and memory limits
   - `activeDeadlineSeconds`
   - no service account token
   - deny-all NetworkPolicy
   - seccomp RuntimeDefault
6. API watches the Job, collects logs, deletes the pod, and stores result metadata.

## Add-on options

- Judge0 CE, self-hosted behind an internal service.
- Custom ephemeral Kubernetes Jobs for each language.
- gVisor or Kata Containers for stronger isolation.
- Firecracker-based microVM judge if you want stronger multi-tenant isolation.

## Never do this

- Do not use Docker socket mounts.
- Do not run candidate code inside the API container.
- Do not run privileged pods.
- Do not allow outbound internet by default.
- Do not share persistent volumes between candidate jobs.
