# Phase 8 — Platform Consolidation Governance Brief

**Date:** 2026-06-18  
**Baseline:** `v0.17.1-phase7-character-hardening`  
**Mission:** Platform consolidation & verification modernization  
**Status:** **AUTHORIZED**

---

## Current platform state

| Capability | Status | Evidence |
|------------|--------|----------|
| Core pipeline (IDEA→VIDEO) | **Operational** | US-V02+ lineage |
| Multi-scene (1–3) | **Operational** | US-V05 ACCEPTED |
| Audio narration | **Operational** | US-V06 ACCEPTED |
| Episode model | **Operational** | US-V07 ACCEPTED |
| Character Bible | **Operational** | US-V08 ACCEPTED |
| Character snapshot hardening | **Operational** | US-V08B ACCEPTED |
| Export manifest ladder v1–v5 | **Operational** | Unit + Olares evidence |
| Olares deployment | **Operational** | Hybrid stack on `aimpos-mwayolares` |
| Alembic head | **0007** | `character_snapshot` |

---

## Deferred initiatives (confirmed)

The following remain **explicitly deferred** until a future SCR and governance authorization:

| Initiative | Status | Rationale |
|------------|--------|-----------|
| **Publishing** | DEFERRED | Out of scope; no creator distribution domain |
| **Multi-project** | DEFERRED | Single-project pilot sufficient for maturity phase |
| **Creator collaboration** | DEFERRED | Requires RBAC + identity model |
| **RBAC / Keycloak** | DEFERRED | No identity provider in baseline |
| Memory / RAG / Neo4j | DEFERRED | Not authorized creator domains |
| GPU burst implementation | DEFERRED | Study complete; pilot package only (OPS-02) |
| Cloud rendering | DEFERRED | Rejected in GPU Burst Study |

---

## GPU Burst Study conclusions

Study artifacts: `GPU-BURST-RECOMMENDATION.md`, `GPU-COST-MODEL.md`, `GPU-PERFORMANCE-BASELINE.md`, `PHASE-GPU-BURST-CLOSURE.md`.

| Finding | Conclusion |
|---------|------------|
| Olares-first preserved | **YES** — burst is optional adjunct |
| ≥50% runtime reduction (multi-scene GPU) | **YES** — parallel STORYBOARD / i2v |
| Recommended pilot mode | **Option B: Manual burst** (RunPod/Vast) |
| Burst scope | STORYBOARD + VIDEO (ComfyUI) only |
| Implementation in Phase 8 | **NO** — OPS-02 pilot package only |

---

## Operational priorities (Phase 8)

| Priority | Work package | Debt |
|----------|--------------|------|
| P0 | `verify_all` through Phase 7.5 | TD-P75-02, TD-P6.5-02 |
| P0 | Manifest-driven drift governance | TD-P6.5-03 |
| P1 | Shared verification library + backport | TD-P6.5-04/05/07 |
| P1 | Olares deploy pod recycle pattern | TD-P75-01 |
| P1 | Episode-scoped approve (minimal) | TD-P6.5-01 |
| P2 | US-V09 full platform re-attestation | New verification mission |
| P2 | OPS-02 GPU burst pilot package | Readiness only |
| P2 | Runbook refresh | Operational accuracy |

---

## Governance stop conditions

STOP if any of the following occur during Phase 8:

- New SCR required for scope expansion
- New creator-facing domain introduced
- GPU burst implementation requested
- Multi-project or RBAC becomes necessary mid-mission

---

## Target release (post-mission)

`v0.18.0-phase8-consolidation` upon US-V09 ACCEPTED and closure authorization.

---

## References

- [TECHNICAL-DEBT-REGISTER.md](TECHNICAL-DEBT-REGISTER.md)
- [docs/operations/VERIFICATION-STANDARDS.md](docs/operations/VERIFICATION-STANDARDS.md)
- [PHASE-7.5-CHARACTER-HARDENING-CLOSURE.md](PHASE-7.5-CHARACTER-HARDENING-CLOSURE.md)
