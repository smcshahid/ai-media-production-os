# Sprint 3I — US-V01 Verification Report

**Date:** 2026-06-11  
**Status:** **PASS — Olares E2E complete**  
**Parent brief:** `docs/sprints/sprint-3i-usv01-brief.md` (ACCEPTED WITH AMENDMENT A-01)  
**Verification plan:** `docs/sprints/sprint-3i-usv01-verification-plan.md` (APPROVED)  
**Baseline:** `v0.3.6-us17`  
**Acceptance package:** `evidence/us-v01-verification/olares-2026-06-11/US-V01-ACCEPTANCE-PACKAGE.md`

---

## 1. Summary

US-V01 Visual MVP acceptance verification is **complete**. Verify scripts were implemented, local regression passed, and the full normative Olares E2E path (including Amendment A-01 storyboard reject/regen) executed successfully. **No product code** was changed.

| Deliverable | Status |
|---|---|
| `deploy/k8s/usv01-verify/` scripts | ✅ Complete |
| Local regression gate | ✅ 81 / 36 / 23 PASS |
| Olares E2E S-00..S-16 + A-01 | ✅ PASS |
| SQL attestation | ✅ Inline S-16 + `sql/` files |
| Acceptance package | ✅ PASS |
| M5 sign-off recommendation | ✅ ACCEPT |

**Run identifiers:** Project `fa5485c3-05d3-4b71-b9ef-39ca7339da47` · Run `efdc8200-f5a4-448a-be83-6e05c05586fd`

---

## 2. Verify script implementation

| File | Steps covered |
|---|---|
| `prep_comfyui.sh` | S-00 / PF-03 |
| `create_project.sh` | PF-05 fresh project (psql bootstrap) |
| `verify_usv01.sh` | S-02..S-16, A-01 S-12a/b, inline V-01..V-07, V-47, SC-V06 |
| `collect_usv01.sh` | Full SQL attestation to `sql/` |
| `run_remote.sh` | Secrets, orchestration, logging |

**Normative path executed:** STORY human edit → SCRIPT reject/regen → STORYBOARD v1 → **A-01 reject/regen** → approve v2 → COMPLETED → worker restart.

---

## 3. Local test results

| Suite | Result |
|---|---|
| API unit | **81 passed** |
| Worker unit | **36 passed** |
| Web unit | **23 passed** |

Logs: `evidence/us-v01-verification/local-2026-06-11/logs/`

---

## 4. Olares execution results

| Step | Result | Notes |
|---|---|---|
| PF-01 images | PASS | `aimpos-api:us17`, `aimpos-worker:us17` |
| PF-03 ComfyUI | WARN | Launcher POST failed; batches still generated |
| PF-04 health | PASS | All dependencies ok |
| PF-05 fresh project | PASS | New UUID |
| S-04 STORY gate | PASS | 30s from start (SC-V07) |
| S-05..S-11 STORY/SCRIPT gates | PASS | Human edit, reject/regen, approve |
| S-12 STORYBOARD v1 | PASS | 4 frames |
| S-12a/b A-01 | PASS | Reject + regen → v2 (4 frames) |
| S-13 PNG read | PASS | HTTP 200, 333051 bytes |
| S-14 COMPLETED | PASS | V-01 + DR-06 confirm (async ~5s delay) |
| S-15 worker restart | PASS | SC-V06 stable COMPLETED |
| S-16 SQL attestation | PASS | All V-01..V-07, V-47 checks |

Full log: `evidence/us-v01-verification/olares-2026-06-11/logs/usv01-verify.log`

---

## 5. Defect classification

| ID | Severity | Class | Status | Detail |
|---|---|---|---|---|
| INFRA-V01-001 | Blocker (transient) | Infrastructure — Olares SSH | **Resolved** | SSH hung during initial attempt; restored before successful run |
| VERIFY-V01-001 | Non-blocking | Verify script timing | **Fixed** | S-14 single poll before async approve; script reported FAIL=1 while platform reached COMPLETED. Poll loop added to `verify_usv01.sh`. |

**No product defects.** No API/worker/web changes authorized or required.

---

## 6. D-37..D-47 / AC / SC attestation

All checks **PASS** — see acceptance package §3–§6 and `sql/` evidence files.

Highlights:

- **5 approvals:** STORY/APPROVED, SCRIPT/REJECTED, SCRIPT/APPROVED, STORYBOARD/REJECTED, STORYBOARD/APPROVED
- **5 agent completions:** story×1, script×2, cinematography×2 — all `qwen3:14b`
- **8 STORYBOARD rows:** v1=4, v2=4; D-46 row count stable on final approve
- **V-47:** v1 hashes intact; 1 STORYBOARD regen audit event

---

## 7. Governance recommendation

**Recommend ACCEPT** for US-V01 closure and **M5 Visual MVP sign-off**.

Proposed tag: **`v0.4.0-usv01`** (verification-only milestone; no product delta from `v0.3.6-us17`).

---

## 8. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial report — Olares blocked |
| 2.0 | 2026-06-11 | Olares PASS — full attestation |
