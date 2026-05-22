import re
from typing import Any


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    if isinstance(value, list):
        return sorted([normalize(v) for v in value])
    return value


def grade_question(question_type: str, correct_answer: Any, answer: Any, explanation: str = "") -> tuple[int, bool, str]:
    if question_type in {"multiple_choice", "true_false"}:
        passed = normalize(answer) == normalize(correct_answer)
        return (100 if passed else 0, passed, explanation if passed else f"Not quite. {explanation}")

    if question_type == "multi_select":
        expected = set(normalize(correct_answer or []))
        received = set(normalize(answer or []))
        passed = expected == received
        score = int((len(expected.intersection(received)) / max(len(expected), 1)) * 100)
        if received - expected:
            score = max(0, score - 20)
        return (100 if passed else score, passed, explanation if passed else f"Expected {sorted(expected)}. {explanation}")

    if question_type in {"short_answer", "scenario"}:
        text = normalize(answer or "")
        expected = correct_answer or {}
        keywords = expected.get("keywords", []) if isinstance(expected, dict) else []
        required = [normalize(k) for k in keywords]
        hits = [k for k in required if k in text]
        score = int((len(hits) / max(len(required), 1)) * 100)
        passed = score >= 80
        missing = [k for k in required if k not in hits]
        feedback = explanation if passed else f"Missing key ideas: {', '.join(missing)}. {explanation}"
        return score, passed, feedback

    return 0, False, "Unsupported question type."


def grade_challenge(test_rules: list[dict[str, Any]] | None, solution: str) -> dict[str, Any]:
    rules = test_rules or []
    results = []
    for rule in rules:
        rule_type = rule.get("type")
        name = rule.get("name", rule_type or "rule")
        passed = False
        details = ""
        if rule_type == "contains":
            value = str(rule.get("value", ""))
            passed = value in solution
            details = f"Expected solution to contain: {value}"
        elif rule_type == "not_contains":
            value = str(rule.get("value", ""))
            passed = value not in solution
            details = f"Expected solution not to contain: {value}"
        elif rule_type == "regex":
            pattern = str(rule.get("pattern", ""))
            passed = re.search(pattern, solution, re.MULTILINE | re.DOTALL) is not None
            details = f"Expected regex match: {pattern}"
        elif rule_type == "line_count_min":
            minimum = int(rule.get("value", 1))
            passed = len([l for l in solution.splitlines() if l.strip()]) >= minimum
            details = f"Expected at least {minimum} non-empty lines"
        else:
            details = f"Unknown rule type: {rule_type}"
        results.append({"name": name, "passed": passed, "details": details})

    passed_count = sum(1 for item in results if item["passed"])
    score = int((passed_count / max(len(results), 1)) * 100)
    return {
        "score": score,
        "passed": bool(results) and score == 100,
        "checks": results,
        "mode": "static_rules",
        "note": "MVP grader uses static validation. Enable the Kubernetes Job runner only after applying namespace, RBAC, NetworkPolicy, CPU/memory, and timeout controls."
    }
