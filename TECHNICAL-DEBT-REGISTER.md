# Technical Debt Register

**Date:** 2026-06-18  
**Mission:** Phase 7.5 Character Bible Hardening (updated from Phase 6.5 baseline)  
**Baseline:** `v0.17.1-phase7-character-hardening`  
**Method:** Evidence from D-records, US-V03–V08B acceptance, closure reports, and codebase review

---

## Ranking key

| Rank | Meaning |
|------|---------|
| **Critical** | Blocks release, causes data loss, or breaks acceptance |
| **High** | Frequent operator pain or latent production defect |
| **Medium** | Maintainability, drift, or incomplete consolidation |
| **Low** | Cosmetic, minor gaps, nice-to-have |

---

## Phase 7.5 closures

| ID | Rank | Status | Resolution |
|----|------|--------|------------|
| **TD-P7-01** | SEV-3 | **CLOSED** | Alembic 0007 `character_snapshot`; export/worker snapshot-first (D-93) |
| **TD-P6.5-08** | Medium | **PARTIAL** | Character entity + bible pilot shipped in Phase 7; hardening in 7.5 |

---

## New / updated items (Phase 7.5)

### TD-P75-01 — Olares rollout requires pod recycle for image refresh

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Olares operations |
| **Evidence** | US-V08B PATCH hotfix; pod kept stale image after `set image` |
| **Cost** | Low — deploy script pod delete |
| **Recommendation** | `deploy_usv08b.sh` / `deploy_api_usv08b.sh` delete pods post-rollout (implemented). |

### TD-P75-02 — verify_all still ends at Phase 3D

| Field | Value |
|-------|-------|
| **Rank** | **High** (inherits TD-P6.5-02) |
| **Area** | Verification |
| **Evidence** | `verify_usv08b_local.ps1` exists; `verify_all.ps1` not extended |
| **Recommendation** | Wire Phase 7/7.5 scripts into verify_all (operational, no SCR). |

---

## Register (Phase 6.5 carry-forward)

| Rank | Meaning |
|------|---------|
| **Critical** | Blocks release, causes data loss, or breaks acceptance |
| **High** | Frequent operator pain or latent production defect |
| **Medium** | Maintainability, drift, or incomplete consolidation |
| **Low** | Cosmetic, minor gaps, nice-to-have |

---

## Register

### TD-P6.5-01 — Pipeline approve is project-scoped, not episode-scoped

| Field | Value |
|-------|-------|
| **Rank** | **High** |
| **Area** | API / workflow |
| **Evidence** | `api/app/routes/pipeline.py` uses `active_for_project()`; US-V07 C1 orphan incident |
| **Cost** | Medium — API + tests + verify script alignment |
| **Risk** | Wrong run approved if active-run guard ever relaxed |
| **Recommendation** | Add optional `episode_id` to approve request; resolve via `active_for_episode()` when set. Defer until next SCR; enforce one-active-run in operations meantime. |

---

### TD-P6.5-02 — verify_all does not cover Phases 4–6

| Field | Value |
|-------|-------|
| **Rank** | **High** |
| **Area** | Verification / release |
| **Evidence** | `deploy/dev/verify_all.ps1` ends at phase3d; D-72 stale |
| **Cost** | Low — orchestrator wiring only |
| **Risk** | Regressions in multi-scene, narration, episode undetected by consolidated gate |
| **Recommendation** | Extend `verify_all.ps1` and `verify_all_olares.ps1` with phase4/5/6 + US-V05–07 smoke flags. |

---

### TD-P6.5-03 — Drift check Alembic default outdated

| Field | Value |
|-------|-------|
| **Rank** | **High** |
| **Area** | Olares operations |
| **Evidence** | `check_drift.sh` `EXPECTED_ALEMBIC:=0003`; manifest requires **0005** |
| **Cost** | Low |
| **Risk** | False PASS or missed migration drift on v0.16 cluster |
| **Recommendation** | Read expected alembic from `deploy/release/manifest.yaml` in drift script wrapper. |

---

### TD-P6.5-04 — US-V05/V06 verification lacks concurrency hardening

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Verification |
| **Evidence** | No `flock`, DB-only cancel; US-V07 fixes not backported |
| **Cost** | Medium — extract `verify_common.sh` + backport |
| **Risk** | SEV-3 recurrence on re-run of older acceptance suites |
| **Recommendation** | Backport US-V07 patterns per [VERIFICATION-STANDARDS.md](docs/operations/VERIFICATION-STANDARDS.md). |

