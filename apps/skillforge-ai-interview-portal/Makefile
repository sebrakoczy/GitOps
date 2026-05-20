APP ?= skillforge
REGISTRY ?= ghcr.io/YOUR_GITHUB_ORG
TAG ?= 0.2.0

.PHONY: dev build docker-build k8s-apply k8s-delete

dev:
	docker compose up --build

build:
	cd apps/web && npm install && npm run build
	docker build -t $(REGISTRY)/$(APP)-api:$(TAG) ./apps/api
	docker build -t $(REGISTRY)/$(APP)-web:$(TAG) ./apps/web

docker-build:
	docker build -t $(REGISTRY)/$(APP)-api:$(TAG) ./apps/api
	docker build -t $(REGISTRY)/$(APP)-web:$(TAG) ./apps/web

k8s-apply:
	kubectl apply -k k8s/overlays/homelab

k8s-delete:
	kubectl delete -k k8s/overlays/homelab
