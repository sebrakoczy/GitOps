# SkillForge Troubleshooting

## ImagePullBackOff for web/api/worker

The Helm chart points to registry images. Build and push the images before deploying:

```bash
docker login ghcr.io -u sebrakoczy
REGISTRY=ghcr.io/sebrakoczy VERSION=0.1.1 PLATFORM=linux/amd64 ./scripts/build-and-push.sh
```

Use `linux/amd64` for typical Intel/AMD homelab nodes. If you need multi-arch images and your Docker builder supports it, use:

```bash
PLATFORM=linux/amd64,linux/arm64 ./scripts/build-and-push.sh
```

Check the exact pull failure:

```bash
kubectl -n skillforge describe pod -l app.kubernetes.io/component=api | sed -n '/Events:/,$p'
kubectl -n skillforge get events --sort-by=.lastTimestamp | tail -40
```

If GHCR packages are private, create an image pull secret:

```bash
kubectl -n skillforge create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username=sebrakoczy \
  --docker-password='<GITHUB_PAT_WITH_READ_PACKAGES>'
```

Then install with:

```bash
helm upgrade --install skillforge ./deploy/helm/skillforge \
  -n skillforge \
  -f ./deploy/helm/skillforge/values-homelab-nodeport.yaml \
  --set imagePullSecrets[0].name=ghcr-pull
```

## Postgres CrashLoopBackOff on Longhorn

The chart sets:

```yaml
PGDATA=/var/lib/postgresql/data/pgdata
```

This avoids Postgres trying to initialize directly in the PVC mount root, which can contain filesystem metadata such as `lost+found`.

Check Postgres logs:

```bash
kubectl -n skillforge logs statefulset/skillforge-postgres --previous
kubectl -n skillforge describe pod skillforge-postgres-0 | sed -n '/Events:/,$p'
```

If the first failed initialization wrote bad partial data and you do not need to preserve this fresh database, reset the PVC:

```bash
helm uninstall skillforge -n skillforge
kubectl -n skillforge delete pvc data-skillforge-postgres-0 redis-data-skillforge-redis-0 --ignore-not-found
helm upgrade --install skillforge ./deploy/helm/skillforge \
  -n skillforge --create-namespace \
  -f ./deploy/helm/skillforge/values-homelab-nodeport.yaml
```
