# Runbook — PostgreSQL (Sprint-0 compose)

**Issue:** T-02-02 · **Parent:** US-02 · **Sprint:** 0

PostgreSQL is the system of record for the Visual MVP. This runbook covers the
Sprint-0 compose service: its volume, init scripts, networking, and how to
verify it.

## Service at a glance

| Property | Value |
|----------|-------|
| Image | `postgres:16-alpine` |
| Container | `aimpos-postgresql` |
| Network | `aimpos-spark` (internal; reachable as host `postgresql:5432`) |
| Named volume | `aimpos-postgres-data` → `/var/lib/postgresql/data` |
| Init scripts | `deploy/init/postgres/*.sql` (run once on empty volume) |
| Credentials | `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` from `.env` |

The base compose file keeps the database **internal-only** — no host port is
published. The dev overlay (`docker-compose.dev.yml`) publishes `5432` to the
host for local tooling.

## First run

```bash
cp .env.example .env          # first time only; review values
make up                       # or: docker compose -f deploy/compose/docker-compose.yml --env-file .env up -d
```

On first boot the official image creates the user and database from `.env`, then
runs `deploy/init/postgres/01-extensions.sql` to enable `uuid-ossp` and
`pgcrypto`.

## Connecting

```bash
# From inside the stack (preferred): open a psql shell
make db-shell

# From the host (requires the dev overlay so 5432 is published)
make up-dev
psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB"
```

Other services connect via the connection string in `.env`:
`postgresql+psycopg://aimpos:...@postgresql:5432/aimpos_spark` (`DATABASE_URL`).

## Verifying (acceptance criteria)

```bash
make db-smoke        # or: python scripts/smoke/test_postgres.py
```

The smoke test checks: psql connects over the `aimpos-spark` network, the
database/user/extensions exist, the base compose does not publish 5432, and the
named volume survives container recreation.

## Operations

| Task | Command |
|------|---------|
| Tail logs | `make logs` |
| Stop stack (keep data) | `make down` |
| Reset database (DESTROYS data) | `make down` then `docker volume rm aimpos-postgres-data` |
| Re-run init scripts | Remove the volume (above), then `make up` |

## Troubleshooting

- **Container never healthy:** check `make logs`; usually a malformed `.env`
  (missing `POSTGRES_PASSWORD`) or a port already in use under the dev overlay.
- **Init script did not run:** init scripts run **only** on an empty volume. If
  the volume already exists, remove it (see above) and start again.
- **`psql: could not translate host name "postgresql"`:** the client is not on
  the `aimpos-spark` network — run it inside the stack or via `make db-shell`.
