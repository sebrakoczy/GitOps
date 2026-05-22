.PHONY: up down build template

up:
	docker compose up --build

down:
	docker compose down

build:
	./scripts/build-and-push.sh

template:
	./scripts/helm-template.sh
