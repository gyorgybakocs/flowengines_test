SHELL := /bin/bash

ENV_FILE := environment/.env
-include $(ENV_FILE)
export COMPOSE_BAKE=true

ifndef ENV
	ENV=dev
endif

.PHONY: clear pre-build build build-yaml build-pgvector build-postgres build-redis build-mongodb build-langflow

CONTAINER_NAMES=pgvector-db-${IMG_POSTFIX} postgres-db-${IMG_POSTFIX} redis-${IMG_POSTFIX} mongodb-${IMG_POSTFIX} langflow-${IMG_POSTFIX}
VOLUME_NAMES=pgvector-${IMG_POSTFIX}-data postgres-${IMG_POSTFIX}-data redis-${IMG_POSTFIX}-data mongodb-${IMG_POSTFIX}-data langflow-${IMG_POSTFIX}-data
IMAGE_NAMES=${IMG_PREFIX}-pgvector-db-${IMG_POSTFIX} ${IMG_PREFIX}/postgres-${IMG_PREFIX} ${IMG_PREFIX}-redis-${IMG_POSTFIX} ${IMG_PREFIX}-mongodb-${IMG_POSTFIX} ${IMG_PREFIX}-langflow-${IMG_POSTFIX}
NETWORK_NAME=environment_${IMG_POSTFIX}_net_int

clear:
	@echo "=========================================================================="
	@echo "========================= STOPPING ALL CONTAINERS ========================"
	@echo "=========================================================================="
	@docker stop $(CONTAINER_NAMES) 2>/dev/null || echo "[INFO] Some main containers are not running or already stopped"
ifeq ($(ENV),dev)
	@docker stop $(DEV_ONLY_CONTAINER_NAMES) 2>/dev/null || echo "[INFO] Some dev-only containers are not running or already stopped"
endif
ifeq ($(ENV),prod)
	@docker stop $(PROD_ONLY_CONTAINER_NAMES) 2>/dev/null || echo "[INFO] Some prof-only containers are not running or already stopped"
endif
	@echo "=========================================================================="
	@echo "======================== REMOVING ALL CONTAINERS ========================="
	@echo "=========================================================================="
	@docker rm -f $(CONTAINER_NAMES) 2>/dev/null || echo "[INFO] Some main containers not found or already removed"
ifeq ($(ENV),dev)
	@docker rm -f $(DEV_ONLY_CONTAINER_NAMES) 2>/dev/null || echo "[INFO] Some dev-only containers not found or already removed"
endif
ifeq ($(ENV),prod)
	@docker rm -f $(PROD_ONLY_CONTAINER_NAMES) 2>/dev/null || echo "[INFO] Some dev-only containers not found or already removed"
endif
	@echo "=========================================================================="
	@echo "========================== REMOVING ALL VOLUMES =========================="
	@echo "=========================================================================="
	@docker volume rm $(VOLUME_NAMES) 2>/dev/null || echo "[INFO] Some volumes not found or already removed"

	@echo "=========================================================================="
	@echo "================ REMOVING ALL BUILT APPLICATION IMAGES ==================="
	@echo "=========================================================================="
	@docker rmi -f $(IMAGE_NAMES) 2>/dev/null || echo "[INFO] Some application images not found or already removed"
ifeq ($(ENV),dev)
	@docker rmi -f $(DEV_PRE_BUILT_RUNTIME_IMAGE_NAMES) 2>/dev/null || echo "[INFO] Some dev pre-built runtime images not found or already removed"
endif
ifeq ($(ENV),prod)
	@docker rmi -f $(PROD_PRE_BUILT_RUNTIME_IMAGE_NAMES) 2>/dev/null || echo "[INFO] Some prod pre-built runtime images not found or already removed"
endif
	@echo "=========================================================================="
	@echo "========================== PRUNING ALL BUILDERS =========================="
	@echo "=========================================================================="
	@docker builder prune -a -f

	@echo "=========================================================================="
	@echo "============================ REMOVING NETWORKS ==========================="
	@echo "=========================================================================="
	@docker network rm $(NETWORK_NAME) 2>/dev/null || echo "[INFO] Network not found or already removed"

	@echo "[SUCCESS] Environment cleared successfully"

