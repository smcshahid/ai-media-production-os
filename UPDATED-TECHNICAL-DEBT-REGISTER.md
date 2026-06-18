# Technical Debt Register (Updated — Phase 8)

**Date:** 2026-06-18  
**Mission:** Phase 8 Platform Consolidation  
**Baseline:** `v0.17.1-phase7-character-hardening` → consolidation release `v0.18.0-phase8-consolidation`  
**Supersedes:** `TECHNICAL-DEBT-REGISTER.md` (Phase 7.5)

---

## Phase 8 closures

| ID | Rank | Status | Resolution |
|----|------|--------|------------|
| **TD-P75-02** | High | **CLOSED** | `verify_all.ps1` + Makefile through Phase 7.5; `make verify-all` |
| **TD-P75-01** | Medium | **CLOSED** | `olares_deploy_common.sh` pod recycle |
| **TD-P6.5-03** | High | **CLOSED** | Manifest-driven drift; no hardcoded Alembic |
| **TD-P6.5-02** | High | **CLOSED** | Merged into TD-P75-02 |
| **TD-P6.5-04** | Medium | **CLOSED** | flock + Temporal terminate in `verify_common.sh` |
| **TD-P6.5-05** | Medium | **CLOSED** | Shared library; US-V05–V08B backported |
| **TD-P6.5-07** | Medium | **CLOSED** | stderr logging via library |
| **TD-P6.5-01** | High | **CLOSED** | Optional `episode_id` on `POST /pipeline/approve` |

---

## Active register (carry-forward)

### TD-P6.5-06 — Acceptance image tags vs release manifest tags

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Release / Olares |
| **Evidence** | Olares `usv08b-phase75` vs manifest `v0.17.1-phase7-character-hardening` |
| **Recommendation** | Post-release deploy from manifest pins; drift override for acceptance documented in Olares ops |

### TD-P6.5-09 — TTS quality (espeak default)

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Worker / narration |
| **Recommendation** | Document speaches enablement; optional quality SCR |

### TD-P6.5-10 — VIDEO_I2V acceptance profile

| Field | Value |
|-------|-------|
| **Rank** | **Medium** |
| **Area** | Worker / GPU |
| **Recommendation** | Separate acceptance vs production profiles in manifest |

### TD-P6.5-11 — MinIO orphan blob on DB failure

| Field | Value |
|-------|-------|
| **Rank** | **Low** |
| **Status** | Deferred |

### TD-P6.5-12 — Uvicorn plaintext startup logs

| Field | Value |
|-------|-------|
| **Rank** | **Low** |
| **Status** | Deferred |

### TD-P6.5-13 — Release process doc version stale

| Field | Value |
|-------|-------|
| **Rank** | **Low** |
| **Status** | Partially superseded by `RELEASE-GOVERNANCE-GUIDE.md` |

---

## Debt reduction summary

| Rank | Before Phase 8 | After Phase 8 |
|------|----------------|---------------|
| Critical | 0 | **0** |
| High | 3 | **0** |
| Medium | 7 | **3** |
| Low | 4 | **4** |

**Net:** 8 items closed; 0 new Critical/High items introduced.

---

## Prioritized next actions (operational, no SCR)

1. TD-P6.5-06 — Align Olares production deploy to manifest semver tags
2. TD-P6.5-09 — Narration quality path documentation
3. OPS-02 — GPU burst pilot execution (governance authorization required)

---

## References

- [PHASE-8-CONSOLIDATION-CLOSURE.md](PHASE-8-CONSOLIDATION-CLOSURE.md)
- [US-V09-ACCEPTANCE-PACKAGE.md](US-V09-ACCEPTANCE-PACKAGE.md)
