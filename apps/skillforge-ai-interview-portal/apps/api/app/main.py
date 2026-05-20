from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except Exception:  # Local dev can run without the Kubernetes package/config.
    client = None
    config = None
    ApiException = Exception

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/skillforge.db")
RECORDING_DIR = Path(os.getenv("RECORDING_DIR", "/data/recordings"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
APP_ENV = os.getenv("APP_ENV", "dev")
ENABLE_K8S_JUDGE = os.getenv("ENABLE_K8S_JUDGE", "false").lower() == "true"
JUDGE_NAMESPACE = os.getenv("JUDGE_NAMESPACE", os.getenv("POD_NAMESPACE", "skillforge"))
JUDGE_TIMEOUT_SECONDS = int(os.getenv("JUDGE_TIMEOUT_SECONDS", "20"))

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

app = FastAPI(
    title="SkillForge AI Interview Portal",
    version="0.2.0",
    description="Homelab-ready HackerRank-style challenge arena plus AI/video mock technical interviews.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    title: str
    description: str
    focus_areas_json: str = "[]"


class Challenge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role_slug: str = Field(index=True)
    title: str
    difficulty: str
    category: str
    prompt: str
    expected_keywords_json: str = "[]"
    rubric_json: str = "{}"
    starter_code: str = ""


class CodeChallenge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role_slug: str = Field(index=True)
    slug: str = Field(index=True, unique=True)
    title: str
    difficulty: str
    category: str
    prompt_md: str
    function_name: str
    languages_json: str = '["python"]'
    starter_code_json: str = "{}"
    visible_tests_json: str = "[]"
    hidden_tests_json: str = "[]"
    tags_json: str = "[]"
    hints_json: str = "[]"
    points: int = 100
    time_limit_seconds: int = 5
    memory_limit_mb: int = 128


class Assessment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role_slug: str = Field(index=True)
    title: str
    description: str
    duration_minutes: int = 60
    challenge_ids_json: str = "[]"
    instructions_json: str = "[]"


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: int = Field(index=True)
    candidate_name: str = "Sebastian"
    answer: str
    score: int = 0
    feedback_json: str = "{}"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CodeSubmission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code_challenge_id: int = Field(index=True)
    candidate_name: str = "Sebastian"
    language: str = "python"
    source_code: str
    status: str = "created"
    score: int = 0
    passed: int = 0
    total: int = 0
    results_json: str = "[]"
    judge_mode: str = "disabled"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InterviewTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role_slug: str = Field(index=True)
    name: str
    mode: str  # technical, behavioral, system-design, video
    duration_minutes: int = 30
    questions_json: str = "[]"
    rubric_json: str = "{}"


class InterviewSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    template_id: int = Field(index=True)
    candidate_name: str = "Sebastian"
    status: str = "in_progress"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    report_json: str = "{}"


class InterviewAnswer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    question_index: int
    question: str
    answer_text: str = ""
    recording_path: str = ""
    score: int = 0
    feedback_json: str = "{}"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubmissionIn(BaseModel):
    challenge_id: int
    candidate_name: str = "Sebastian"
    answer: str


class CodeSubmissionIn(BaseModel):
    code_challenge_id: int
    candidate_name: str = "Sebastian"
    language: str = "python"
    source_code: str
    include_hidden: bool = True


class InterviewStartIn(BaseModel):
    template_id: int
    candidate_name: str = "Sebastian"


class InterviewAnswerIn(BaseModel):
    question_index: int
    question: str
    answer_text: str = ""


class SessionCompleteIn(BaseModel):
    finalize: bool = True


def as_json(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return fallback


def challenge_out(c: CodeChallenge, include_hidden: bool = False) -> dict[str, Any]:
    data = c.model_dump() | {
        "languages": as_json(c.languages_json, []),
        "starter_code": as_json(c.starter_code_json, {}),
        "visible_tests": as_json(c.visible_tests_json, []),
        "tags": as_json(c.tags_json, []),
        "hints": as_json(c.hints_json, []),
    }
    if include_hidden:
        data["hidden_tests"] = as_json(c.hidden_tests_json, [])
    return data


def keyword_score(answer: str, expected_keywords: list[str]) -> dict[str, Any]:
    answer_l = answer.lower()
    hits = [kw for kw in expected_keywords if kw.lower() in answer_l]
    missing = [kw for kw in expected_keywords if kw.lower() not in answer_l]
    base = round((len(hits) / max(len(expected_keywords), 1)) * 100)
    length_bonus = 10 if len(answer.split()) >= 80 else 0
    score = min(100, base + length_bonus)
    return {
        "score": score,
        "hits": hits,
        "missing": missing,
        "summary": "Good structure and coverage." if score >= 75 else "Needs deeper coverage of the rubric items.",
        "recommendations": [
            "State assumptions up front.",
            "Explain trade-offs, failure modes, and security controls.",
            "Close with how you would validate the solution in production.",
        ],
    }


async def ollama_feedback(prompt: str) -> Optional[dict[str, Any]]:
    if not OLLAMA_BASE_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=45) as client_http:
            resp = await client_http.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "{}")
            return json.loads(raw)
    except Exception as exc:
        return {"score": 0, "summary": f"LLM feedback unavailable: {exc}", "recommendations": []}


def visible_static_result(challenge: CodeChallenge, reason: str) -> dict[str, Any]:
    visible = as_json(challenge.visible_tests_json, [])
    results = [
        {
            "name": test.get("name", f"test-{i+1}"),
            "visible": True,
            "passed": False,
            "input": test.get("input"),
            "expected": test.get("expected"),
            "actual": None,
            "error": reason,
        }
        for i, test in enumerate(visible)
    ]
    return {
        "status": "judge_disabled",
        "score": 0,
        "passed": 0,
        "total": len(visible),
        "results": results,
        "judge_mode": "static-disabled",
    }


def make_python_harness(function_name: str) -> str:
    return r'''
import base64, json, resource, signal, sys, traceback
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (160 * 1024 * 1024, 160 * 1024 * 1024))
signal.alarm(8)
source = base64.b64decode(sys.argv[1]).decode("utf-8", "replace")
tests = json.loads(base64.b64decode(sys.argv[2]).decode("utf-8"))
function_name = sys.argv[3]
results = []
try:
    ns = {"__builtins__": __builtins__}
    exec(source, ns, ns)
    fn = ns.get(function_name)
    if not callable(fn):
        raise RuntimeError(f"Function {function_name} was not found or is not callable")
    for t in tests:
        try:
            args = t.get("input", [])
            if not isinstance(args, list):
                args = [args]
            actual = fn(*args)
            expected = t.get("expected")
            passed = actual == expected
            results.append({"name": t.get("name", "test"), "visible": bool(t.get("visible", False)), "passed": passed, "input": t.get("input"), "expected": expected, "actual": actual, "error": None})
        except Exception as exc:
            results.append({"name": t.get("name", "test"), "visible": bool(t.get("visible", False)), "passed": False, "input": t.get("input"), "expected": t.get("expected"), "actual": None, "error": str(exc)})
except Exception as exc:
    results.append({"name": "compile-or-load", "visible": True, "passed": False, "input": None, "expected": None, "actual": None, "error": str(exc), "traceback": traceback.format_exc(limit=2)})
print(json.dumps({"results": results}))
'''.strip()


def make_javascript_harness(function_name: str) -> str:
    return r'''
const source = Buffer.from(process.argv[1], 'base64').toString('utf8');
const tests = JSON.parse(Buffer.from(process.argv[2], 'base64').toString('utf8'));
const functionName = process.argv[3];
const results = [];
try {
  const wrapped = new Function(`${source}; return typeof ${functionName} !== 'undefined' ? ${functionName} : undefined;`);
  const fn = wrapped();
  if (typeof fn !== 'function') throw new Error(`Function ${functionName} was not found`);
  for (const t of tests) {
    try {
      const args = Array.isArray(t.input) ? t.input : [t.input];
      const actual = fn(...args);
      const expected = t.expected;
      const passed = JSON.stringify(actual) === JSON.stringify(expected);
      results.push({name: t.name || 'test', visible: !!t.visible, passed, input: t.input, expected, actual, error: null});
    } catch (err) {
      results.push({name: t.name || 'test', visible: !!t.visible, passed: false, input: t.input, expected: t.expected, actual: null, error: String(err.message || err)});
    }
  }
} catch (err) {
  results.push({name: 'compile-or-load', visible: true, passed: false, input: null, expected: null, actual: null, error: String(err.message || err)});
}
console.log(JSON.stringify({results}));
'''.strip()


def k8s_available() -> bool:
    return ENABLE_K8S_JUDGE and client is not None and config is not None


def load_k8s_config_once() -> None:
    if not k8s_available():
        raise RuntimeError("Kubernetes judge is disabled. Set ENABLE_K8S_JUDGE=true and run inside Kubernetes.")
    try:
        config.load_incluster_config()
    except Exception:
        config.load_kube_config()


def run_k8s_judge(challenge: CodeChallenge, language: str, source_code: str, include_hidden: bool) -> dict[str, Any]:
    if language not in as_json(challenge.languages_json, ["python"]):
        raise HTTPException(status_code=400, detail=f"Language {language} is not enabled for this challenge")
    load_k8s_config_once()
    batch = client.BatchV1Api()
    core = client.CoreV1Api()
    all_tests = []
    for test in as_json(challenge.visible_tests_json, []):
        test = dict(test)
        test["visible"] = True
        all_tests.append(test)
    if include_hidden:
        for test in as_json(challenge.hidden_tests_json, []):
            test = dict(test)
            test["visible"] = False
            all_tests.append(test)

    source_b64 = base64.b64encode(source_code.encode()).decode()
    tests_b64 = base64.b64encode(json.dumps(all_tests).encode()).decode()
    job_name = f"sf-judge-{uuid.uuid4().hex[:12]}"

    if language == "python":
        image = "python:3.12-alpine"
        harness = make_python_harness(challenge.function_name)
        command = ["python", "-c", harness, source_b64, tests_b64, challenge.function_name]
    elif language in {"javascript", "node"}:
        image = "node:22-alpine"
        harness = make_javascript_harness(challenge.function_name)
        command = ["node", "-e", harness, source_b64, tests_b64, challenge.function_name]
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    job = client.V1Job(
        metadata=client.V1ObjectMeta(name=job_name, labels={"app.kubernetes.io/name": "skillforge-judge", "skillforge/job": job_name}),
        spec=client.V1JobSpec(
            ttl_seconds_after_finished=120,
            backoff_limit=0,
            active_deadline_seconds=challenge.time_limit_seconds + 10,
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app.kubernetes.io/name": "skillforge-judge", "skillforge/job": job_name}),
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    automount_service_account_token=False,
                    security_context=client.V1PodSecurityContext(run_as_non_root=True, run_as_user=1000, run_as_group=1000, seccomp_profile=client.V1SeccompProfile(type="RuntimeDefault")),
                    containers=[client.V1Container(
                        name="runner",
                        image=image,
                        command=command,
                        resources=client.V1ResourceRequirements(
                            requests={"cpu": "50m", "memory": "64Mi"},
                            limits={"cpu": "500m", "memory": f"{challenge.memory_limit_mb}Mi"},
                        ),
                        security_context=client.V1SecurityContext(
                            allow_privilege_escalation=False,
                            read_only_root_filesystem=True,
                            capabilities=client.V1Capabilities(drop=["ALL"]),
                        ),
                    )],
                ),
            ),
        ),
    )
    try:
        batch.create_namespaced_job(namespace=JUDGE_NAMESPACE, body=job)
        deadline = time.time() + min(JUDGE_TIMEOUT_SECONDS, challenge.time_limit_seconds + 15)
        pod_name = None
        while time.time() < deadline:
            pods = core.list_namespaced_pod(namespace=JUDGE_NAMESPACE, label_selector=f"skillforge/job={job_name}").items
            if pods:
                pod_name = pods[0].metadata.name
                phase = pods[0].status.phase
                if phase in {"Succeeded", "Failed"}:
                    break
            time.sleep(0.5)
        if not pod_name:
            return {"status": "infra_error", "score": 0, "passed": 0, "total": len(all_tests), "results": [{"name": "judge", "passed": False, "visible": True, "error": "Judge pod did not start"}], "judge_mode": "k8s-job"}
        logs = core.read_namespaced_pod_log(namespace=JUDGE_NAMESPACE, name=pod_name, container="runner", tail_lines=50)
        parsed = json.loads(logs.strip().splitlines()[-1])
        results = parsed.get("results", [])
        passed = sum(1 for r in results if r.get("passed"))
        total = len(results)
        score = round((passed / max(total, 1)) * challenge.points)
        # Hide hidden test inputs/expected/actual values, but reveal pass/fail.
        safe_results = []
        for r in results:
            if not r.get("visible"):
                safe_results.append({"name": r.get("name", "hidden"), "visible": False, "passed": r.get("passed", False), "error": r.get("error")})
            else:
                safe_results.append(r)
        return {"status": "passed" if passed == total else "failed", "score": score, "passed": passed, "total": total, "results": safe_results, "judge_mode": "k8s-job"}
    except ApiException as exc:
        return {"status": "infra_error", "score": 0, "passed": 0, "total": len(all_tests), "results": [{"name": "kubernetes-api", "visible": True, "passed": False, "error": str(exc)}], "judge_mode": "k8s-job"}
    except Exception as exc:
        return {"status": "infra_error", "score": 0, "passed": 0, "total": len(all_tests), "results": [{"name": "judge", "visible": True, "passed": False, "error": str(exc)}], "judge_mode": "k8s-job"}
    finally:
        try:
            batch.delete_namespaced_job(namespace=JUDGE_NAMESPACE, name=job_name, propagation_policy="Background")
        except Exception:
            pass


