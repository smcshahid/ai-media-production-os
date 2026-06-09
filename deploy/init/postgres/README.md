# deploy/init/postgres — PostgreSQL initialization

Scripts in this directory are mounted read-only into the PostgreSQL container at
`/docker-entrypoint-initdb.d`. The official `postgres` image runs them **once**,
in lexical order, the first time the data directory is empty.

| Script | Purpose |
|--------|---------|
| `01-extensions.sql` | Enable `uuid-ossp` and `pgcrypto` for the US-04 schema |

## Notes

- The database (`POSTGRES_DB`) and user (`POSTGRES_USER`) are created by the
  image from environment variables in the repo `.env` (see `.env.example`) —
  not by these scripts.
- Scripts run **only** on an empty volume. To re-run them, remove the named
  volume: `docker volume rm aimpos-postgres-data` (destroys data).
- Keep statements idempotent (`IF NOT EXISTS`) so manual re-application is safe.

Owned by **T-02-02**. Verify with `python scripts/smoke/test_postgres.py`.
