# deploy/init/minio — MinIO initialization

MinIO has no `/docker-entrypoint-initdb.d` hook, so bucket bootstrap runs in a
dedicated one-shot `minio-init` service (the `minio/mc` client) defined in the
Sprint-0 compose. It waits for MinIO to report healthy, then runs the script
here and exits.

| Script | Purpose |
|--------|---------|
| `create-buckets.sh` | Create the `MINIO_BUCKET` bucket (idempotent) and keep it private |

## Notes

- **Bucket name is env-driven.** The script creates `$MINIO_BUCKET` from the repo
  `.env` (see `.env.example`) — it is not hardcoded. All application code must
  read the bucket from `MINIO_BUCKET` for the same reason.
- **Idempotent.** Uses `mc mb --ignore-existing`; safe to re-run on every
  `docker compose up`.
- **Credentials** come from `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` in `.env`.

Owned by **T-02-03**. Verify with `python scripts/smoke/test_minio.py`.
