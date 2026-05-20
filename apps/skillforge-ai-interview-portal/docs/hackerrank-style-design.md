# SkillForge HackerRank-Style Design

This version adds a HackerRank-like practice flow while keeping the homelab threat model in mind.

## Core modules

1. **Timed assessments**
   - Role-specific screens for Platform Engineering, DevSecOps, and AI Infrastructure.
   - Each assessment contains one or more coding challenges.
   - Designed to be extended with YAML challenge packs later.

2. **Coding challenge arena**
   - Challenge catalog by role track.
   - Problem statement, tags, difficulty, visible tests, hidden tests, starter code, language selector, and submission history.
   - Initial languages: Python and JavaScript.

3. **Kubernetes-isolated judge**
   - The main API does not execute submitted code directly.
   - When `ENABLE_K8S_JUDGE=true`, submissions run as short-lived Kubernetes Jobs.
   - Judge pods have no service account token, resource limits, read-only root filesystem, dropped Linux capabilities, non-root execution, RuntimeDefault seccomp, and a default-deny egress NetworkPolicy.

4. **Scenario lab**
   - Written system-design and DevOps prompts.
   - Useful for senior/principal platform interviews where design thinking matters more than pure algorithms.

5. **Mock technical interview**
   - Question flow by role.
   - Browser video recording upload.
   - Text/transcript scoring using a rule-based fallback or Ollama if configured.

## Current limitations

- This is an MVP, not a production hiring platform.
- The judge is intentionally off by default.
- Existing database/PVC installs will not automatically receive newly seeded challenges. For a fresh seed, delete the dev SQLite database or redeploy with a new Postgres volume.
- The code editor is currently a textarea. A later version should add Monaco Editor.
- No authentication or multi-user isolation yet.
- No plagiarism detection yet.
- No proctoring yet.

## Recommended next upgrades

1. Add authentication with Keycloak, Authentik, or OIDC.
2. Add an admin challenge builder.
3. Add Monaco Editor.
4. Add YAML/JSON import for challenge packs.
5. Split the judge into a separate microservice and namespace.
6. Add Kyverno policies for judge pods.
7. Add Prometheus metrics and Grafana dashboards.
8. Add Loki logs for submission debugging.
9. Add MinIO/S3 for recording and report storage.
10. Add Argo CD app-of-apps for platform deployment.