def seed_data() -> None:
    with Session(engine) as session:
        if session.exec(select(Role)).first():
            # Existing installs keep their data. Delete the DB/PVC to reseed all examples.
            return
        roles = [
            Role(
                slug="senior-platform-engineer",
                title="Senior Platform / Kubernetes Engineer",
                description="Production-grade Kubernetes, GitOps, Terraform, cloud security, observability, and reliability.",
                focus_areas_json=json.dumps(["Kubernetes architecture", "Terraform and immutable infrastructure", "GitOps with Argo CD", "Cloud/container security", "Observability and incident response"]),
            ),
            Role(
                slug="devsecops-engineer",
                title="DevSecOps Engineer",
                description="Secure CI/CD, supply-chain security, threat modeling, policy-as-code, and cloud hardening.",
                focus_areas_json=json.dumps(["OWASP and threat modeling", "CI/CD hardening", "SAST/DAST/SBOM", "Kubernetes security", "Cloud IAM and network controls"]),
            ),
            Role(
                slug="ai-infra-engineer",
                title="AI Infrastructure Engineer",
                description="GPU-aware Kubernetes, model serving, MLOps, vector stores, observability, and inference reliability.",
                focus_areas_json=json.dumps(["GPU scheduling", "Model serving", "MLOps pipelines", "Cost/performance tuning", "AI security"]),
            ),
        ]
        session.add_all(roles)

        challenges = [
            Challenge(
                role_slug="senior-platform-engineer",
                title="Design a Production Bare-Metal Kubernetes Platform",
                difficulty="Hard",
                category="System Design",
                prompt="Design a production-grade bare-metal Kubernetes platform for a regulated company. Include HA control plane, etcd backup/restore, ingress, storage, GitOps, monitoring, secret management, and disaster recovery.",
                expected_keywords_json=json.dumps(["etcd", "backup", "restore", "Argo CD", "ingress", "Longhorn", "Prometheus", "Alertmanager", "NetworkPolicy", "RBAC", "secrets", "S3"]),
                rubric_json=json.dumps({"architecture": 30, "reliability_dr": 25, "security": 25, "operability": 20}),
            ),
            Challenge(
                role_slug="senior-platform-engineer",
                title="Terraform Multi-Environment Module Review",
                difficulty="Medium",
                category="Terraform",
                prompt="Review a Terraform module that deploys an ALB, target groups, listener rules, and ECS services across L1, L3, and L4. Explain how you would structure variables, remote state, provider versions, and safe environment selection.",
                expected_keywords_json=json.dumps(["required_providers", "remote state", "DynamoDB locking", "map", "validation", "workspaces", "module", "outputs", "plan", "state"]),
                rubric_json=json.dumps({"correctness": 30, "upgrade_safety": 25, "environment_design": 25, "security": 20}),
            ),
            Challenge(
                role_slug="devsecops-engineer",
                title="Secure a CI/CD Pipeline for Container Delivery",
                difficulty="Hard",
                category="DevSecOps",
                prompt="Design a secure CI/CD pipeline that builds, tests, scans, signs, and deploys container images to Kubernetes using GitOps. Include controls for secrets, SBOM, provenance, image hardening, and policy gates.",
                expected_keywords_json=json.dumps(["SBOM", "SLSA", "cosign", "Trivy", "OPA", "Kyverno", "least privilege", "secrets", "Argo CD", "admission control", "immutable"]),
                rubric_json=json.dumps({"pipeline": 25, "supply_chain": 30, "k8s_security": 25, "operations": 20}),
            ),
            Challenge(
                role_slug="ai-infra-engineer",
                title="Run AI Workloads on Homelab Kubernetes",
                difficulty="Medium",
                category="AI Infrastructure",
                prompt="Explain how you would run small AI workloads on Kubernetes using a mix of NVIDIA, AMD, and Apple Silicon resources. Cover scheduling, drivers, model serving, storage, and practical limitations.",
                expected_keywords_json=json.dumps(["NVIDIA device plugin", "ROCm", "Metal", "Ollama", "node labels", "taints", "model serving", "PVC", "GPU operator", "monitoring"]),
                rubric_json=json.dumps({"hardware_fit": 25, "k8s_scheduling": 25, "serving": 25, "limitations": 25}),
            ),
        ]
        session.add_all(challenges)

        code_challenges = [
            CodeChallenge(
                role_slug="senior-platform-engineer",
                slug="parse-k8s-cpu",
                title="Parse Kubernetes CPU Quantities",
                difficulty="Easy",
                category="Kubernetes Scripting",
                prompt_md="Write `parse_cpu(value)` that converts Kubernetes CPU quantities to millicores. Examples: `500m -> 500`, `1 -> 1000`, `2.5 -> 2500`. Return an integer.",
                function_name="parse_cpu",
                languages_json=json.dumps(["python", "javascript"]),
                starter_code_json=json.dumps({
                    "python": "def parse_cpu(value):\n    # value is a string like '500m', '1', or '2.5'\n    pass\n",
                    "javascript": "function parse_cpu(value) {\n  // value is a string like '500m', '1', or '2.5'\n}\n",
                }),
                visible_tests_json=json.dumps([
                    {"name": "millicores", "input": ["500m"], "expected": 500},
                    {"name": "one-core", "input": ["1"], "expected": 1000},
                ]),
                hidden_tests_json=json.dumps([
                    {"name": "decimal-core", "input": ["2.5"], "expected": 2500},
                    {"name": "zero-milli", "input": ["0m"], "expected": 0},
                ]),
                tags_json=json.dumps(["kubernetes", "python", "parsing", "sre"]),
                hints_json=json.dumps(["A value ending in m is already millicores.", "A value without m represents CPU cores."]),
                points=100,
            ),
            CodeChallenge(
                role_slug="senior-platform-engineer",
                slug="terraform-env-key",
                title="Safe Terraform Environment Key",
                difficulty="Medium",
                category="Terraform Logic",
                prompt_md="Write `env_key(env)` that safely returns the first two uppercase characters from an environment name. It must reject values shorter than two characters by returning `None`/`null`. Examples: `L3-17 -> L3`, `l4-prod -> L4`.",
                function_name="env_key",
                languages_json=json.dumps(["python", "javascript"]),
                starter_code_json=json.dumps({
                    "python": "def env_key(env):\n    # Return an uppercase two-character key or None\n    pass\n",
                    "javascript": "function env_key(env) {\n  // Return an uppercase two-character key or null\n}\n",
                }),
                visible_tests_json=json.dumps([
                    {"name": "l3-numbered", "input": ["L3-17"], "expected": "L3"},
                    {"name": "lowercase-prod", "input": ["l4-prod"], "expected": "L4"},
                ]),
                hidden_tests_json=json.dumps([
                    {"name": "too-short", "input": ["L"], "expected": None},
                    {"name": "empty", "input": [""], "expected": None},
                ]),
                tags_json=json.dumps(["terraform", "validation", "string-handling"]),
                hints_json=json.dumps(["Avoid substr/slice errors on short values.", "Normalize to uppercase after checking length."]),
                points=100,
            ),
            CodeChallenge(
                role_slug="devsecops-engineer",
                slug="detect-dangerous-dockerfile",
                title="Detect Dangerous Dockerfile Patterns",
                difficulty="Medium",
                category="Container Security",
                prompt_md="Write `dockerfile_findings(lines)` that accepts a list of Dockerfile lines and returns a sorted list of findings. Detect: `latest-tag` when a FROM line uses `:latest`, `root-user` when `USER root` appears, and `curl-bash` when a line pipes curl or wget to sh/bash.",
                function_name="dockerfile_findings",
                languages_json=json.dumps(["python", "javascript"]),
                starter_code_json=json.dumps({
                    "python": "def dockerfile_findings(lines):\n    findings = []\n    # return a sorted list like ['curl-bash', 'latest-tag']\n    return findings\n",
                    "javascript": "function dockerfile_findings(lines) {\n  const findings = [];\n  // return a sorted array like ['curl-bash', 'latest-tag']\n  return findings;\n}\n",
                }),
                visible_tests_json=json.dumps([
                    {"name": "latest", "input": [["FROM node:latest", "USER app"]], "expected": ["latest-tag"]},
                    {"name": "root", "input": [["FROM alpine:3.20", "USER root"]], "expected": ["root-user"]},
                ]),
                hidden_tests_json=json.dumps([
                    {"name": "curlbash", "input": [["RUN curl https://example/install.sh | bash"]], "expected": ["curl-bash"]},
                    {"name": "combined", "input": [["FROM ubuntu:latest", "RUN wget -qO- https://x | sh", "USER root"]], "expected": ["curl-bash", "latest-tag", "root-user"]},
                ]),
                tags_json=json.dumps(["docker", "devsecops", "policy-as-code"]),
                hints_json=json.dumps(["Case-insensitive matching helps.", "Sort the final findings for deterministic output."]),
                points=100,
            ),
            CodeChallenge(
                role_slug="ai-infra-engineer",
                slug="gpu-node-selector",
                title="Choose GPU Node Selector",
                difficulty="Easy",
                category="AI Infrastructure",
                prompt_md="Write `gpu_node_selector(vendor)` that returns a Kubernetes node selector dictionary/object for `nvidia`, `amd`, or `apple`. Use keys: `accelerator=nvidia`, `accelerator=amd`, `accelerator=apple-silicon`. Return empty object for unknown vendors.",
                function_name="gpu_node_selector",
                languages_json=json.dumps(["python", "javascript"]),
                starter_code_json=json.dumps({
                    "python": "def gpu_node_selector(vendor):\n    # Return a dict for nodeSelector\n    pass\n",
                    "javascript": "function gpu_node_selector(vendor) {\n  // Return an object for nodeSelector\n}\n",
                }),
                visible_tests_json=json.dumps([
                    {"name": "nvidia", "input": ["nvidia"], "expected": {"accelerator": "nvidia"}},
                    {"name": "amd", "input": ["AMD"], "expected": {"accelerator": "amd"}},
                ]),
                hidden_tests_json=json.dumps([
                    {"name": "apple", "input": ["apple"], "expected": {"accelerator": "apple-silicon"}},
                    {"name": "unknown", "input": ["cpu"], "expected": {}},
                ]),
                tags_json=json.dumps(["gpu", "kubernetes", "ai-infra"]),
                hints_json=json.dumps(["Normalize the vendor string.", "Unknown vendors should not force scheduling."]),
                points=100,
            ),
        ]
        session.add_all(code_challenges)
        session.commit()
        ids = {c.slug: c.id for c in session.exec(select(CodeChallenge)).all()}
        session.add_all([
            Assessment(
                role_slug="senior-platform-engineer",
                title="Platform Engineer Timed Screen",
                description="HackerRank-style assessment with Kubernetes scripting and Terraform safety logic.",
                duration_minutes=45,
                challenge_ids_json=json.dumps([ids["parse-k8s-cpu"], ids["terraform-env-key"]]),
                instructions_json=json.dumps(["Solve each function using the selected language.", "Visible tests are shown; hidden tests affect the final score.", "Explain trade-offs in the system-design area after the coding round."]),
            ),
            Assessment(
                role_slug="devsecops-engineer",
                title="DevSecOps Coding + Policy Screen",
                description="Detect risky container patterns and then explain how you would enforce the control in CI/CD.",
                duration_minutes=35,
                challenge_ids_json=json.dumps([ids["detect-dangerous-dockerfile"]]),
                instructions_json=json.dumps(["Return deterministic results.", "Use this as practice for policy-as-code thinking."]),
            ),
            Assessment(
                role_slug="ai-infra-engineer",
                title="AI Infra Practical Screen",
                description="Practice Kubernetes scheduling logic for heterogeneous AI hardware.",
                duration_minutes=30,
                challenge_ids_json=json.dumps([ids["gpu-node-selector"]]),
                instructions_json=json.dumps(["Keep logic simple and explicit.", "Use labels that match your homelab node-labeling strategy."]),
            ),
        ])

        templates = [
            InterviewTemplate(
                role_slug="senior-platform-engineer",
                name="Platform Engineer AI Mock Interview",
                mode="technical-video",
                duration_minutes=35,
                questions_json=json.dumps(["Walk me through your production Kubernetes architecture and why you chose it.", "How do you restore an etcd snapshot after a control-plane failure?", "How would you migrate a legacy Terraform 0.11 module to Terraform 1.x safely?", "What security controls would you enforce before allowing workloads into production?", "Describe an incident where observability changed how you debugged a system."]),
                rubric_json=json.dumps({"depth": 30, "structure": 20, "accuracy": 25, "communication": 25}),
            ),
            InterviewTemplate(
                role_slug="devsecops-engineer",
                name="DevSecOps Technical Screen",
                mode="technical-video",
                duration_minutes=30,
                questions_json=json.dumps(["Design a secure container supply-chain pipeline from commit to Kubernetes deployment.", "How would you threat model a public API deployed behind an ingress controller?", "What would you block with admission control in a regulated Kubernetes platform?", "Explain how you would handle secrets without committing them to Git."]),
                rubric_json=json.dumps({"security_depth": 35, "practicality": 25, "tooling": 20, "communication": 20}),
            ),
            InterviewTemplate(
                role_slug="ai-infra-engineer",
                name="AI Infrastructure Mock Interview",
                mode="technical-video",
                duration_minutes=30,
                questions_json=json.dumps(["How do GPUs get exposed and scheduled in Kubernetes?", "How would you serve an LLM internally for developer productivity?", "Compare NVIDIA CUDA, AMD ROCm, and Apple Metal for homelab AI workloads.", "How do you monitor inference latency, GPU utilization, and model failures?"]),
                rubric_json=json.dumps({"ai_infra": 30, "k8s": 25, "tradeoffs": 25, "communication": 20}),
            ),
        ]
        session.add_all(templates)
        session.commit()


