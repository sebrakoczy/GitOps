# Question Bank Expansion Roadmap

The MVP includes 60 questions and 8 labs. Expand toward a full Senior Platform Engineer prep bank with these targets.

## Target inventory

| Domain | Target questions | Target hands-on labs |
|---|---:|---:|
| Kubernetes Core | 150 | 40 |
| Kubernetes Troubleshooting | 125 | 50 |
| Kubernetes Security | 125 | 40 |
| Linux Systems | 125 | 35 |
| Bash Automation | 100 | 40 |
| Terraform / IaC | 125 | 40 |
| Ansible | 75 | 25 |
| GitOps / CI/CD | 100 | 35 |
| Observability / SRE | 100 | 30 |
| Platform Engineering | 100 | 20 |
| Cloud / Networking | 100 | 25 |
| System Design | 75 | 25 |

## High-value lab ideas

### Kubernetes

- Fix a CrashLoopBackOff caused by bad env vars.
- Fix a Service selector mismatch.
- Debug a pending pod caused by unbound PVC.
- Add correct resource requests/limits.
- Add readiness/liveness/startup probes.
- Convert a Deployment into a Helm chart.
- Write a NetworkPolicy allowing frontend to API only.
- Create a least-privilege Role and RoleBinding.
- Restore a broken Argo CD app sync.
- Diagnose CoreDNS resolution failure.

### Linux

- Create a systemd service and timer.
- Rotate and compress logs.
- Find top disk-consuming directories.
- Debug a failed service from journald logs.
- Diagnose port/listener conflicts.
- Add sysctl values for Kubernetes networking.

### Bash

- Parse logs with awk/sed/grep/jq.
- Write idempotent backup scripts.
- Add error handling and cleanup traps.
- Build a certificate expiry checker.
- Build a Kubernetes namespace report.

### Terraform

- Create reusable VPC module inputs/outputs.
- Refactor hard-coded values into variables.
- Fix type errors in variables.
- Configure S3 + DynamoDB backend.
- Import an existing security group.
- Write validation blocks.
- Split environment values with tfvars.

### Ansible

- Patch Linux hosts with rollback notes.
- Template nginx or HAProxy config.
- Use handlers correctly.
- Add Ansible Vault variables.
- Create a reusable role.
- Use facts and conditionals.

### GitOps / CI/CD

- Build and push image with GitHub Actions.
- Update Helm values via PR.
- Add image scanning and secret scanning.
- Roll back by reverting Git.
- Create Argo CD app-of-apps layout.

### SRE / Observability

- Write Prometheus alert rules.
- Define SLO and burn-rate alerts.
- Build Grafana dashboard JSON.
- Analyze incident timeline.
- Tune noisy alerts.
