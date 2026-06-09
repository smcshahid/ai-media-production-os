# AIMPOS-Spark Visual — Developer shortcuts
# Functional targets land with their owning issues:
#   up/down/logs/db-* -> T-02-02 (Sprint-0 compose: postgresql; +minio/redis/api later)
#   migrate           -> US-04   (Alembic initial migration)

COMPOSE_FILE := deploy/compose/docker-compose.yml
COMPOSE_DEV  := deploy/compose/docker-compose.dev.yml
ENV_FILE     := .env
COMPOSE      := docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE)
COMPOSE_DEV_CMD := docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV) --env-file $(ENV_FILE)

.PHONY: help env up up-dev down logs logs-api db-shell db-smoke minio-smoke migrate

help:
	@echo "AIMPOS-Spark Visual - make targets"
	@echo "  make env       Create .env from .env.example if missing"
	@echo "  make up        Start Sprint-0 compose stack (internal network)"
	@echo "  make up-dev    Start stack with host ports published (local dev)"
	@echo "  make down      Stop the compose stack"
	@echo "  make logs      Tail logs for all services"
	@echo "  make logs-api  Tail API container logs (available after API service lands)"
	@echo "  make db-shell  Open a psql shell on the postgresql service"
	@echo "  make db-smoke    Run the PostgreSQL smoke test (T-02-02 acceptance)"
	@echo "  make minio-smoke Run the MinIO smoke test (T-02-03 acceptance)"
	@echo "  make migrate     Apply Alembic migrations (available after US-04)"

env:
	@test -f $(ENV_FILE) || (cp .env.example $(ENV_FILE) && echo "Created $(ENV_FILE) from .env.example - review before use.")

up: env
	$(COMPOSE) up -d

up-dev: env
	$(COMPOSE_DEV_CMD) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

logs-api:
	@echo "[pending] 'make logs-api' tails the api service once it joins the compose stack."

db-shell:
	$(COMPOSE) exec postgresql sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-smoke:
	python scripts/smoke/test_postgres.py

minio-smoke:
	python scripts/smoke/test_minio.py

migrate:
	@echo "[stub] 'make migrate' will run alembic upgrade head once US-04 lands."
