# SkillForge Architecture

## MVP architecture

```text
Browser
  ↓
skillforge-web / nginx
  ↓ /api
skillforge-api / FastAPI
  ↓
PostgreSQL

skillforge-worker
  ↓ future queue processing
Redis
  ↓ future isolated execution
Kubernetes Jobs
```

## Why static grading first?

Running arbitrary code is dangerous. The first release uses static validation so the portal is immediately useful for question practice and YAML/script/IaC pattern checks while we design the runner properly.

## Future secure runner flow

```text
User submits challenge
  ↓
API stores submission and emits queue message
  ↓
Worker reads submission
  ↓
Worker creates short-lived Kubernetes Job
  ↓
Job runs test harness in restricted container
  ↓
Worker reads logs/result artifact
  ↓
Submission marked passed/failed
  ↓
Job is cleaned up by TTL controller
```

## Data model

- Category
- Question
- Challenge
- Attempt
- Submission

The first version seeds content from `content/question-bank.yaml`.

## Homelab deployment model

For your current homelab:

- Namespace: `skillforge`
- StorageClass: `longhorn`
- Web exposure: NodePort initially
- GitOps: Argo CD Application
- Database: in-cluster PostgreSQL StatefulSet for MVP
- Redis: in-cluster StatefulSet for queue/worker expansion

For a more production-like setup later:

- External PostgreSQL or managed database
- External secrets controller
- cert-manager and ingress TLS
- Prometheus metrics and dashboards
- NetworkPolicy enforced by a capable CNI
- Separate runner namespace and stronger sandboxing
