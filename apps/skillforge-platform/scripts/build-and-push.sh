#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/sebrakoczy}"
VERSION="${VERSION:-0.1.1}"
PLATFORM="${PLATFORM:-linux/amd64}"
BUILDER="${BUILDER:-skillforge-builder}"

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER" --use >/dev/null
else
  docker buildx use "$BUILDER" >/dev/null
fi

echo "Building and pushing SkillForge images"
echo "Registry: $REGISTRY"
echo "Version:  $VERSION"
echo "Platform: $PLATFORM"

docker buildx build --platform "$PLATFORM" -f backend/Dockerfile -t "$REGISTRY/skillforge-api:$VERSION" --push .
docker buildx build --platform "$PLATFORM" -f frontend/Dockerfile -t "$REGISTRY/skillforge-web:$VERSION" --push .
docker buildx build --platform "$PLATFORM" -f worker/Dockerfile -t "$REGISTRY/skillforge-worker:$VERSION" --push .
