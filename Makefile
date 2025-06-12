SHELL := /bin/bash

ENV_FILE := .env
-include $(ENV_FILE)
export COMPOSE_BAKE=true

ifndef ENV
	ENV=dev
endif

.PHONY: build-yaml up upd down ps logs

build-yaml:
	@echo "=========================================================================="
	@echo "=========================== BUILDING YAML FILE ==========================="
	@echo "=========================================================================="
	@set -a; source ${ENV_FILE}; set +a; \
	envsubst < docker-compose-template.yaml > docker-compose.yaml
	@echo "--- Created yaml file ---"
	@test -f docker-compose.yaml && echo "docker-compose.yaml - File exists" || echo "docker-compose.yaml - File does not exist"


up: build-yaml
	@echo "----------------- Starting Docker containers -------------------"
	docker compose --env-file ${ENV_FILE} -f docker-compose.yaml up --remove-orphans
upd: build-yaml
	@echo "----------------- Starting Docker containers -------------------"
	docker compose --env-file ${ENV_FILE} -f docker-compose.yaml up -d --remove-orphans
down:
	@echo "----------------- Stopping Docker containers -------------------"
	docker compose --env-file ${ENV_FILE} -f docker-compose.yaml down --remove-orphans
ps:
	@echo "----------------- Listing running Docker containers -------------------"
	docker ps
logs:
	@echo "----------------- Following Docker logs -------------------"
	docker compose logs -f
