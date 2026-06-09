# AIMPOS-Spark Visual — Sprint 0 Status

**Document Type:** Execution Tracker (living)
**Sprint:** 0 — Platform Skeleton
**Last updated:** 2026-06-09
**Sources of truth:** [Sprint 0 — Platform Skeleton.md](./Sprint%200%20%E2%80%94%20Platform%20Skeleton.md) · [Sprint Reclassification.md](./Sprint%20Reclassification.md) · [DECISIONS.md](./DECISIONS.md)

This tracker reflects build progress only. Scope, AC, and gates remain governed by the frozen planning documents.

---

## Progress summary

| Metric | Value |
|--------|------:|
| Sprint 0 issues (class A) | 26 |
| Complete | 2 |
| In progress | 0 |
| Not started | 24 |

**Issue closure policy:** an issue is marked **Done** here when implementation is complete and PR-reviewed. The GitHub issue is **closed on merge to `main`** per [definition-of-done.md](./docs/governance/definition-of-done.md). "Done (pending merge)" means code + review are complete but the PR has not yet landed.

---

## Issue status

Legend: ✅ Done · 🟡 In progress · ⬜ Not started

### Backend foundation
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-04 | 4 | Database schema foundation | ⬜ |
| US-03 | 5 | API health and logging | ⬜ |
| T-02-02 | 45 | Configure PostgreSQL volume and init scripts | ✅ Done (merged, #72) |
| T-02-03 | 46 | Configure MinIO bucket on startup | ✅ Done (pending merge) |
| T-03-01 | 53 | Implement /health with dependency probes | ⬜ |
| T-03-02 | 54 | Add structured logging middleware | ⬜ |
| T-03-03 | 55 | Request ID propagation | ⬜ |
| T-04-01 | 50 | SQLAlchemy models for core tables | ⬜ |
| T-04-02 | 51 | Initial Alembic migration | ⬜ |
| T-04-03 | 52 | Repository layer interfaces | ⬜ |

### Create Project
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-01 | 8 | Create default project | ⬜ |
| FEAT-01 | 20 | Project Bootstrap | ⬜ |
| T-01-01 | 63 | Projects table migration | ⬜ |
| T-01-02 | 64 | Seed default project | ⬜ |
| T-01-03 | 65 | GET /projects endpoint | ⬜ |
| T-01-04 | 66 | Unit test project repository | ⬜ |

### Upload Asset
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-05 | 6 | MinIO asset upload service | ⬜ |
| T-05-01 | 56 | MinIO client wrapper | ⬜ |
| T-05-02 | 57 | Content-hash keys | ⬜ |
| T-05-03 | 58 | AssetVersion on upload | ⬜ |
| T-05-04 | 59 | Upload round-trip test | ⬜ |

### Login + Dashboard shell
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-25 | 17 | Bearer token auth | ⬜ |
| US-26 | 12 | Nav shell + idle routes | ⬜ |
| T-26-01 | 67 | App shell with React Router | ⬜ |
| T-26-02 | 68 | Nav bar and route guards | ⬜ |

### Governance umbrella
| Issue | # | Title | Status |
|-------|---|-------|--------|
| EPIC-06 | 42 | Governance umbrella | ⬜ (open through Sprint 5) |

---

## T-02-02 — completion record

**Issue:** #45 · **Parent:** US-02 · **Branch:** `feature/T-02-02-postgres-init`
**Status:** ✅ Done (pending merge) · **Review:** Approve with comments (resolved)

### Acceptance criteria
| AC | Result |
|----|--------|
| Named volume `aimpos-postgres-data` persists across restarts | ✅ Verified by smoke test |
| Exposes 5432 to API on internal network only | ✅ No host binding in base compose |
| Init creates DB + user matching `.env.example` | ✅ Image-created from `.env`; extensions via init script |
| `psql` connects from the api network after `up` | ✅ One-off client on `aimpos-spark` network |

### Delivered
- `deploy/compose/docker-compose.yml` — PostgreSQL service, named volume, internal `aimpos-spark` network
- `deploy/compose/docker-compose.dev.yml` — dev overlay publishing 5432
- `deploy/init/postgres/01-extensions.sql` + `README.md` — `uuid-ossp`, `pgcrypto`
- `Makefile` — `up`/`down`/`logs`/`db-shell`/`db-smoke`/`env` targets wired
- `scripts/smoke/test_postgres.py` — verifies all four AC (stdlib-only, reproducible)
- `docs/runbooks/postgres.md` — operations runbook
- `DECISIONS.md` — D-16 (with D-11 reconciliation)

### Verification
`python scripts/smoke/test_postgres.py` → PASS (all four AC), ~30s, exits 0.

### Review outcome
Approve with comments. Decision-log inconsistency (D-11 vs D-16) reconciled in `DECISIONS.md`. Remaining comments captured as technical debt below.

---

## T-02-03 — completion record

**Issue:** #46 · **Parent:** US-02 · **Branch:** `feature/T-02-03-minio-bucket`
**Status:** ✅ Done (pending merge) · **Review:** Approve with comments (resolved)

### Acceptance criteria
| AC | Result |
|----|--------|
| MinIO starts with persistent volume | ✅ `aimpos-minio-data`; object survives recreation |
| Bucket `aimpos-hot-assets` exists after first `up` | ✅ Created by `minio-init`; `.env.example` aligned to `aimpos-hot-assets` (see D-17) |
| S3 API accessible from the api network using `.env` creds | ✅ One-off `mc` over `aimpos-spark` network |
| Init script is idempotent | ✅ Re-ran init service cleanly; bucket count = 1 |

### Delivered
- `deploy/compose/docker-compose.yml` — `minio` (internal-only, healthcheck) + one-shot `minio-init` (mc); `aimpos-minio-data` volume
- `deploy/compose/docker-compose.dev.yml` — dev overlay publishing 9000/9001
- `deploy/init/minio/create-buckets.sh` + `README.md` — idempotent, env-driven bucket
- `scripts/smoke/test_minio.py` — verifies all four AC (stdlib-only, reproducible)
- `docs/runbooks/minio.md` — operations runbook
- `Makefile` — `minio-smoke` target
- `.env.example` — `MINIO_BUCKET=aimpos-hot-assets` (AC2 alignment)
- `DECISIONS.md` — D-17 (with bucket-name resolution)

### Verification
`python scripts/smoke/test_minio.py` → PASS (all four AC), ~20s, exits 0.

### Review outcome
Approve with comments. AC2 bucket-name conflict (`aimpos-spark` placeholder vs `aimpos-hot-assets`) resolved by aligning `.env.example`; recorded in D-17. Remaining items captured as technical debt below.

---

## Technical debt register

Identified during the T-02-02 PR review. Items with a follow-up issue are tracked in the backlog; minor items are noted here for awareness.

| ID | Item | Severity | Disposition |
|----|------|----------|-------------|
| TD-01 | `env_file` injects all repo secrets into the PostgreSQL container (not least-privilege) | Low | Follow-up #69 |
| TD-02 | Smoke test is non-hermetic — operates on the dev stack/volume and bounces containers | Low | Follow-up #70 |
| TD-03 | Smoke test writes a real `.env` into the working tree when absent | Low | Follow-up #70 |
| TD-04 | `pgcrypto` is speculative for Sprint 0 (`gen_random_uuid()` is built-in on PG13+; lineage/audit is Future Release) | Low | Accepted for now; revisit if unused by US-04 |
| TD-05 | `Makefile` `logs-api` is a stub until the API service joins the compose | Trivial | Resolves when API service entry lands |
| TD-06 | Root `README.md` lacks the Sprint-0 service port map required by the Phase A DoD | Low | Follow-up #71 |
| TD-07 | `minio` uses blanket `env_file` (same least-privilege smell as TD-01) | Low | Broaden #69 to all compose services |
| TD-08 | `test_minio.py` shares the dev stack/volume (same non-hermetic gap as TD-02) | Low | Broaden #70 to all smoke tests |
| TD-09 | `#46` carries a stale `sprint:s1` label and the tasks markdown still says "Sprint 1" (live milestone is Sprint 0) | Trivial | Doc/label drift; same as T-02-02 |

---

## Follow-up backlog items (recorded, not implemented)

| # | Title | Milestone | Labels |
|---|-------|-----------|--------|
| [#69](https://github.com/smcshahid/ai-media-production-os/issues/69) | Harden PostgreSQL service env (least-privilege, drop blanket `env_file`) | Sprint 1 | tech-debt, devops |
| [#70](https://github.com/smcshahid/ai-media-production-os/issues/70) | Isolate PostgreSQL smoke test from the dev stack (ephemeral project/volume) | Sprint 1 | tech-debt, devops, test |
| [#71](https://github.com/smcshahid/ai-media-production-os/issues/71) | Add Sprint-0 service port map to README | Sprint 1 | tech-debt, docs |

## Planning notes (for when the owning issue begins)

- **Sprint-0 compose service ownership (resolved by approved analysis, 2026-06-09):** the **API** service entry is **required** for Sprint 0 and is owned by **US-03 / T-03-01 (#53)**; the **Redis** service entry is **optional** (only referenced by the `/health` probe) and, if included, is also owned by US-03 / T-03-01. No new task is needed.
- **T-03-01 dependency inconsistency (recorded on #53, do not action until US-03 begins):** T-03-01 lists `T-02-01` (the full 9-service compose, Sprint 1) as a dependency, but T-03-01 is Sprint 0. The real dependency is "Sprint-0 compose exists (T-02-02, D-16) + initial migration T-04-02." Correct the dependency when US-03 is picked up.

---

## Document control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-09 | Initial Sprint 0 status; T-02-02 complete; tech-debt register; follow-ups #69–#71 |
