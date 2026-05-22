#!/usr/bin/env bash
set -euo pipefail

helm template skillforge ./deploy/helm/skillforge --namespace skillforge -f ./deploy/helm/skillforge/values-homelab-nodeport.yaml
