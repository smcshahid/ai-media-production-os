# Phase 7.5 — Character Bible Hardening Closure Report

**Date:** 2026-06-18  
**Status:** **CLOSED — US-V08B ACCEPTED — RELEASE CUT**  
**Release:** `v0.17.1-phase7-character-hardening`  
**Baseline:** `v0.17.0-phase7-character-bible`  
**Governance:** Phase 7.5 release closure **AUTHORIZED**

---

## Mission outcome

| Work package | Status |
|--------------|--------|
| WP-0 TD-P7-01 character snapshot | **DONE** |
| WP-1 Character edit UX | **DONE** |
| WP-2 Continuity hardening | **DONE** |
| WP-3 Manifest v5 governance | **DONE** |
| WP-4 Verification hardening | **DONE** |
| WP-5 Operational runbooks | **DONE** |
| WP-6 US-V08B PATH A–F | **PASS** |
| WP-7 Olares acceptance | **PASS** |
| WP-8 Release preparation | **DONE** |

---

## Technical debt remediation

| ID | Resolution |
|----|------------|
| **TD-P7-01** | Alembic **0007** `pipeline_runs.character_snapshot`; export/worker read snapshot first |

---

## Verification summary

### Local — PASS

128 API + 60 worker + 3 core + web vitest. Evidence: `evidence/us-v08b-verification/local-2026-06-18/logs/`

### Olares — PASS

Images: `aimpos-*:usv08b-phase75` · Alembic: **0007**  
Paths A, B, C, F: primary E2E **PASS**  
Paths D, E: supplemental **PASS** after PATCH hotfix  
Evidence: `evidence/us-v08b-verification/olares-2026-06-18/`

---

## Risks (residual)

| ID | Sev | Risk | Mitigation |
|----|-----|------|------------|
| R-P75-01 | SEV-3 | Olares image rollout requires pod recycle | `deploy_api_usv08b.sh` deletes pods post-rollout |
| R-P75-02 | SEV-3 | Legacy runs without snapshot | Live-row export fallback |

No open SEV-1/SEV-2 at closure.

---

## Lessons learned

1. **Snapshot at pipeline start** is the minimal correct fix for export reproducibility — no graph, RAG, or episode redesign required.
2. **Async SQLAlchemy + Pydantic** on `onupdate` columns requires explicit `updated_at` assignment on PATCH (BUG-P75-01).
3. **Olares `set image` alone** may not refresh running pods — force pod recycle after import (TD-P75-01, mitigated in deploy scripts).
4. **Supplemental path attestation** remains valid for SEV-3 verification defects (PATH D/E primary vs supplement).
5. **Verification scripts** must validate PATCH HTTP status and use manifests already written by `verify_character_export`.

---

## Release history (updated)

| Version | Codename | Date | Notes |
|---------|----------|------|-------|
| v0.13.0-phase3d | phase3d | 2026-06-17 | Platform maturity Phases 3A–3D |
| v0.14.0-phase4-multiscene | phase4-multiscene | 2026-06-17 | Multi-scene pilot (US-V05) |
| v0.15.0-phase5-narration | phase5-narration | 2026-06-17 | Audio narration pilot (US-V06) |
| v0.16.0-phase6-episode | phase6-episode | 2026-06-18 | Episode model pilot (US-V07) |
| v0.17.0-phase7-character-bible | phase7-character-bible | 2026-06-18 | Character Bible pilot (US-V08) |
| **v0.17.1-phase7-character-hardening** | **phase7-character-hardening** | **2026-06-18** | **Character snapshot + UX + US-V08B** |

---

## Recommendation for next governance phase

**Phase 8 — Platform consolidation (recommended):**

1. Extend `verify_all` through Phase 7.5 (TD-P75-02).  
2. Extract `deploy/k8s/lib/verify_common.sh` and backport flock/cancel patterns.  
3. Align Olares drift check Alembic head with manifest (**0007**).  
4. Defer new creator domains (memory, RAG, publishing, RBAC) until explicit SCR.

---

## Final deliverables

- [x] `PHASE-7.5-CHARACTER-HARDENING-CLOSURE.md` (this document)
- [x] `US-V08B-ACCEPTANCE-PACKAGE.md`
- [x] `RELEASE-READINESS-RECOMMENDATION.md`
- [x] `evidence/release-v0.17.1-phase7-character-hardening/RELEASE-EVIDENCE.md`
- [x] `docs/release/notes/v0.17.1-phase7-character-hardening.md`
- [x] `TECHNICAL-DEBT-REGISTER.md` (TD-P7-01 closed)
- [x] Tag `v0.17.1-phase7-character-hardening`

---

## Repository closure

**Complete** — release tag `v0.17.1-phase7-character-hardening` cut and pushed.

See [US-V08B-ACCEPTANCE-PACKAGE.md](US-V08B-ACCEPTANCE-PACKAGE.md) and [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md).