build-pgvector-base:
	@echo "=========================================================================="
	@echo "========== CREATING PGVECTOR BASE IMAGE (ENVIRONMENT: $(ENV)) ============"
	@echo "=========================================================================="
	@echo "--> Building for PRODUCTION/DEVELOPMENT environment."
	@echo "--> Using full-featured Debian image for convenience: pgvector:${PGVECTOR_VERSION}"
	@docker pull pgvector/pgvector:${PGVECTOR_VERSION}
	@docker tag pgvector/pgvector:${PGVECTOR_VERSION} ${CUSTOM_PGVECTOR_IMG}
	@echo "[SUCCESS] $(ENV) pgvector base image created as ${CUSTOM_PGVECTOR_IMG}"

build-postgres-base:
	@echo "=========================================================================="
	@echo "========== CREATING POSTGRES BASE IMAGE (ENVIRONMENT: $(ENV)) ============"
	@echo "=========================================================================="
	@echo "--> Building for PRODUCTION/DEVELOPMENT environment."
	@echo "--> Using full-featured Debian image for convenience: postgres:${POSTGRESDB_VERSION}"
	@docker pull postgres:${POSTGRESDB_VERSION}
	@docker tag postgres:${POSTGRESDB_VERSION} ${CUSTOM_POSTGRESDB_IMG}
	@echo "[SUCCESS] $(ENV) postgres base image created as ${CUSTOM_POSTGRESDB_IMG}"

build-redis-base:
	@echo "=========================================================================="
	@echo "============ CREATING REDIS BASE IMAGE (ENVIRONMENT: $(ENV)) ============="
	@echo "=========================================================================="
	@echo ""
ifeq ($(ENV),prod)
	@echo "--> Building for PRODUCTION environment."
	@echo "--> Using secure, minimal alpine image: redis:${REDIS_VERSION}-alpine"
	@docker pull redis:${REDIS_VERSION}-alpine
	@docker tag redis:${REDIS_VERSION}-alpine ${CUSTOM_REDIS_IMG}
	@echo "[SUCCESS] PROD redis base image created as ${CUSTOM_REDIS_IMG}"
else
	@echo "--> Building for DEVELOPMENT environment."
	@echo "--> Using full-featured Debian image for convenience: redis:${REDIS_VERSION}"
	@docker pull redis:${REDIS_VERSION}
	@docker tag redis:${REDIS_VERSION} ${CUSTOM_REDIS_IMG}
	@echo "[SUCCESS] DEV redis base image created as ${CUSTOM_REDIS_IMG}"
endif

build-mongodb-base:
	@echo "=========================================================================="
	@echo "=========== CREATING MONGODB BASE IMAGE (ENVIRONMENT: $(ENV)) ============"
	@echo "=========================================================================="
	@echo "--> Building for PRODUCTION/DEVELOPMENT environment."
	@echo "--> Using official MongoDB image: mongo:${MONGODB_VERSION}"
	@docker pull mongo:${MONGODB_VERSION}
	@docker tag mongo:${MONGODB_VERSION} ${CUSTOM_MONGODB_IMG}
	@echo "[SUCCESS] $(ENV) MongoDB base image created as ${CUSTOM_MONGODB_IMG}"

build-langflow-base:
	@echo "=========================================================================="
	@echo "=========== CREATING LANGFLOW BASE IMAGE (ENVIRONMENT: $(ENV)) ==========="
	@echo "=========================================================================="
	@echo ""
	@echo "--> Building for PRODUCTION/DEVELOPMENT environment."
	@echo "--> Using Langflow image: langflow:${LANGFLOW_VERSION}"
	@docker pull langflowai/langflow:${LANGFLOW_VERSION}
	@docker tag langflowai/langflow:${LANGFLOW_VERSION} ${CUSTOM_LANGFLOW_IMG}
	@echo "[SUCCESS] $(ENV) Langflow base image created as ${CUSTOM_LANGFLOW_IMG}"
	PYTHON_VERSION=$$(docker run --rm ${CUSTOM_LANGFLOW_IMG} sh -c 'echo $${PYTHON_VERSION%.*}'); \
	   sed -i '/^PYTHON_VERSION=/d' ${ENV_FILE}; \
	   echo "PYTHON_VERSION=$$PYTHON_VERSION" >> ${ENV_FILE};

