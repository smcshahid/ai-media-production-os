# US-V01 Acceptance Package — Olares Verification

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-11  
**Baseline:** `v0.3.6-us17` (`aimpos-api:us17`, `aimpos-worker:us17`)  
**Project:** `fa5485c3-05d3-4b71-b9ef-39ca7339da47` (fresh)  
**Run:** `efdc8200-f5a4-448a-be83-6e05c05586fd`  
**Amendment:** A-01 (D-47 extension S-12a/b)  
**Verify log:** `logs/usv01-verify.log` · **Metadata:** `metadata.json`

---

## 1. Verification summary

| Check | Result |
|---|---|
| Local regression (API 81 / worker 36 / web 23) | **PASS** |
| Verify scripts implemented | **PASS** — `deploy/k8s/usv01-verify/` |
| Olares E2E S-00..S-16 + A-01 | **PASS** |
| Issue 43 AC-1..AC-9 | **PASS** |
| SC-V01..SC-V08 | **PASS** |
| D-37..D-47 incl. V-47 | **PASS** |
| Worker restart durability (SC-V06) | **PASS** |

**Closure recommendation:** **ACCEPT** — Visual MVP acceptance gate satisfied. Recommend M5 sign-off.

---

## 2. Environment

| Field | Value |
|---|---|
| API ClusterIP | `http://10.233.21.231:8000` |
| API image | `docker.io/library/aimpos-api:us17` |
| Worker image | `docker.io/library/aimpos-worker:us17` |
| Health | postgres, redis, minio **ok** |
| ComfyUI | Launcher probe `unreachable` at start; storyboard batches v1/v2 both produced 4 frames (ComfyUI operational during run) |
| Project bootstrap | `create_project.sh` psql INSERT (no `POST /projects` API — verify infrastructure only) |
| Run start | 2026-06-11T06:19:47+00:00 |
| Terminal status | **COMPLETED** |

---

## 3. Issue 43 acceptance criteria

| AC | Requirement | Evidence | Result |
|---|---|---|---|
| AC-1 | Fresh project | PF-05 `PROJECT=fa5485c3-…` | **PASS** |
| AC-2 | Start pipeline | S-03 HTTP 201, `RUN_ID=efdc8200-…` | **PASS** |
| AC-3 | Story edit + approve | S-05 human-edit v2 branch; S-06 STORY/APPROVED | **PASS** |
| AC-4 | Script reject/regen/approve | S-08 REJECT; S-09 regen; S-11 APPROVED; 2 SCRIPT versions | **PASS** |
| AC-5 | Approve all storyboard frames | S-14 STORYBOARD/APPROVED on v2 batch (4 frames) | **PASS** |
| AC-6 | COMPLETED terminal | V-01 `status=COMPLETED`; DR-06 polls confirm | **PASS** |
| AC-7 | 4+ approvals + 3+ model calls | V-02 (5 approvals); V-07 (5 agent completions) | **PASS** |
| AC-8 | Lineage idea → frames | V-06 STORY→SCRIPT (2), SCRIPT→STORYBOARD (8) | **PASS** |
| AC-9 | Worker restart durability | S-15 DR-01..06; status stable COMPLETED post-restart | **PASS** |

---

## 4. Scope Freeze SC attestation

| SC | Requirement | Evidence | Result |
|---|---|---|---|
| SC-V01 | Complete pipeline | V-01 COMPLETED + STORYBOARD approved | **PASS** |
| SC-02 | Local inference | V-07 all `model_id=qwen3:14b` | **PASS** |
| SC-V03 | 3/3 human gates | V-02 STORY, SCRIPT, STORYBOARD decisions | **PASS** |
| SC-V04 | Versioned assets | STORY v2 human-edit; SCRIPT v1–2; STORYBOARD 8 rows (2×4) | **PASS** |
| SC-V05 | Audit completeness | V-07 five AGENT_TASK_COMPLETED events | **PASS** |
| SC-V06 | Durability post-restart | `logs/worker-restart.log` DR-06 ×3 COMPLETED | **PASS** |
| SC-V07 | Time to first story | `T_STORY_GATE` delta **30s** (< 5 min) | **PASS** |
| SC-V08 | Comprehension (API path) | Full normative path via curl; no UI required for attestation | **PASS** |

---

## 5. D-37..D-47 validation matrix

