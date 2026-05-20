#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/YOUR_GITHUB_ORG}"
TAG="${TAG:-0.2.0}"

docker build -t "$REGISTRY/skillforge-api:$TAG" ./apps/api
docker build -t "$REGISTRY/skillforge-web:$TAG" ./apps/web

docker push "$REGISTRY/skillforge-api:$TAG"
docker push "$REGISTRY/skillforge-web:$TAG"
