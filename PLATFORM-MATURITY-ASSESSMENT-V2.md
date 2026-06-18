# Platform Maturity Assessment V2

**Date:** 2026-06-18  
**Mission:** Phase 8 Platform Consolidation  
**Baseline:** `v0.17.1-phase7-character-hardening`  
**Supersedes:** `PLATFORM-MATURITY-ASSESSMENT.md` (Phase 6.5)

---

## Scoring model (1–5)

| Score | Label |
|-------|-------|
| 5 | Optimized — consolidated, measured, low defect rate |
| 4 | Managed — evidence-backed, minor gaps |
| 3 | Defined — documented, partial automation |
| 2 | Repeatable — scripts exist, drift common |
| 1 | Ad hoc |

**Overall maturity V2:** **4.3 / 5** (up from **3.5 / 5** at Phase 6.5)

---

## Dimension scores

### Product maturity — **4.3 / 5** (+0.3)

| Criterion | V1 | V2 | Notes |
|-----------|----|----|-------|
| Core pipeline | 5 | 5 | Stable |
| Multi-scene / narration / episode | 4 | 4 | US-V05–V07 |
| Character bible + snapshot | — | **4** | US-V08/V08B |
| Export v1–v5 ladder | 5 | **5** | US-V09 unit attestation |
| Deferred creator domains | 2 | 2 | Intentionally bounded |

### Operational maturity — **4.0 / 5** (+0.8)

| Criterion | V1 | V2 | Notes |
|-----------|----|----|-------|
| verify-all consolidation | 2 | **5** | `make verify-all` Phases 3B–7.5 |
| Runbooks | 3 | **4** | Phase 8 refresh |
| Evidence discipline | 4 | **4** | US-V09 package |
| Technical debt visibility | 4 | **5** | Updated register |

### Deployment maturity — **4.2 / 5** (+0.7)

| Criterion | V1 | V2 | Notes |
|-----------|----|----|-------|
| Olares deploy repeatability | 4 | **4** | Pod recycle pattern |
| Drift detection accuracy | 2 | **4** | Manifest-driven (acceptance override documented) |
| Migration discipline | 4 | **5** | Alembic **0007** on Olares |

### Verification maturity — **4.5 / 5** (+1.1)

| Criterion | V1 | V2 | Notes |
|-----------|----|----|-------|
| Shared verification library | — | **5** | `verify_common.sh` |
| Concurrency safety | 3 | **4** | Backported flock/cancel |
| End-to-end verify-all | 2 | **5** | Phase 8 closure |
| US-V09 platform attestation | — | **5** | Local FAIL=0; Olares supplement PASS manifest v5 |

### GPU / burst readiness — **3.5 / 5** (new)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Study completeness | 5 | GPU Burst Study closed |
| Pilot package | 4 | OPS-02 ready |
| Implementation | 1 | Not authorized (correct) |

---

## Verification improvements (Phase 8)

- `deploy/k8s/lib/verify_common.sh` — flock, Temporal terminate, retry, supplemental helpers
- US-V05–V08B Olares scripts backported
- `deploy/dev/verify_usv09_local.ps1` — export ladder + verify-all
- Episode-scoped approve test coverage

---

## Deployment improvements (Phase 8)

- `deploy/k8s/lib/olares_deploy_common.sh`
- `scripts/release/load-manifest-env.sh` absolute-path fix
- `check_drift.sh` requires manifest-sourced `EXPECTED_ALEMBIC`

---

## GPU pilot readiness assessment

| Item | Ready |
|------|-------|
| Cost model | **YES** |
| Runtime targets | **YES** |
| Governance controls | **YES** |
| OPS-02 procedures | **YES** |
| Burst implementation | **NO** (deferred) |

**Verdict:** Platform ready for optional **OPS-02 GPU Burst Pilot** mission; not required for consolidation baseline.

---

## Roadmap recommendation

| Priority | Phase | Rationale |
|----------|-------|-----------|
| 1 (optional) | GPU Burst Pilot | OPS-02 package ready; runtime ROI validated in study |
| 2 (SCR) | Publishing | Creator-facing; deferred |
| 3 (SCR) | Multi-project + RBAC | Foundation for collaboration |

**Maintain** consolidation baseline (`v0.18.0`) until explicit governance authorizes next domain SCR.

---

## References

- [PHASE-8-CONSOLIDATION-CLOSURE.md](PHASE-8-CONSOLIDATION-CLOSURE.md)
- [OPS-02-GPU-BURST-PILOT.md](OPS-02-GPU-BURST-PILOT.md)
- [UPDATED-TECHNICAL-DEBT-REGISTER.md](UPDATED-TECHNICAL-DEBT-REGISTER.md)
