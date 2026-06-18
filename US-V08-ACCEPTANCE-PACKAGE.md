# US-V08 Character Bible Pilot — Acceptance Package

**Date:** 2026-06-18  
**Mission:** US-V08 Character Bible Acceptance & Release Attestation  
**Baseline:** Phase 7 (SCR-2026-005) · `v0.16.0-phase6-episode` + Phase 7 delta  
**Verifier:** Verification Lead (local + Olares E2E)  
**Governance decision:** **US-V08 ACCEPTED**  
**Release:** `v0.17.0-phase7-character-bible`

---

## Executive summary

| Path | Scope | Olares result | Authoritative run / episode | Evidence |
|------|-------|---------------|----------------------------|----------|
| **PATH A** | 1 character, 1 episode, 1 scene → manifest v5 | **PASS** | `e2fbec9b-…` / ep **49** | `evidence/us-v08-verification/olares-2026-06-18/path-A/` |
| **PATH B** | 3 characters, 3 scenes → manifest v5 | **PASS** | `925b2faa-…` / ep **50** | `evidence/us-v08-verification/olares-2026-06-18/path-B/` |
| **PATH C1** | Multi-episode — Episode 1 (3 chars) | **PASS** (supplement) | `885b7b2c-…` / ep **55** | `evidence/us-v08-verification/olares-2026-06-18/path-C1/` |
| **PATH C2** | Multi-episode — Episode 2 (3 chars) | **PASS** | `ae26081f-…` / ep **54** | `evidence/us-v08-verification/olares-2026-06-18/path-C2/` |
| **PATH D** | Legacy manifest v1–v4 backward compat | **PASS** | legacy runs (v2/v3 attested) | `evidence/us-v08-verification/olares-2026-06-18/path-D-*` |
| **PATH E** | Audit, history, lineage, runs, characters | **PASS** | ref `e2fbec9b-…` | `evidence/us-v08-verification/olares-2026-06-18/path-E-*` |
| **Local automated** | Core + API + worker + web | **PASS** | FAIL=0 | `evidence/us-v08-verification/local-2026-06-17/logs/` |
| **Olares deploy** | Alembic **0006**, images `usv08-phase7` | **PASS** | probe post-deploy | `evidence/us-v08-verification/olares-2026-06-18/logs/` |

**Final matrix:** All paths **PASS** after PATH C1 supplemental attestation (primary E2E overlap orphaned C1 run `2dacd911-…` — SEV-3, closed).

---

## PATH A — Single character, single episode (PASS)

**Run:** `e2fbec9b-047a-4fde-8e0b-50a2a6290861`  
**Episode:** `9e706eb0-a2e7-4cd5-b146-322978a20970` (number **49**)  
**Character:** Maya-A-a1 (`b7788c4e-…`)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v5 | **PASS** |
| `characters[]` in manifest | **PASS** (1 entry) |
| `episodes/episode_49/` layout | **PASS** |
| `narration.wav` in manifest | **PASS** |

---

## PATH B — Three characters, three scenes (PASS)

**Run:** `925b2faa-6d34-47de-8c24-c79dd1ea1382`  
**Episode:** `e270a06b-23db-4d3c-9a22-1e860069f4ac` (number **50**)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v5 | **PASS** |
| `characters[]` count = 3 | **PASS** |
| `scene_count` = 3 | **PASS** |
| Scene paths under `episodes/episode_50/scenes/` | **PASS** |

---

## PATH C — Multi-episode continuity (PASS)

### C1 — Episode 1 (supplemental attestation)

Primary E2E run `2dacd911-…` (ep 53) was orphaned by overlapping verification cleanup (SEV-3, closed). Supplemental run **PASS**:

**Run:** `885b7b2c-56b9-409d-b640-8111af7c9434`  
**Episode:** `a21f5d65-fc0c-41f1-a65f-fd9cfae4ae1d` (number **55**)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v5 | **PASS** |
| `characters[]` count = 3 | **PASS** |
| Episode status COMPLETED | **PASS** |

### C2 — Episode 2 (primary E2E)

**Run:** `ae26081f-2783-4edd-a700-deb3d2f9c80a`  
**Episode:** `dca4b850-729f-49ed-99a8-d5ed63a4f01a` (number **54**)

| Check | Result |
|-------|--------|
| Pipeline COMPLETED | **PASS** |
| Export manifest v5 | **PASS** |
| Shared character metadata pattern | **PASS** |
| Episode numbering distinct (54 vs 55) | **PASS** |

---

## PATH D — Backward compatibility (PASS)

| Legacy ladder | Sample run | Manifest | Result |
|---------------|------------|----------|--------|
| v3 narrated | `e3c0d402-…` | **3** | **PASS** |
| v2/v3 multi-scene | `3258cc26-…` | **3** | **PASS** |
| v4 episode (no characters) | `1e9e6246-…` | **4** | **PASS** (US-V07 legacy) |

Character-scoped runs use **v5** only when `character_ids` resolve to existing character rows at export time.

---

## PATH E — Platform regression (PASS)

Reference run: `e2fbec9b-047a-4fde-8e0b-50a2a6290861`

| Surface | Result |
|---------|--------|
| Audit events | **PASS** |
| Asset history | **PASS** |
| Lineage | **PASS** |
| Run history | **PASS** |
| Character list API | **PASS** |
| Episodes + narration preserved | **PASS** |

---

## Manifest v5 example

From PATH C1 (`path-C1-manifest.json`):

```json
{
  "manifest_version": "5",
  "episode_number": 55,
  "characters": [
    { "name": "Maya-C1-a1", "role": "protagonist", "visual_traits": "silver lab coat" },
    { "name": "Eli-C1-a1", "role": "mentor", "visual_traits": "weathered field jacket" },
    { "name": "Jordan-C1-a1", "role": "ally", "visual_traits": "bright orange scarf" }
  ]
}
```

---

## Migration evidence

| Step | Result | Log |
|------|--------|-----|
| Alembic 0006 on Olares | **PASS** | `logs/migration-0006.log` |
| `characters` table present | **PASS** | `logs/olares-probe-post.log` |
| `pipeline_runs.character_ids` column | **PASS** | probe |

---

## Defect classification (closed)

| ID | Class | Sev | Finding | Resolution |
|----|-------|-----|---------|------------|
| VD-V08-01 | Verification | SEV-3 | Multiline JSON grep false-negative on v5 | Fixed: Python validation in `verify_usv08_e2e.sh` |
| VD-V08-02 | Verification | SEV-3 | Character limit collision on E2E retries | Fixed: `cleanup_project_characters` + unique names |
| VD-V08-03 | Verification | SEV-3 | PowerShell docker stderr abort | Fixed: `verify_usv08_olares.ps1` ErrorAction |
| VD-V08-04 | Environment | SEV-3 | Overlapping E2E processes orphaned C1 | Closed: supplemental C1 run |
| PD-V08-01 | Product | SEV-3 | Export v5 requires character rows at export | Documented; pilot accepts run-bound IDs |

No unresolved **SEV-1** or **SEV-2**.

---

## PASS/FAIL matrix (final)

| Path | Final |
|------|-------|
| A | **PASS** |
| B | **PASS** |
| C1 | **PASS** |
| C2 | **PASS** |
| D | **PASS** |
| E | **PASS** |
| Local | **PASS** |
| Olares | **PASS** |

**US-V08: ACCEPTED**
