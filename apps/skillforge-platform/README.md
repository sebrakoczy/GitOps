# SkillForge Platform

Kubernetes-native interview training platform for Senior Platform Engineer / Kubernetes / DevOps / DevSecOps preparation.

This MVP includes:

- React + Vite + TypeScript frontend
- FastAPI backend
- PostgreSQL persistence
- Redis-backed worker placeholder
- Static question and lab grading
- Seeded interview bank with 12 domains, 60 questions, and 8 lab challenges
- Docker Compose local runtime
- Helm chart for Kubernetes homelab deployment
- Argo CD Application manifest
- Security-first scaffold for future isolated Kubernetes Job-based grading

## Domains covered

- Kubernetes Core
- Kubernetes Troubleshooting
- Kubernetes Security
- Linux Systems
- Bash Automation
- Terraform / IaC
- Ansible
- GitOps / CI/CD
- Observability / SRE
- Platform Engineering
- Cloud / Networking
- System Design

## Quick start with Docker Compose

```bash
docker compose up --build
```

Open:

```text
http://localhost:8080
```

API health check:

```bash
curl http://localhost:8000/api/health
```

## Local API-only development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend falls back to local SQLite if `DATABASE_URL` is not set.

## Local frontend development

```bash
cd frontend
npm install
npm run dev
```

Set the API URL when needed:

```bash
export VITE_API_BASE_URL=http://localhost:8000/api
npm run dev
```

## Build production images

Replace `YOUR_GITHUB_USER` or set `REGISTRY` first.

```bash
export REGISTRY=ghcr.io/sebrakoczy
export VERSION=0.1.0

docker build -f backend/Dockerfile -t $REGISTRY/skillforge-api:$VERSION .
docker build -f frontend/Dockerfile -t $REGISTRY/skillforge-web:$VERSION .
docker build -f worker/Dockerfile -t $REGISTRY/skillforge-worker:$VERSION .

docker push $REGISTRY/skillforge-api:$VERSION
docker push $REGISTRY/skillforge-web:$VERSION
docker push $REGISTRY/skillforge-worker:$VERSION
```

## Deploy to Kubernetes with Helm

```bash
kubectl create namespace skillforge --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install skillforge ./deploy/helm/skillforge \
  --namespace skillforge \
  -f ./deploy/helm/skillforge/values-homelab-nodeport.yaml
```

Check status:

```bash
kubectl -n skillforge get pods,svc,pvc
kubectl -n skillforge logs deploy/skillforge-api
```

If you use the included NodePort override, the web service exposes port `30080`.

```bash
kubectl -n skillforge get svc skillforge-web
```

## Deploy with Argo CD

1. Push this repo to GitHub.
2. Edit `deploy/argocd/application.yaml` and replace:

```yaml
repoURL: https://github.com/YOUR_GITHUB_USER/skillforge-platform.git
```

3. Edit image repositories/tags in `deploy/helm/skillforge/values.yaml` or use your own values file.
4. Apply:

```bash
kubectl apply -f deploy/argocd/application.yaml
```

## Important security note about challenge execution

The MVP intentionally uses static grading rules and does **not** execute arbitrary user code inside the API pod.

The worker contains a scaffold for future Kubernetes Job-based isolated execution. Before enabling live code execution, harden the runner with:

- Separate namespace for grader Jobs
- Dedicated ServiceAccount with minimal RBAC
- Default-deny NetworkPolicy
- No hostPath mounts
- No privileged containers
- `runAsNonRoot`, dropped capabilities, seccomp RuntimeDefault
- CPU, memory, and wall-clock limits
- `activeDeadlineSeconds`
- `ttlSecondsAfterFinished`
- Image allowlist
- No production secrets mounted into grader pods
- Log retention and cleanup

## Project structure

```text
skillforge-platform/
├── backend/                 # FastAPI app
├── frontend/                # React/Vite app
├── worker/                  # Future isolated grading worker
├── content/                 # Seed question/lab bank
├── deploy/
│   ├── helm/skillforge/     # Kubernetes Helm chart
│   └── argocd/              # Argo CD Application
├── docs/                    # Architecture and roadmap docs
└── docker-compose.yaml
```

## Next build steps

Recommended next iterations:

1. Add local user accounts and auth.
2. Add admin CRUD UI for questions and labs.
3. Add a real queue flow from API to worker.
4. Enable isolated Kubernetes Job runner for selected trusted challenge types.
5. Add Monaco editor for coding/lab tasks.
6. Add timed interview mode.
7. Add AI mock interview mode.
8. Add Stripe/subscription support if this becomes a SaaS product.
