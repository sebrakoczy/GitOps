# Challenge Authoring Format

The current seed data lives in `apps/api/app/main.py`. A future version should load these from YAML or JSON. Use this shape:

```yaml
slug: parse-k8s-cpu
title: Parse Kubernetes CPU Quantities
role_slug: senior-platform-engineer
difficulty: Easy
category: Kubernetes Scripting
function_name: parse_cpu
languages:
  - python
  - javascript
starter_code:
  python: |
    def parse_cpu(value):
        pass
  javascript: |
    function parse_cpu(value) {
    }
visible_tests:
  - name: millicores
    input: ["500m"]
    expected: 500
hidden_tests:
  - name: decimal-core
    input: ["2.5"]
    expected: 2500
tags:
  - kubernetes
  - parsing
hints:
  - A value ending in m is already millicores.
```

## Good homelab challenge categories

- Kubernetes YAML debugging
- Terraform expression safety
- Linux shell parsing
- Dockerfile security policy
- AWS IAM policy reasoning
- CI/CD pipeline graph logic
- Observability query interpretation
- Incident response prioritization
- AI workload scheduling
