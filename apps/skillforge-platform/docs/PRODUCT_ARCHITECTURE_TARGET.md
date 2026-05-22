# SkillForge Target Production Architecture

SkillForge should become a serious platform engineering interview-prep product, not a generic quiz app. The product should evaluate practical judgment across command-line work, troubleshooting, design tradeoffs, security, reliability, and communication.

## Product principles

1. **Role-specific depth**: focus on Senior Platform Engineer / Kubernetes / DevSecOps / SRE / IaC roles.
2. **Hands-on over trivia**: scenario labs, broken manifests, production debugging, and architecture prompts.
3. **Explain the why**: scoring should reward tradeoffs, safety, validation, and rollback planning.
4. **Safe execution**: never run user code in the API pod; use isolated, resource-limited execution workers.
5. **Content as a product**: question packs should be versioned, reviewed, tagged, and measurable.
6. **Measurable readiness**: users should see domain gaps, skill trends, readiness by role, and recommended next practice.

## Current v0.2 stack

- Frontend: React + Vite + TypeScript
- API: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Worker scaffold: Python worker
- Cache/queue placeholder: Redis
- Deployment: Helm + Kubernetes + Argo CD-ready manifests
- Network: NodePort homelab mode with optional Cilium allow policy
- Content: YAML seed pack with repeatable upsert

## Recommended production stack

### Web and application

- React + TypeScript for the app workspace.
- Next.js or a separate marketing site if SEO/public landing pages become important.
- FastAPI remains a strong fit for the platform API because Python will also power graders, content tooling, and AI evaluation workflows.
- PostgreSQL as the system of record.
- Redis for queues, caching, rate limiting, and short-lived session/state workflows.

### Execution and grading

- Static grading for safe MVP checks.
- Kubernetes Jobs for controlled labs.
- Dedicated runner namespace, dedicated ServiceAccount, no hostPath, no privileged pods.
- Per-job CPU/memory/time limits, TTL cleanup, read-only root filesystem, seccomp, dropped capabilities.
- NetworkPolicy/CiliumPolicy deny egress by default.
- For public untrusted code execution, evaluate stronger isolation such as gVisor, Kata Containers, Firecracker-style microVMs, or a separate disposable runner cluster.

### Security and identity

- OIDC-based auth for users.
- Admin role for content management.
- Separate learner/user/org models.
- Secret management through External Secrets with Vault, AWS Secrets Manager, or SSM Parameter Store.
- Signed images, SBOM generation, dependency scanning, IaC scanning, and admission policy gates.

### Observability and operations

- OpenTelemetry traces and structured JSON logs.
- Prometheus metrics for API latency, errors, attempts, submissions, and grading failures.
- Grafana dashboards and alerting.
- Loki or another log backend for searchable logs.
- Postgres backup/restore runbooks and restore tests.

### Product capabilities to add next

1. Role-based roadmaps: Senior Platform Engineer, Kubernetes Engineer, DevSecOps Engineer, SRE, Cloud Platform Engineer.
2. Interview simulator: timed rounds, domain rotation, follow-up prompts, rubric scoring.
3. AI evaluator: score short answers against rubrics and give coaching feedback.
4. Lab workspaces: browser terminal or remote container shell for hands-on tasks.
5. Admin studio: create/edit/publish/version question packs.
6. User progress: readiness by domain, weak areas, streaks, recommendations.
7. Organization accounts: team dashboards, assignment packs, hiring/interview use cases.
8. Billing: Stripe subscriptions and organization plans.
9. Content QA pipeline: lint question YAML, validate rubrics, detect duplicates, review before publish.
10. Security review process: threat model public code execution before enabling it broadly.
