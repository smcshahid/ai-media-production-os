# Release Readiness Recommendation — Phase 7 Character Bible Pilot

**Date:** 2026-06-18  
**Release:** `v0.17.0-phase7-character-bible`  
**Baseline:** `v0.16.0-phase6-episode`  
**SCR:** SCR-2026-005 (ACCEPTED)  
**Acceptance:** US-V08 **ACCEPTED**

---

## Recommendation

**RELEASE READY WITH CONDITIONS** — Olares attestation complete (PATH A–E PASS with C1 supplemental). Authorized for annotated tag **`v0.17.0-phase7-character-bible`**.

---

## Final PASS/FAIL matrix

| Path | Scope | Olares | Final |
|------|-------|--------|-------|
| **PATH A** | 1 character, 1 episode → manifest v5 | PASS | **PASS** |
| **PATH B** | 3 characters, 3 scenes → manifest v5 | PASS | **PASS** |
| **PATH C1** | Multi-episode ep 1 (supplement) | PASS | **PASS** |
| **PATH C2** | Multi-episode ep 2 | PASS | **PASS** |
| **PATH D** | Legacy v1–v4 | PASS | **PASS** |
| **PATH E** | Platform regression | PASS | **PASS** |
| **Local automated** | Core + API + worker + web | PASS | **PASS** |

Evidence: `evidence/us-v08-verification/olares-2026-06-18/`

---

## Conditions

| ID | Severity | Condition |
|----|----------|-----------|
| TD-P7-01 | SEV-3 | Document that manifest v5 requires character rows at export (not just `character_ids` on run) |
| OPS-V08-01 | SEV-4 | Olares E2E must use single flock; supplemental paths via `USV08_ONLY_PATH` |

No unresolved SEV-1 or SEV-2.

---

## Migration notes

1. Run `alembic upgrade head` (revision **0006**).
2. Creates `characters` table and `pipeline_runs.character_ids`.
3. Existing projects unchanged until characters created and selected at pipeline start.
4. Olares: `deploy/k8s/usv08-verify/migrate_0006_olares.sh`

---

## Deployment checklist

| Step | Status |
|------|--------|
| Apply Alembic 0006 | **DONE** (Olares) |
| Deploy `usv08-phase7` images | **DONE** (Olares) |
| `verify_phase7_local.ps1` | **PASS** |
| `verify_usv08_e2e.sh` Paths A–E | **PASS** |
| Evidence archived | **DONE** |
| Git tag `v0.17.0-phase7-character-bible` | **AUTHORIZED** |

---

## Release decision

**B. RELEASE READY WITH CONDITIONS** — Product pilot validated on Olares; C1 supplemental attestation and SEV-3 export snapshot note tracked for Phase 8.
