# Release Evidence — v0.18.0-phase8-consolidation

**Date:** 2026-06-18  
**Release:** `v0.18.0-phase8-consolidation`  
**Baseline:** `v0.17.1-phase7-character-hardening`  
**Acceptance:** US-V09 **ACCEPTED**

---

## Pre-release gates

| Gate | Result | Evidence |
|------|--------|----------|
| US-V09 local | **FAIL=0** | `evidence/us-v09-verification/local-2026-06-18/` |
| US-V09 Olares | **FAIL=0** | `evidence/us-v09-verification/olares-2026-06-18/` |
| PASS/FAIL matrix | **Final PASS** | `evidence/us-v09-verification/olares-2026-06-18/PASS-FAIL-MATRIX.md` |
| Alembic head | **0007** | unchanged |
| SEV-1 / SEV-2 | **None** | PASS-FAIL matrix |

---

## Olares authoritative run

| Field | Value |
|-------|-------|
| Run ID | `d71d9c82-d847-4bfc-b11e-14ccc1d310a4` |
| Episode | 64 |
| Scenes | 2 |
| Manifest | **v5** |
| Snapshot | length **1** |

Artifacts: `evidence/us-v09-verification/olares-2026-06-18/platform-export.zip`, `platform-manifest.json`

---

## Phase 8 deliverables

- verify_all modernization (Phases 4–7.5)
- verify_common.sh + olares_deploy_common.sh
- Manifest-driven drift
- Episode-scoped approve
- OPS-02 pilot package (no implementation)

---

## Git release artifacts

| Field | Value |
|-------|-------|
| Tag | `v0.18.0-phase8-consolidation` |
| Remote | `origin/main` |
