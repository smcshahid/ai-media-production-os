# Release Evidence — v0.16.0-phase6-episode

**Date:** 2026-06-18  
**Release:** `v0.16.0-phase6-episode`  
**Baseline:** `v0.15.0-phase5-narration`  
**Acceptance:** US-V07 **ACCEPTED**

---

## Pre-release gates

| Gate | Result | Evidence |
|------|--------|----------|
| Core episode tests | **4 passed** | `evidence/us-v07-verification/local-2026-06-17/logs/pytest-core-episode.txt` |
| API unit tests | **121 passed** | `evidence/us-v07-verification/local-2026-06-17/logs/pytest-api.txt` |
| Worker unit tests | **58 passed** | `evidence/us-v07-verification/local-2026-06-17/logs/pytest-worker.txt` |
| Web vitest | **44 passed** | `evidence/us-v07-verification/local-2026-06-17/logs/vitest-web.txt` |
| Phase 6 local verify | **PASS** | `deploy/dev/verify_phase6_local.ps1` FAIL=0 |
| Olares E2E PATH A–E | **PASS** | `evidence/us-v07-verification/olares-2026-06-17/` |
| Alembic head | **0005** | `api/alembic/versions/0005_episode_model_pilot.py` |

---

## Olares authoritative runs

| Path | Run ID | Episode | manifest |
|------|--------|---------|----------|
| A | `16d4b266-c088-4b8a-baf8-188f83470be0` | 23 | v4 |
| B | `cad81163-76e2-4f03-9f6f-30299e080f66` | 24 | v4 |
| C1 (supplement) | `1e9e6246-b059-4107-b50d-c1626d5d8e84` | 28 | v4 |
| C2 | `1e4f8f0a-1e77-4521-a91f-002355b688ef` | 26 | v4 |

---

## Pinned images (manifest)

| Service | Image |
|---------|-------|
| API | `docker.io/library/aimpos-api:v0.16.0-phase6-episode` |
| Web | `docker.io/library/aimpos-web:v0.16.0-phase6-episode` |
| Worker | `docker.io/library/aimpos-worker:v0.16.0-phase6-episode` |

Source: `deploy/release/manifest.yaml`

---

## Phase 6 deliverables included

- Episode entity + Alembic 0005
- Episode-scoped pipeline workflow
- Manifest v4 export layout
- Episode dashboard UX
- US-V07 verification suite (local + Olares)
- Verification script hardening (flock, Temporal terminate, idle wait)

---

## Git release artifacts

| Field | Value |
|-------|-------|
| Commit | `4c9bf86` |
| Tag | `v0.16.0-phase6-episode` |
| Remote | `origin/main` (pushed) |

| Artifact | Path |
|----------|------|
| VERSION | `VERSION` |
| Release notes | `docs/release/notes/v0.16.0-phase6-episode.md` |
| Acceptance | `US-V07-ACCEPTANCE-PACKAGE.md` |
| Closure | `US-V07-CLOSURE-REPORT.md` |
| Readiness | `RELEASE-READINESS-RECOMMENDATION.md` |
| PASS/FAIL matrix | `evidence/us-v07-verification/olares-2026-06-17/PASS-FAIL-MATRIX.md` |

---

## Sign-off

| Role | Status |
|------|--------|
| Verification Lead | US-V07 ACCEPTED — all paths PASS |
| Release Manager | Tag authorized |
| Governance | Phase 6 ACCEPTED — no stop conditions triggered |
