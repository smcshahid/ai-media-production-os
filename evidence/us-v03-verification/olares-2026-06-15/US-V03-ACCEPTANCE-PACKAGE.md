# US-V03 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-15  
**Baseline:** `v0.11.0-us21`  
**Images:** `aimpos-api:us21` · `aimpos-worker:us21`  
**Olares integrated verify:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## 1. Executive summary

| Check | Result | Evidence |
|---|---|---|
| Path A fresh E2E (US-V02) | **PASS** | `logs/usv03-verify.log` · COMPLETED at VIDEO |
| US-20 Lineage Viewer | **PASS** | `FAIL=0` · DISPLAY_CHAIN=PASS |
| US-22 Asset History API | **PASS** | `FAIL=0` · SQL/API row parity |
| US-23 Asset History UI | **PASS** | US23_INLINE=PASS · local EC-23-01 |
| US-21 Realtime Updates | **PASS** | `WS_SMOKE=PASS` · POLL http=200 |
| Cross-feature XF-01..06 | **PASS** | `phase2-cross.log` excerpt in master log |
| Path B reference project | **PASS** | `PATH_B FAIL=0` |
| Phase 1 regression (D-37..D-54) | **PASS** | Export · D-51 · worker restart |
| Defect clearance | **PASS** | 0 unresolved S1/S2 |

**Closure recommendation:** **READY** — M7 Phase 2 sign-off may proceed.

---

## 2. Preconditions

| Field | Value |
|---|---|
| Host | `olares@10.0.0.34` |
| Namespace | `aimpos-mwayolares` |
| API / Worker images | `us21` |
| Local gate | API 111 passed · Web 36 passed · build PASS |
| Verify scripts | `deploy/k8s/usv03-verify/` |
| Path A project | `0c98583a-0520-43c9-b811-8bbdf936cc34` |
| Path A run | `0728f2d6-b53b-48f1-ad6f-1cd32f56057e` |

---

## 3. Test execution summary

| Phase | Description | Result |
|---|---|---|
| PF | Preflight (health, images, ffmpeg) | PASS |
| B | US-V02 normative E2E on fresh project | PASS |
| C | US-20 / US-22 / US-21 / US-23 attestation | PASS |
| XF | Cross-feature matrix XF-01..06 | PASS |
| DR | Worker restart durability | PASS |
| D | Path B reference project supplemental | PASS |

**Wall-clock (Path A E2E):** ~4 minutes (2026-06-15T01:31:23 → 01:35:10 UTC)

---

## 4. Metrics

| Metric | Value |
|---|---|
| Story gate latency | 30 s (SC-V07) |
| Export ZIP size | 1,550,430 bytes |
| Export file count | 9 |
| History API rows | 15 (SQL = API) |
| Lineage API edges | 18 (SQL = API) |
| Lineage nodes | 8 (incl. 4 STORYBOARD frames) |
| STORYBOARD→VIDEO edges | 4 |
| Global asset_versions (no writes) | 145 before/after Phase 2 suite |
| API unit tests (local) | 111 passed |
| Web unit tests (local) | 36 passed |

---

## 5. PASS/FAIL results

### EC-P2 overall

| ID | Criterion | Result |
|---|---|---|
| EC-P2-01 | Fresh E2E COMPLETED | **PASS** |
| EC-P2-02 | Export integrity | **PASS** |
| EC-P2-03 | Phase 1 regression | **PASS** |
| EC-P2-04 | All story exits | **PASS** |
| EC-P2-05 | Cross-feature matrix | **PASS** |
| EC-P2-06 | Worker durability | **PASS** |
| EC-P2-07 | Local regression gate | **PASS** |
| EC-P2-08 | No pipeline drift | **PASS** |
| EC-P2-09 | Orchestrator FAIL=0 | **PASS** |
| EC-P2-10 | Acceptance package | **PASS** |
| EC-P2-11 | No open S1/S2 | **PASS** |

### Per-story

| Story | Exit | Result |
|---|---|---|
| US-20 | EC-20-01..08 | **PASS** |
| US-22 | EC-22-01..09 | **PASS** |
| US-23 | EC-23-01..09 | **PASS** |
| US-21 | EC-21-01..09 | **PASS** (WS smoke + poll; gate latency spot-check per US-21 pattern) |

---

## 6. Cross-feature validation (XF-01..06)

| ID | Result | Detail |
|---|---|---|
| XF-01 | **PASS** | All lineage asset IDs present in history |
| XF-02 | **PASS** | history=15 ≥ lineage_nodes=8 |
| XF-03 | **PASS** | Export manifest hashes verified |
| XF-04 | **PASS** | REST status=COMPLETED at attestation |
| XF-05 | **PASS** | lineage/history/export HTTP 200 |
| XF-06 | **PASS** | asset_versions count unchanged |

Path B cross-feature on reference project: **PASS** (XF_FAIL=0).

---

## 7. Regression results

| Check | Result |
|---|---|
| D-51 STORYBOARD approve ≠ COMPLETED | **PASS** (`POST_SB_STATUS=AWAITING_APPROVAL`) |
| D-51 COMPLETED at VIDEO approve | **PASS** |
| D-52 export 9 files + 409 negative | **PASS** |
| D-53 manifest hash verify | **PASS** |
| D-54 BUNDLE_EXPORTED audit | **PASS** |
| SC-F05 / SC-V06 worker restart | **PASS** |
| US-V02 reference project (Path B) | **PASS** |

---

## 8. Decision record attestation (D-55..D-59)

| ID | Result | Evidence |
|---|---|---|
| D-55 Lineage API | **PASS** | API/SQL edge parity |
| D-56 Lineage UI scope | **PASS** | Synthetic IDEA; read-only API |
| D-57 Asset history API | **PASS** | Stage groups; newest-first |
| D-58 Asset history UI | **PASS** | Content-read; local `/history` route |
| D-59 Realtime channel | **PASS** | WS_SMOKE=PASS; poll fallback; Redis ok |

---

## 9. Defect register

| ID | Severity | Class | Status | Detail |
|---|---|---|---|---|
| VERIFY-V03-001 | S3 | Verification | **Resolved** | S-11 SCRIPT approve race on first run; fixed via `approve_stage` retry in `verify_e2e.sh` |

**No product defects.** **No unresolved S1 or S2.**

---

## 10. Final acceptance recommendation

**READY for M7 — Spark Full Phase 2 signed.**

All mandatory PASS conditions satisfied:
- Olares `FAIL=0`
- XF-01..06 PASS
- EC-P2-01..11 PASS
- Acceptance package generated
- Path A complete on fresh project
- Zero unresolved Severity-1/2 defects
