# AIMPOS-Spark Visual — Developer shortcuts
# Functional targets land with their owning issues:
#   up/down/logs/db-* -> T-02-02 (Sprint-0 compose: postgresql, minio, redis, api)
#   migrate           -> US-04   (Alembic initial migration)
#   logs-api/health   -> T-03-01 (API service + /health endpoint)

COMPOSE_FILE := deploy/compose/docker-compose.yml
COMPOSE_DEV  := deploy/compose/docker-compose.dev.yml
ENV_FILE     := .env
COMPOSE      := docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE)
COMPOSE_DEV_CMD := docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV) --env-file $(ENV_FILE)

.PHONY: help env up up-dev down logs logs-api db-shell db-smoke minio-smoke health migrate migrate-down

# US-04 / T-04-02: until the API image lands (US-03), run Alembic in a one-off
# python container attached to the compose network so DATABASE_URL
# (postgresql:5432 from .env) resolves. Requires the stack running (make up).
# When the API image exists this becomes `docker compose run --rm api alembic
# <cmd>` (see DECISIONS.md D-20). aimpos-core is installed editable; api itself
# is not pip-installed (its source is on the path via alembic.ini prepend).
MIGRATE_DEPS := sqlalchemy>=2.0,<3.0 alembic>=1.13,<2.0 psycopg[binary]>=3.2,<4.0
define ALEMBIC_RUN
docker run --rm --network aimpos-spark --env-file $(ENV_FILE) \
	-v "$(CURDIR)":/repo -w /repo/api python:3.12-slim \
	sh -c "pip install -q '$(MIGRATE_DEPS)' -e /repo/packages/aimpos-core && alembic $(1)"
endef

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
	@echo "  make health      Curl the API /health endpoint (needs make up-dev)"
	@echo "  make migrate     Apply Alembic migrations (alembic upgrade head)"
	@echo "  make migrate-down Roll back the last Alembic migration (downgrade -1)"

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
	$(COMPOSE) logs -f api

# Hits /health on the dev-published port. -f makes curl exit non-zero on 503 so
# this doubles as a quick readiness gate. Requires `make up-dev`.
health:
	curl -fsS http://localhost:$${API_PORT:-8000}/health | python -m json.tool

db-shell:
	$(COMPOSE) exec postgresql sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-smoke:
	python scripts/smoke/test_postgres.py

minio-smoke:
	python scripts/smoke/test_minio.py

migrate:
	$(call ALEMBIC_RUN,upgrade head)

migrate-down:
	$(call ALEMBIC_RUN,downgrade -1)