| ID | Decision | Step | Evidence | Result |
|---|---|---|---|---|
| D-37 | Approved story, no branch promotion | S-05, S-06 | STORY v2 `human-edit`; no new STORY on approve | **PASS** |
| D-38 | Append-only ai-draft regen | S-09 | V-04 two distinct SCRIPT hashes | **PASS** |
| D-39 | `script.fountain` semantics | S-07, S-11 | SCRIPT stored; lineage STORY→SCRIPT | **PASS** |
| D-40 | Fountain validation | S-07, S-11 | SCRIPT persisted without error | **PASS** |
| D-41 | Approved script, no promotion | S-11 | No SCRIPT insert on approve | **PASS** |
| D-42 | Script regen inputs | S-08, S-09 | Regen after SCRIPT reject with note | **PASS** |
| D-43 | Storyboard frame contract | S-12, S-12c | Shared version; frame_index 1..4 per batch | **PASS** |
| D-44 | Batch completeness | S-12, S-12c | Exactly 4 frames per version; no orphans | **PASS** |
| D-45 | Frame count = 4 | S-12, S-12c | V-05: v1=4, v2=4 | **PASS** |
| D-46 | Approved batch, no promotion | S-14 | Rows 8 before/after S-14 | **PASS** |
| D-47 | Storyboard regen inputs | S-12a, S-12b | V-47 v1 intact; regen audit count=1 | **PASS** |

---

## 6. Amendment A-01 / V-47 attestation

| Check | Expected | Observed | Result |
|---|---|---|---|
| STORYBOARD v1 frames | 4 | SB_V1=1 frames=4 | **PASS** |
| STORYBOARD reject note | Non-empty rationale | `US-V01 A-01: increase contrast and wider establishing shots.` | **PASS** |
| STORYBOARD regen | HTTP 200 | S-12b `regenerations_used=1` | **PASS** |
| STORYBOARD v2 frames | 4 | SB_V2=2 frames=4 | **PASS** |
| v1 hashes intact post-regen | Identical to S-12 snapshot | V-47 inline PASS | **PASS** |
| PNG content-read | HTTP 200 | S-13 bytes=333051 | **PASS** |
| REGENERATION_REQUESTED audit | ≥1 STORYBOARD | V-47 count=1 | **PASS** |

v1 content hashes (unchanged after regen): see `sql/v47-d47-extension.txt`.

---

## 7. Worker restart durability (SC-V06)

Procedure executed per verification plan §6 after S-14 approve.

| Step | Observation |
|---|---|
| DR-01 baseline | `AWAITING_APPROVAL` (async approve signal in flight — platform transitioned to COMPLETED ~5s later) |
| DR-03 restart | `kubectl rollout restart deployment/aimpos-worker` — success |
| DR-06 polls | All three polls: `status=COMPLETED`, `current_stage=null`, same `run_id` |

**SC-V06: PASS** — see `logs/worker-restart.log`.

---

## 8. Deferred items (T-V01-03)

Video (US-18), export (US-19), lineage UI (US-20), asset history (US-22/23), multi-project, Keycloak, WebSocket — **Deferred** per Scope Freeze. Not required for Visual MVP acceptance.

---

## 9. Local regression baseline

| Suite | Result | Log |
|---|---|---|
| API unit | 81 passed | `../local-2026-06-11/logs/pytest-api-baseline.txt` |
| Worker unit | 36 passed | `../local-2026-06-11/logs/pytest-worker-baseline.txt` |
| Web unit | 23 passed | `../local-2026-06-11/logs/vitest-baseline.txt` |

---

## 10. Non-blocking observations

| ID | Class | Detail | Impact |
|---|---|---|---|
| INFRA-V01-001 | Infrastructure | SSH to Olares initially hung; later restored | **Resolved** — run completed |
| VERIFY-V01-001 | Verify script | S-14 polled once before async approve completed; script exit `FAIL=1` | **Non-blocking** — V-01/DR-06 confirm COMPLETED; poll loop fixed in `verify_usv01.sh` |
| PF-03 | ComfyUI probe | Launcher POST failed at script start | **Non-blocking** — both storyboard batches generated successfully |

No product defects discovered. No platform changes required.

---

## 11. M5 sign-off

**M5 Visual MVP signed:** **RECOMMENDED ACCEPT**

All Issue 43 ACs, SC-V01..SC-V08, and D-37..D-47 (including Amendment A-01 / V-47) are satisfied on Olares with baseline `v0.3.6-us17`. Proposed release tag: **`v0.4.0-usv01`**.
