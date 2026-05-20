# SkillForge AI Interview Portal

A homelab-ready technical training portal inspired by HackerRank-style challenge practice and AI interviewer workflows.

This starter repo is designed for a Kubernetes homelab and includes:

- React web portal
- FastAPI backend
- PostgreSQL database in Kubernetes
- Role-based timed assessments
- HackerRank-style coding challenge arena
- Visible and hidden test cases
- Submission scoring and leaderboard
- Kubernetes Job-based code judge design
- Browser video recording upload
- Technical scenario scoring
- Optional Ollama-based AI feedback
- Kubernetes manifests with Longhorn PVCs
- Argo CD application manifest
- Safe roadmap for hardening the code judge

## What this MVP does

1. Lets you choose a role track:
   - Senior Platform / Kubernetes Engineer
   - DevSecOps Engineer
   - AI Infrastructure Engineer
2. Loads role-specific timed assessments.
3. Provides function-based coding problems with starter code.
4. Shows visible test cases and scores hidden tests when the judge is enabled.
5. Stores code submissions and exposes a leaderboard.
6. Scores long-form technical scenario answers.
7. Runs mock technical video interviews.
8. Uploads browser-recorded `.webm` answers to the API PVC.
9. Produces a basic interview report.
10. Can use Ollama for LLM feedback, or use the built-in rubric fallback.

## Important security note

The API does **not** execute submitted code directly.

The Kubernetes judge is disabled by default. When enabled, submissions run as short-lived Kubernetes Jobs with resource limits, no service account token, non-root execution, RuntimeDefault seccomp, read-only root filesystem, and a NetworkPolicy that denies egress.

See:

- `docs/enable-k8s-code-judge.md`
- `docs/hackerrank-style-design.md`
- `docs/challenge-authoring.md`

## Local development

```bash
cp .env.example .env
make dev
```

Open:

```text
http://localhost:8080
```

API health:

```bash
curl http://localhost:8000/api/health | jq
```

In local development, the code judge remains disabled unless you explicitly wire Kubernetes access and set `ENABLE_K8S_JUDGE=true`.

## Optional Ollama integration

Run Ollama locally or in Kubernetes, then set:

```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1:8b
```

For Kubernetes, point the API ConfigMap to your in-cluster Ollama service, for example:

```yaml
OLLAMA_BASE_URL: "http://ollama.ollama.svc.cluster.local:11434"
OLLAMA_MODEL: "llama3.1:8b"
```

## Build images

Edit `Makefile` and `k8s/overlays/homelab/images-patch.yaml` to use your real registry.

```bash
export REGISTRY=ghcr.io/YOUR_GITHUB_ORG
export TAG=0.2.0
make docker-build
./scripts/build-and-push.sh
```

## Deploy to your homelab Kubernetes cluster

This overlay assumes Longhorn is available as the `longhorn` StorageClass.

```bash
kubectl apply -k k8s/overlays/homelab
kubectl -n skillforge get pods,pvc,svc,ingress
```

If you do not have ingress working yet, use the included NodePort:

```text
http://<any-worker-node-ip>:32081
```

If you use ingress, add this to your workstation `/etc/hosts`:

```text
<ingress-or-haproxy-ip> skillforge.local
```

Then open:

```text
http://skillforge.local
```

## Enable the Kubernetes code judge

First deploy the included RBAC and NetworkPolicy:

```bash
kubectl apply -k k8s/overlays/homelab
```

Then set:

```yaml
ENABLE_K8S_JUDGE: "true"
```

Restart the API:

```bash
kubectl -n skillforge rollout restart deploy/skillforge-api
kubectl -n skillforge logs deploy/skillforge-api -f
```

Verify permissions:

```bash
kubectl -n skillforge auth can-i create jobs --as=system:serviceaccount:skillforge:skillforge-api
kubectl -n skillforge auth can-i get pods/log --as=system:serviceaccount:skillforge:skillforge-api
```

## Deploy with Argo CD

1. Push this repo to GitHub.
2. Update `k8s/argocd/application.yaml` with your repo URL.
3. Apply:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app sync skillforge
argocd app get skillforge
```

## API endpoints

```text
GET  /api/health
GET  /api/roles
GET  /api/assessments?role_slug=senior-platform-engineer
GET  /api/code-challenges?role_slug=senior-platform-engineer
POST /api/code-submissions
GET  /api/leaderboard?code_challenge_id=1
GET  /api/challenges?role_slug=senior-platform-engineer
POST /api/submissions
GET  /api/interview-templates?role_slug=senior-platform-engineer
POST /api/interviews/start
POST /api/interviews/{session_id}/answers
POST /api/interviews/{session_id}/recording
POST /api/interviews/{session_id}/complete
```

## Production-like hardening checklist

- Replace the example Postgres Secret with External Secrets.
- Add TLS to ingress.
- Add OIDC/SSO authentication.
- Add NetworkPolicies for the API, Postgres, and frontend.
- Add Prometheus metrics and Grafana dashboards.
- Add Loki or OpenSearch logging.
- Add S3/MinIO backups for Postgres and recordings.
- Add image signing and admission control.
- Put the judge in a dedicated namespace.
- Add gVisor or Kata Containers for stronger sandboxing.
- Add Kyverno/OPA policies for all judge pods.
- Add per-user isolation before exposing to anyone else.

## Suggested next features

- Admin UI for creating challenges and rubrics.
- YAML-based challenge imports.
- Monaco editor.
- Speech-to-text transcription.
- Adaptive interview follow-up questions.
- Contest mode.
- Candidate progress dashboard.
- Plagiarism/similarity checks.
- Exportable PDF reports.
