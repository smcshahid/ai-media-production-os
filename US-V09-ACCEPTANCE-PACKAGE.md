# US-V09 Acceptance Package — Platform Re-attestation

**Date:** 2026-06-18  
**Mission:** Phase 8 Platform Consolidation  
**Baseline:** `v0.17.1-phase7-character-hardening`  
**Release:** `v0.18.0-phase8-consolidation`  
**Status:** **ACCEPTED**

---

## Scope

Verification-only re-attestation covering multi-scene, narration, episode model, character bible, character snapshots, and export ladder v1–v5.

---

## Local results — **PASS (FAIL=0)**

| Gate | Result | Evidence |
|------|--------|----------|
| Manifest validation | **PASS** | `evidence/us-v09-verification/local-2026-06-18/logs/validate-manifest.txt` |
| Export ladder v1–v5 | **14 passed** | `evidence/us-v09-verification/local-2026-06-18/logs/pytest-export-ladder.txt` |
| Episode-scoped approve | **5 passed** | `evidence/us-v09-verification/local-2026-06-18/logs/pytest-approve-episode.txt` |
| `make verify-all` | **PASS** | `evidence/us-v09-verification/local-2026-06-18/logs/verify-all.txt` |

---

## Olares results — **PASS (FAIL=0)**

| Gate | Primary | Supplement | Final | Evidence |
|------|---------|------------|-------|----------|
| V09-01 Alembic | PASS | — | **PASS** | `logs/e2e-olares.log` |
| V09-02 Narration | PASS | — | **PASS** | `logs/e2e-olares.log` |
| V09-03 Governance | PASS | — | **PASS** | `logs/e2e-olares.log` |
| V09-04 Platform path | FAIL | **PASS** | **PASS** | `platform-manifest.json`, run `d71d9c82-…` |
| Drift | PASS | — | **PASS** | `logs/drift.log` |

**Authoritative run:** `d71d9c82-d847-4bfc-b11e-14ccc1d310a4` — episode 64, 2-scene, manifest **v5**, character snapshot length **1**.

**Primary failure:** SEV-3 verification defect BUG-P8-01 (`jsonb_array_length` on JSON column). Supplement attestation **PASS** per VERIFICATION-STANDARDS §2.8.

Full matrix: `evidence/us-v09-verification/olares-2026-06-18/PASS-FAIL-MATRIX.md`

---

## Debt closed in US-V09

| ID | Resolution |
|----|------------|
| TD-P75-02 | `verify_all.ps1` through Phase 7.5 |
| TD-P75-01 | `olares_deploy_common.sh` pod recycle |
| TD-P6.5-03 | Manifest-driven drift |
| TD-P6.5-04/05/07 | `verify_common.sh` backport |
| TD-P6.5-01 | Optional `episode_id` on approve |
| TD-P6.5-02 | Superseded by TD-P75-02 |

---

## Sign-off

| Role | Decision |
|------|----------|
| Verification Lead | **US-V09 ACCEPTED** |
| Release Manager | **GO** for `v0.18.0-phase8-consolidation` |
| Operations Architect | Olares Alembic **0007**, platform path attested |

**No open SEV-1 or SEV-2.**

---

## References

- [PHASE-8-CONSOLIDATION-CLOSURE.md](PHASE-8-CONSOLIDATION-CLOSURE.md)
- [OPS-02-GPU-BURST-PILOT.md](OPS-02-GPU-BURST-PILOT.md)
- [UPDATED-TECHNICAL-DEBT-REGISTER.md](UPDATED-TECHNICAL-DEBT-REGISTER.md)
