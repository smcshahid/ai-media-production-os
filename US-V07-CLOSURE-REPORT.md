# US-V07 Episode Model Pilot — Closure Report

**Date:** 2026-06-18  
**Mission:** US-V07 Episode Model Acceptance & Release Attestation  
**Outcome:** **ACCEPTANCE COMPLETE**  
**Release decision:** **RELEASE READY** → **`v0.16.0-phase6-episode`**

---

## Mission objective

Complete authoritative acceptance of the Phase 6 Episode Model Pilot on Olares and establish release readiness — verification and closure only, no new implementation.

---

## What was executed

### Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)

1. **Migration 0005** — applied; `episodes` table + `pipeline_runs.episode_id`
2. **Phase 6 deploy** — `aimpos-api:usv07-phase6`, `aimpos-worker:usv07-phase6`, `aimpos-web:usv07-phase6`
3. **Primary E2E** — PATH A, B, C2, D, E **PASS**; C1 orphaned (SEV-3 verification overlap)
4. **PATH C1 supplement** — `verify_path_c1_olares.sh` **PASS** (`FAIL=0`)

### Local (verification host)

1. Core episode **4** tests — PASS  
2. API **121** unit tests — PASS  
3. Worker **58** unit tests — PASS (1 skipped)  
4. Web **44** vitest — PASS  
5. `deploy/dev/verify_phase6_local.ps1` — FAIL=0  

---

## Authoritative Olares run IDs

| Path | Run ID | Episode ID | Ep # |
|------|--------|------------|------|
| A | `16d4b266-c088-4b8a-baf8-188f83470be0` | `7b8639a0-7c0e-4f40-a05b-a6a8a4e31bbf` | 23 |
| B | `cad81163-76e2-4f03-9f6f-30299e080f66` | `cd73536e-a211-414b-9fa4-294a280b707c` | 24 |
| C1 (supplement) | `1e9e6246-b059-4107-b50d-c1626d5d8e84` | `b899fad1-5a61-4294-85dc-ca03d1ebcfe0` | 28 |
| C2 | `1e4f8f0a-1e77-4521-a91f-002355b688ef` | `2f8097fc-1bf0-42c6-9407-5abe99cefd75` | 26 |

---

## Evidence locations

| Artifact | Path |
|----------|------|
| Acceptance package | `US-V07-ACCEPTANCE-PACKAGE.md` |
| PASS/FAIL matrix | `evidence/us-v07-verification/olares-2026-06-17/PASS-FAIL-MATRIX.md` |
| Olares PATH A | `evidence/us-v07-verification/olares-2026-06-17/path-a/` |
| Olares PATH B | `evidence/us-v07-verification/olares-2026-06-17/path-b/` |
| Olares PATH C1 supplement | `evidence/us-v07-verification/olares-2026-06-17/path-c1/` |
| Olares PATH C2 | `evidence/us-v07-verification/olares-2026-06-17/path-c2/` |
| Olares PATH D | `evidence/us-v07-verification/olares-2026-06-17/path-d/` |
| Olares PATH E | `evidence/us-v07-verification/olares-2026-06-17/path-e/` |
| Olares E2E logs | `evidence/us-v07-verification/olares-2026-06-17/logs/` |
| Local test logs | `evidence/us-v07-verification/local-2026-06-17/logs/` |
| Release evidence | `evidence/release-v0.16.0-phase6-episode/RELEASE-EVIDENCE.md` |

---

## Acceptance criteria scorecard

| Criterion | Required | Actual |
|-----------|----------|--------|
| PATH A PASS | Yes | **YES** |
| PATH B PASS | Yes | **YES** |
| PATH C1 PASS | Yes | **YES** (supplement) |
| PATH C2 PASS | Yes | **YES** |
| PATH D PASS | Yes | **YES** |
| PATH E PASS | Yes | **YES** |
| Olares PASS | Yes | **YES** |
| No SEV-1 open | Yes | **YES** |
| No SEV-2 open | Yes | **YES** |
| Commit/tag/push | If all PASS | **EXECUTED** |

---

## Timeline (UTC)

| Time | Event |
|------|-------|
| 00:30 | PATH A started (`16d4b266-…`) |
| 00:34 | PATH A COMPLETED, manifest v4 |
| 00:34 | PATH B started (`cad81163-…`) |
| 00:43 | PATH C1 primary started (`69c705a6-…`) — later orphaned |
| 00:44 | PATH C2 started while C1 in STORYBOARD |
| 00:50 | Primary E2E DONE FAIL=1 (C1 empty) |
| 01:16 | Orphan cancelled; verification script hardened |
| 01:18 | PATH C1 supplement started (`90516b45-…` → success on `1e9e6246-…`) |
| 01:23 | PATH C1 supplement PASS (`FAIL=0`) |
| 04:59+ | Evidence pulled; closure docs finalized |

---

## Lessons learned

1. **Single E2E instance required** — overlapping `verify_usv07_e2e.sh` processes caused C1 orphan; fixed with `flock` and Temporal workflow terminate on cancel.
2. **DB cancel ≠ workflow stop** — `cancel_active_runs` must terminate Temporal workflows and wait for project idle before the next path.
3. **Supplemental attestation is valid** — SEV-3 verification defects closed with isolated path re-run without product changes.
4. **Manifest v4 ladder works** — episode exports coexist with v1–v3 legacy exports on the same project.

---

## Recommended Phase 7 candidate

**Platform maturity track (recommended):** adopt `verify-all` / operational hardening before opening character bible or publishing SCRs. Character bible and studio workflows remain **out of scope** until explicitly authorized by governance.

---

## Related documents

- [US-V07-ACCEPTANCE-PACKAGE.md](US-V07-ACCEPTANCE-PACKAGE.md)
- [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md)
- [PHASE-6-EPISODE-CLOSURE.md](PHASE-6-EPISODE-CLOSURE.md)
- [SCR-2026-004.md](SCR-2026-004.md)
