# Runbook — MinIO (Sprint-0 compose)

**Issue:** T-02-03 · **Parent:** US-02 · **Sprint:** 0

MinIO is the content-addressable asset store for the Visual MVP. This runbook
covers the Sprint-0 compose service: its volume, bucket bootstrap, networking,
and how to verify it.

## Service at a glance

| Property | Value |
|----------|-------|
| Image | `minio/minio:RELEASE.2025-09-07T16-13-09Z` |
| Container | `aimpos-minio` (+ one-shot `aimpos-minio-init`) |
| Network | `aimpos-spark` (internal; reachable as `minio:9000`) |
| Named volume | `aimpos-minio-data` → `/data` |
| Bucket init | `deploy/init/minio/create-buckets.sh` (via `minio/mc`) |
| Bucket name | `MINIO_BUCKET` from `.env` (env-driven, not hardcoded) |
| Credentials | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` from `.env` |

The base compose keeps MinIO **internal-only** — no host ports. The dev overlay
(`docker-compose.dev.yml`) publishes `9000` (S3 API) and `9001` (console).

## How bucket bootstrap works

MinIO has no `initdb` hook, so a one-shot `minio-init` service (the `minio/mc`
client) waits for MinIO to report healthy, runs `create-buckets.sh` to create
`$MINIO_BUCKET` idempotently (`mc mb --ignore-existing`), sets it private, then
exits. Re-running `docker compose up` is safe.

## First run

```bash
cp .env.example .env      # first time only
make up                   # starts postgresql + minio + minio-init
```

## Connecting

```bash
# Console (requires the dev overlay so 9001 is published)
make up-dev
# open http://localhost:9001  (login with MINIO_ROOT_USER / MINIO_ROOT_PASSWORD)

# CLI from inside the network
docker run --rm --network aimpos-spark --entrypoint sh \
  minio/mc:RELEASE.2025-08-13T08-35-41Z \
  -c 'mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" && mc ls local'
```

## Verifying (acceptance criteria)

```bash
make minio-smoke      # or: python scripts/smoke/test_minio.py
```

Checks: S3 API reachable on the `aimpos-spark` network, bucket exists, init is
idempotent, and objects survive container recreation on the named volume.

## Operations

| Task | Command |
|------|---------|
| Tail logs | `make logs` |
| Stop stack (keep data) | `make down` |
| Reset object store (DESTROYS data) | `make down` then `docker volume rm aimpos-minio-data` |
| Re-create bucket | `docker compose -f deploy/compose/docker-compose.yml --env-file .env up -d --force-recreate minio-init` |

## Troubleshooting

- **`minio-init` exits non-zero:** check `docker logs aimpos-minio-init`; usually
  a bad `.env` (missing `MINIO_ROOT_PASSWORD`) or MinIO not yet healthy.
- **Bucket missing:** confirm `MINIO_BUCKET` is set in `.env`; re-run the init
  service (see above).
- **Bucket name mismatch with asset code:** the bucket is env-driven; ensure all
  code reads `MINIO_BUCKET` rather than a literal (see DECISIONS D-17).