build-base: build-pgvector-base build-postgres-base build-redis-base build-mongodb-base build-langflow-base

clear-docker-build:
	@echo 'Clearing the docker build'
	@if docker images -f "dangling=true" -q | grep -q '.*'; then \
		docker rmi $$(docker images -f "dangling=true" -q); \
	fi

build-yaml:
	@echo "=========================================================================="
	@echo "=========================== BUILDING YAML FILE ==========================="
	@echo "=========================================================================="
	@set -a; source ${ENV_FILE}; set +a; \
	envsubst < environment/docker-compose-build-template.yaml > environment/docker-compose-build.yaml
	@echo "--- Created yaml file ---"
	@test -f environment/docker-compose-build.yaml && echo "environment/docker-compose-build.yaml - File exists" || echo "environment/docker-compose-build.yaml - File does not exist"

build-redis: clear-docker-build
	@echo "=========================================================================="
	@echo "========================= BUILDING REDIS IMAGE ==========================="
	@echo "=========================================================================="
	@if docker compose --progress plain --env-file ${ENV_FILE} -f environment/docker-compose-build.yaml build redis-${IMG_POSTFIX} --no-cache; then \
		echo "[SUCCESS] Redis image built successfully as redis-${IMG_POSTFIX}"; \
	else \
		echo "[ERROR] Failed to build Redis image"; \
	fi

build-postgres: clear-docker-build
	@echo "=========================================================================="
	@echo "======================== BUILDING POSTGRES IMAGE =========================="
	@echo "=========================================================================="
	@if docker compose --progress plain --env-file ${ENV_FILE} -f environment/docker-compose-build.yaml build postgres-${IMG_POSTFIX} --no-cache; then \
		echo "[SUCCESS] Postgres image built successfully as postgres-${IMG_POSTFIX}"; \
	else \
		echo "[ERROR] Failed to build Postgres image"; \
	fi

build-pgvector: clear-docker-build
	@echo "=========================================================================="
	@echo "======================= BUILDING PGVECTOR IMAGE =========================="
	@echo "=========================================================================="
	@if docker compose --progress plain --env-file ${ENV_FILE} -f environment/docker-compose-build.yaml build pgvector-${IMG_POSTFIX} --no-cache; then \
		echo "[SUCCESS] Pgvector image built successfully as pgvector-${IMG_POSTFIX}"; \
	else \
		echo "[ERROR] Failed to build Pgvector image"; \
	fi

build-mongodb: clear-docker-build
	@echo "=========================================================================="
	@echo "======================== BUILDING MONGODB IMAGE =========================="
	@echo "=========================================================================="
	@if docker compose --progress plain --env-file ${ENV_FILE} -f environment/docker-compose-build.yaml build mongodb-${IMG_POSTFIX} --no-cache; then \
		echo "[SUCCESS] MongoDB image built successfully as mongodb-${IMG_POSTFIX}"; \
	else \
		echo "[ERROR] Failed to build MongoDB image"; \
	fi

build-langflow: clear-docker-build
	@echo "=========================================================================="
	@echo "====================== BUILDING LANGFLOW APP IMAGE ======================="
	@echo "=========================================================================="
	@if docker compose --progress plain --env-file ${ENV_FILE} -f environment/docker-compose-build.yaml build langflow-${IMG_POSTFIX} --no-cache; then \
	   echo "[SUCCESS] Langflow app image built successfully as langflow-${IMG_POSTFIX}"; \
	else \
	   echo "[ERROR] Failed to build Langflow app image"; \
	fi

build: build-yaml build-pgvector build-postgres build-redis build-mongodb build-langflow