---

### TD-P6.5-05 — Duplicate verification helper code

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Verification |
| **Evidence** | 50+ scripts under `deploy/k8s/*-verify/` with copied `poll_until`, `approve` |
| **Cost** | Medium |
| **Risk** | Fix in one script not propagated |
| **Recommendation** | Create `deploy/k8s/lib/verify_common.sh`; source from phase scripts. |

---

### TD-P6.5-06 — Acceptance image tags vs release manifest tags

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Release / Olares |
| **Evidence** | Olares runs `usv07-phase6`; manifest pins `v0.16.0-phase6-episode` |
| **Cost** | Low — retag/redeploy |
| **Risk** | Operator uncertainty about running version |
| **Recommendation** | Post-release deploy script reads manifest tags only; document in Olares guide. |

---

### TD-P6.5-07 — log() stdout pollution in US-V05/V06

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Verification |
| **Evidence** | `tee -a` on stdout; US-V07 fixed with stderr logging |
| **Cost** | Low |
| **Risk** | HTTP 422 on pipeline start if log pollutes captured stdout |
| **Recommendation** | Adopt stderr logging contract everywhere. |

---

### TD-P6.5-08 — Character continuity model

| Field | Value |
|-------|-------|
| **Rank** | **Low** (was Medium) |
| **Area** | Domain / agents |
| **Evidence** | Phase 7 Character Bible + Phase 7.5 snapshot hardening |
| **Status** | **Pilot complete** — cap 3/project; no memory/RAG |
| **Recommendation** | Future SCR only if cap, fields, or memory scope expands. |

---

### TD-P6.5-09 — TTS quality (espeak default)

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Worker / narration |
| **Evidence** | D-82; PHASE-5 closure notes speaches optional |
| **Cost** | Low — config + verify path |
| **Risk** | Creator-facing quality ceiling |
| **Recommendation** | Document speaches enablement in Olares ops; optional quality path in future SCR. |

---

### TD-P6.5-10 — VIDEO_I2V often disabled in acceptance

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Worker / GPU |
| **Evidence** | US-V07 logs: `video_i2v_enabled=false` → slideshow |
| **Cost** | N/A — intentional for CPU acceptance |
| **Risk** | Production config diverges from acceptance |
| **Recommendation** | Separate acceptance profile: `ACCEPTANCE_I2V=false` documented; production profile in manifest. |

---

### TD-P6.5-11 — MinIO orphan blob on DB failure (TD-25 legacy)

| Field | Value |
|-------|-------|
| **Rank** | **Low** |
| **Area** | API storage |
| **Evidence** | D-record TD-25 referenced in DECISIONS |
| **Cost** | Medium |
| **Risk** | Storage clutter, not data corruption |
| **Recommendation** | Deferred; content-addressed keys limit impact. |

---

### TD-P6.5-12 — Uvicorn plaintext startup logs (TD-19 legacy)

| Field | Value |
|-------|-------|
| **Rank** | **Low** |
| **Area** | Observability |
| **Evidence** | DECISIONS D-19 gap |
| **Cost** | Low |
| **Risk** | Log pipeline inconsistency |
| **Recommendation** | Deferred. |

---

### TD-P6.5-13 — Release process doc version stale

| Field | Value |
|-------|-------|
| **Rank** | **Low** |
| **Area** | Documentation |
| **Evidence** | `RELEASE-PROCESS.md` header "Phase 3D" |
| **Cost** | Trivial |
| **Risk** | Operator follows outdated cadence table |
| **Recommendation** | Update on next release doc pass; superseded by RELEASE-GOVERNANCE-GUIDE.md. |

---

## Summary by rank

| Rank | Count | Top action |
|------|-------|------------|
| Critical | **0** | — |
| High | **3** | verify_all extension (TD-P75-02 / P6.5-02), drift alembic, approve episode scoping |
| Medium | **7** | Verification consolidation, Olares pod recycle (mitigated) |
| Low | **4** | Docs and observability polish |

---

## Prioritized remediation order (operational, no SCR)

1. TD-P6.5-03 — Drift alembic from manifest (expect **0007**)  
2. TD-P75-02 / TD-P6.5-02 — verify_all phases 4–7.5  
3. TD-P6.5-04/05/07 — Verification library + backport  
4. TD-P6.5-06 — Manifest-aligned Olares deploy  
