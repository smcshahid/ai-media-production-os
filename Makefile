# AIMPOS-Spark Visual — Developer shortcuts
# Targets are stubbed during Repository Setup (T-00-01).
# They become functional as their owning issues land:
#   up/down  -> T-02-02 (Sprint-0 compose: postgresql, minio, redis, api)
#   migrate  -> US-04   (Alembic initial migration)

.PHONY: help up down migrate logs-api

help:
	@echo "AIMPOS-Spark Visual - make targets"
	@echo "  make up        Start local compose stack (available after T-02-02)"
	@echo "  make down      Stop local compose stack (available after T-02-02)"
	@echo "  make migrate   Apply Alembic migrations (available after US-04)"
	@echo "  make logs-api  Tail API container logs (available after T-02-02)"

up:
	@echo "[stub] 'make up' will run docker compose up once T-02-02 lands."

down:
	@echo "[stub] 'make down' will run docker compose down once T-02-02 lands."

migrate:
	@echo "[stub] 'make migrate' will run alembic upgrade head once US-04 lands."

logs-api:
	@echo "[stub] 'make logs-api' will tail the api service once T-02-02 lands."
