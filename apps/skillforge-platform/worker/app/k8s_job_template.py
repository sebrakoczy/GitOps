from __future__ import annotations

import base64
import hashlib
from typing import Any


def build_static_runner_job(namespace: str, challenge_slug: str, solution: str, image: str = "alpine:3.20") -> dict[str, Any]:
    """Build an example Kubernetes Job for future isolated grading.

    This is intentionally conservative. The MVP API currently uses static validation
    in-process. Enable real job execution only after reviewing RBAC, NetworkPolicy,
    seccomp, resource limits, cleanup, image allowlists, and secret exposure.
    """
    safe_slug = challenge_slug.replace("_", "-").replace(".", "-")[:40]
    suffix = hashlib.sha256(solution.encode()).hexdigest()[:10]
    encoded_solution = base64.b64encode(solution.encode()).decode()
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": f"skillforge-run-{safe_slug}-{suffix}",
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/name": "skillforge",
                "app.kubernetes.io/component": "grader-job",
                "skillforge.io/challenge": challenge_slug,
            },
        },
        "spec": {
            "backoffLimit": 0,
            "activeDeadlineSeconds": 30,
            "ttlSecondsAfterFinished": 300,
            "template": {
                "metadata": {
                    "labels": {
                        "app.kubernetes.io/name": "skillforge",
                        "app.kubernetes.io/component": "grader-job",
                    }
                },
                "spec": {
                    "restartPolicy": "Never",
                    "automountServiceAccountToken": False,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 10001,
                        "runAsGroup": 10001,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": "runner",
                            "image": image,
                            "imagePullPolicy": "IfNotPresent",
                            "command": ["/bin/sh", "-lc"],
                            "args": [
                                "mkdir -p /work && echo \"$SOLUTION_B64\" | base64 -d > /work/solution.txt && "
                                "wc -l /work/solution.txt && echo 'Static runner placeholder complete'"
                            ],
                            "env": [{"name": "SOLUTION_B64", "value": encoded_solution}],
                            "workingDir": "/work",
                            "resources": {
                                "requests": {"cpu": "50m", "memory": "64Mi"},
                                "limits": {"cpu": "500m", "memory": "256Mi"},
                            },
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                                "capabilities": {"drop": ["ALL"]},
                            },
                            "volumeMounts": [{"name": "work", "mountPath": "/work"}],
                        }
                    ],
                    "volumes": [{"name": "work", "emptyDir": {"sizeLimit": "16Mi"}}],
                },
            },
        },
    }
