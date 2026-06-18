# US-V07 Episode Model Pilot — Acceptance Package

**Date:** 2026-06-18  
**Mission:** US-V07 Episode Model Acceptance & Release Attestation  
**Baseline:** Phase 6 implementation (SCR-2026-004) · `v0.15.0-phase5-narration` + Phase 6 delta  
**Verifier:** Verification Lead (local automated + Olares E2E)  
**Governance decision:** **US-V07 ACCEPTED**  
**Release:** `v0.16.0-phase6-episode` — see [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md)

---

## Executive summary

| Path | Scope | Olares result | Authoritative run / episode | Evidence |
|------|-------|---------------|----------------------------|----------|
| **PATH A** | 1 episode, 1 scene, narrated → manifest v4 | **PASS** | `16d4b266-…` / ep **23** | `evidence/us-v07-verification/olares-2026-06-17/path-a/` |
| **PATH B** | 1 episode, 3 scenes, narrated → manifest v4 | **PASS** | `cad81163-…` / ep **24** | `evidence/us-v07-verification/olares-2026-06-17/path-b/` |
| **PATH C1** | Multi-episode project — Episode 1 export | **PASS** (supplement) | `1e9e6246-…` / ep **28** | `evidence/us-v07-verification/olares-2026-06-17/path-c1/` |
| **PATH C2** | Multi-episode project — Episode 2 export | **PASS** | `1e4f8f0a-…` / ep **26** | `evidence/us-v07-verification/olares-2026-06-17/path-c2/` |
| **PATH D** | Legacy manifest v1/v2/v3 backward compat | **PASS** | `7e8699d1…`, `3258cc26…`, `e3c0d402…` | `evidence/us-v07-verification/olares-2026-06-17/path-d/` |
| **PATH E** | Audit, history, lineage, run history | **PASS** | ref run `16d4b266-…` | `evidence/us-v07-verification/olares-2026-06-17/path-e/` |
| **Local automated** | Unit/integration suites | **PASS** | FAIL=0 | `evidence/us-v07-verification/local-2026-06-17/logs/` |
| **Olares deploy** | Phase 6 images `usv07-phase6` | **PASS** | Alembic **0005** applied | `evidence/us-v07-verification/olares-2026-06-17/logs/` |

**Final matrix:** All paths **PASS** after PATH C1 supplemental attestation (see [PASS-FAIL-MATRIX.md](evidence/us-v07-verification/olares-2026-06-17/PASS-FAIL-MATRIX.md)).

---

## Path A — Single episode, single scene, narrated (PASS Olares)

**Run:** `16d4b266-c088-4b8a-baf8-188f83470be0`  
**Episode:** `7b8639a0-7c0e-4f40-a05b-a6a8a4e31bbf` (number **23**)  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v4 | **PASS** (~14.6 MB) |
| `episodes/episode_23/` layout | **PASS** |
| `narration.wav` in manifest | **PASS** |
| `idea.txt` at ZIP root | **PASS** |

---

## Path B — Single episode, three scenes, narrated (PASS Olares)

**Run:** `cad81163-76e2-4f03-9f6f-30299e080f66`  
**Episode:** `cd73536e-a211-414b-9fa4-294a280b707c` (number **24**)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v4 | **PASS** (~46.3 MB) |
| `scene_count` = 3 | **PASS** |
| Scene paths under `episodes/episode_24/scenes/` | **PASS** |
| Narration sidecars per scene | **PASS** |

---

## Path C — Multi-episode project (PASS Olares)

### C1 — Episode 1 (supplemental attestation)

Primary E2E run `69c705a6-…` (ep 25) was orphaned by overlapping verification (SEV-3, closed). Supplemental run **PASS**:

**Run:** `1e9e6246-b059-4107-b50d-c1626d5d8e84`  
**Episode:** `b899fad1-5a61-4294-85dc-ca03d1ebcfe0` (number **28**)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v4 | **PASS** (~13.5 MB) |
| Episode status COMPLETED | **PASS** |
| NARRATION assets ≥ 1 | **PASS** |

### C2 — Episode 2 (primary E2E)

**Run:** `1e4f8f0a-1e77-4521-a91f-002355b688ef`  
**Episode:** `2f8097fc-1bf0-42c6-9407-5abe99cefd75` (number **26**)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v4 | **PASS** (~12.5 MB) |
| Episode isolation (C1 ≠ C2 numbering) | **PASS** (ep 28 vs ep 26) |

---

## Path D — Backward compatibility (PASS Olares)

| Legacy tier | Run | manifest_version | Result |
|-------------|-----|------------------|--------|
| v3 narrated single-scene | `e3c0d402-f623-42e7-a120-c5b284d13242` | **3** | **PASS** |
| v2/v3 multi-scene | `3258cc26-d971-47d9-8c7f-b5868c2de9d4` | **3** | **PASS** |
| v1 silent (no narration assets) | `7e8699d1-35c6-4135-9a2b-404a737ad622` | **3** | **PASS** (export ladder preserved) |

Episode-scoped runs do not alter legacy export ladder.

---

## Path E — Governance regression (PASS Olares)

**Reference run:** `16d4b266-c088-4b8a-baf8-188f83470be0`

| Check | Result |
|-------|--------|
| Audit append-only | **PASS** |
| Asset history HTTP 200 | **PASS** |
| Lineage read-only HTTP 200 | **PASS** |
| Run history HTTP 200 | **PASS** |

---

## Local automated regression

| Suite | Result |
|-------|--------|
| Core episode | **4 passed** |
| API unit | **121 passed** |
| Worker unit | **58 passed**, 1 skipped |
| Web vitest | **44 passed** |

Logs: `evidence/us-v07-verification/local-2026-06-17/logs/`

---

## Manifest v4 specification (summary)

| Field | Description |
|-------|-------------|
| `manifest_version` | `"4"` when run has `episode_id` |
| `episode_id` | UUID of episode |
| `episode_number` | 1-based within project |
| `files[].episode_number` | Per-file episode scope |
| ZIP layout | `episodes/episode_XX/` + optional `scenes/scene_XX/` |
| Shared IDEA | `idea.txt` at ZIP root |

v1/v2/v3 ladder unchanged for legacy runs (`episode_id IS NULL`).

---

## Olares verification

| Step | Result |
|------|--------|
| Alembic **0005** on PostgreSQL | **PASS** |
| Deploy `aimpos-api:usv07-phase6`, worker, web | **PASS** |
| E2E PATH A–E (`verify_usv07_e2e.sh`) | **PASS** (C1 via supplement) |
| Evidence archived | **PASS** |

Evidence root: `evidence/us-v07-verification/olares-2026-06-17/`

---

## Defects closed

| ID | Severity | Description | Disposition |
|----|----------|-------------|-------------|
| US-V07-C1-ORPHAN | SEV-3 | Primary E2E C1 orphaned when C2 started during STORYBOARD | **CLOSED** — supplement PASS; script hardened (`flock`, workflow terminate, idle wait) |

No open SEV-1 or SEV-2 defects.