@app.on_event("startup")
def on_startup() -> None:
    RECORDING_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    seed_data()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "env": APP_ENV,
        "llm_enabled": bool(OLLAMA_BASE_URL),
        "k8s_judge_enabled": ENABLE_K8S_JUDGE,
        "judge_namespace": JUDGE_NAMESPACE,
    }


@app.get("/api/roles")
def get_roles() -> list[dict[str, Any]]:
    with Session(engine) as session:
        roles = session.exec(select(Role)).all()
        return [r.model_dump() | {"focus_areas": as_json(r.focus_areas_json, [])} for r in roles]


@app.get("/api/challenges")
def get_challenges(role_slug: Optional[str] = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        query = select(Challenge)
        if role_slug:
            query = query.where(Challenge.role_slug == role_slug)
        rows = session.exec(query).all()
        return [c.model_dump() | {"expected_keywords": as_json(c.expected_keywords_json, []), "rubric": as_json(c.rubric_json, {})} for c in rows]


@app.get("/api/code-challenges")
def get_code_challenges(role_slug: Optional[str] = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        query = select(CodeChallenge)
        if role_slug:
            query = query.where(CodeChallenge.role_slug == role_slug)
        rows = session.exec(query).all()
        return [challenge_out(c) for c in rows]


@app.get("/api/assessments")
def get_assessments(role_slug: Optional[str] = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        query = select(Assessment)
        if role_slug:
            query = query.where(Assessment.role_slug == role_slug)
        rows = session.exec(query).all()
        output = []
        for a in rows:
            ids = as_json(a.challenge_ids_json, [])
            challenges = []
            for cid in ids:
                challenge = session.get(CodeChallenge, cid)
                if challenge:
                    challenges.append(challenge_out(challenge))
            output.append(a.model_dump() | {"challenge_ids": ids, "instructions": as_json(a.instructions_json, []), "challenges": challenges})
        return output


@app.get("/api/leaderboard")
def get_leaderboard(code_challenge_id: Optional[int] = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        query = select(CodeSubmission)
        if code_challenge_id:
            query = query.where(CodeSubmission.code_challenge_id == code_challenge_id)
        rows = session.exec(query).all()
        rows = sorted(rows, key=lambda r: (r.score, r.created_at), reverse=True)[:20]
        return [r.model_dump() | {"results": as_json(r.results_json, [])} for r in rows]


@app.post("/api/submissions")
async def create_submission(payload: SubmissionIn) -> dict[str, Any]:
    with Session(engine) as session:
        challenge = session.get(Challenge, payload.challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        expected = as_json(challenge.expected_keywords_json, [])
        fallback = keyword_score(payload.answer, expected)
        llm = await ollama_feedback("You are a senior technical interviewer. Score this answer as JSON with keys score, summary, strengths, gaps, recommendations. " f"Challenge: {challenge.prompt}\nRubric: {challenge.rubric_json}\nAnswer: {payload.answer}")
        feedback = llm if llm and llm.get("score", 0) else fallback
        score = int(feedback.get("score", fallback["score"]))
        sub = Submission(challenge_id=payload.challenge_id, candidate_name=payload.candidate_name, answer=payload.answer, score=max(0, min(100, score)), feedback_json=json.dumps(feedback))
        session.add(sub)
        session.commit()
        session.refresh(sub)
        return sub.model_dump() | {"feedback": feedback}


@app.post("/api/code-submissions")
def create_code_submission(payload: CodeSubmissionIn) -> dict[str, Any]:
    with Session(engine) as session:
        challenge = session.get(CodeChallenge, payload.code_challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Code challenge not found")
        if ENABLE_K8S_JUDGE:
            result = run_k8s_judge(challenge, payload.language, payload.source_code, payload.include_hidden)
        else:
            result = visible_static_result(challenge, "Kubernetes judge is disabled. Enable ENABLE_K8S_JUDGE=true after applying judge RBAC and NetworkPolicy.")
        sub = CodeSubmission(
            code_challenge_id=payload.code_challenge_id,
            candidate_name=payload.candidate_name,
            language=payload.language,
            source_code=payload.source_code,
            status=result["status"],
            score=int(result.get("score", 0)),
            passed=int(result.get("passed", 0)),
            total=int(result.get("total", 0)),
            results_json=json.dumps(result.get("results", [])),
            judge_mode=result.get("judge_mode", "unknown"),
        )
        session.add(sub)
        session.commit()
        session.refresh(sub)
        return sub.model_dump() | {"results": result.get("results", []), "challenge": challenge_out(challenge)}


@app.get("/api/interview-templates")
def get_interview_templates(role_slug: Optional[str] = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        query = select(InterviewTemplate)
        if role_slug:
            query = query.where(InterviewTemplate.role_slug == role_slug)
        rows = session.exec(query).all()
        return [t.model_dump() | {"questions": as_json(t.questions_json, []), "rubric": as_json(t.rubric_json, {})} for t in rows]


@app.post("/api/interviews/start")
def start_interview(payload: InterviewStartIn) -> dict[str, Any]:
    with Session(engine) as session:
        template = session.get(InterviewTemplate, payload.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        interview = InterviewSession(template_id=payload.template_id, candidate_name=payload.candidate_name)
        session.add(interview)
        session.commit()
        session.refresh(interview)
        return interview.model_dump() | {"template": template.model_dump(), "questions": as_json(template.questions_json, [])}


@app.post("/api/interviews/{session_id}/answers")
async def add_interview_answer(session_id: str, payload: InterviewAnswerIn) -> dict[str, Any]:
    with Session(engine) as session:
        interview = session.get(InterviewSession, session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview session not found")
        template = session.get(InterviewTemplate, interview.template_id)
        rubric = as_json(template.rubric_json, {}) if template else {}
        expected = list(rubric.keys()) + ["architecture", "tradeoff", "security", "observability", "reliability", "example"]
        fallback = keyword_score(payload.answer_text, expected)
        llm = await ollama_feedback("You are an AI interviewer. Evaluate this spoken technical interview answer. Return JSON with score, summary, strengths, gaps, recommendations. " f"Question: {payload.question}\nRubric: {rubric}\nAnswer transcript/text: {payload.answer_text}")
        feedback = llm if llm and llm.get("score", 0) else fallback
        answer = InterviewAnswer(session_id=session_id, question_index=payload.question_index, question=payload.question, answer_text=payload.answer_text, score=int(feedback.get("score", fallback["score"])), feedback_json=json.dumps(feedback))
        session.add(answer)
        session.commit()
        session.refresh(answer)
        return answer.model_dump() | {"feedback": feedback}


@app.post("/api/interviews/{session_id}/recording")
async def upload_recording(session_id: str, question_index: int, file: UploadFile = File(...)) -> dict[str, str]:
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", file.filename or "answer.webm")
    filename = f"{session_id}-q{question_index}-{uuid.uuid4().hex}-{safe_name}"
    destination = RECORDING_DIR / filename
    with destination.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)
    return {"recording_path": str(destination), "filename": filename}


@app.post("/api/interviews/{session_id}/complete")
def complete_interview(session_id: str, payload: SessionCompleteIn) -> dict[str, Any]:
    with Session(engine) as session:
        interview = session.get(InterviewSession, session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview session not found")
        answers = session.exec(select(InterviewAnswer).where(InterviewAnswer.session_id == session_id)).all()
        avg = round(sum(a.score for a in answers) / max(len(answers), 1))
        report = {
            "overall_score": avg,
            "questions_answered": len(answers),
            "summary": "Strong mock interview performance." if avg >= 75 else "Good practice session; focus on structured answers and deeper examples.",
            "recommendations": ["Use STAR or Situation → Action → Result for experience questions.", "For technical answers, state assumptions, trade-offs, failure modes, and security controls.", "Close each answer with measurable business impact or operational outcome."],
        }
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc)
        interview.report_json = json.dumps(report)
        session.add(interview)
        session.commit()
        return interview.model_dump() | {"report": report}


@app.get("/api/interviews/{session_id}/report")
def get_interview_report(session_id: str) -> dict[str, Any]:
    with Session(engine) as session:
        interview = session.get(InterviewSession, session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview session not found")
        answers = session.exec(select(InterviewAnswer).where(InterviewAnswer.session_id == session_id)).all()
        return {"session": interview.model_dump(), "report": as_json(interview.report_json, {}), "answers": [a.model_dump() | {"feedback": as_json(a.feedback_json, {})} for a in answers]}
