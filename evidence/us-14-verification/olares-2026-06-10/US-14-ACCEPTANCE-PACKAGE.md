# US-14 Acceptance Package — Olares Verification

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-10 / 2026-06-11 UTC  
**API image:** `docker.io/library/aimpos-api:us09` (unchanged)  
**Worker image:** `docker.io/library/aimpos-worker:us14`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Run:** `ad45f3a7-e772-437b-be00-c62a9121cec1`  
**Verify log:** `logs/us14-verify.log` · **Temporal history:** `logs/temporal-history.txt`  
**Implementation report:** `docs/sprints/sprint-3e-us14-implementation-report.md`

---

## Verification summary

| Check | Result |
|---|---|
| V-01 — Fountain content sample (1 scene, dialogue) | **PASS** |
| V-02 — SCRIPT `asset_versions` row | **PASS** |
| V-03 — MinIO `mc stat` on script key | **PASS** |
| V-04 — Validator pass (successful store) | **PASS** |
| V-05 — `lineage_edges` story → script | **PASS** |
| V-06 — `GET /pipeline/status` → `AWAITING_APPROVAL`/`SCRIPT` | **PASS** |
| V-07 — Worker log `script_agent_completed` (`qwen3:14b`) | **PASS** |
| V-08 — Temporal history: `run_script_agent` after STORY approve | **PASS** |

**Closure recommendation:** **ACCEPT**

---

## Test gates before deployment

| Suite | Result |
|---|---|
| Worker unit | 16 passed |
| API unit | 76 passed (regression) |
| Web unit | 14 passed (regression) |

Logs: `evidence/us-14-verification/local-2026-06-10/logs/`

---

## Stale-run cleanup (documented deviation)

The US-09 post-fix run `980617a8-…` was left at `AWAITING_APPROVAL`/`SCRIPT` under the **stub** workflow. Deploying `aimpos-worker:us14` changed the SCRIPT activity type from `run_stub_stage` to `run_script_agent`, causing `TMPRL1100` nondeterminism on replay. That run was marked **`CANCELLED`** in `pipeline_runs` (`deploy/k8s/us14-verify/cancel_stale_run.sh`) before starting run `ad45f3a7-…`. This is expected when swapping stub activities for real agents on in-flight workflows.

---

## Setup — fresh pipeline

```
POST /ideas      → IDEA v7 (US-14 Olares Verify)
POST /pipeline/start → run ad45f3a7-e772-437b-be00-c62a9121cec1, RUNNING/STORY
poll             → AWAITING_APPROVAL / STORY (Story Architect v9)
```

Story asset for this run: `c2fc462f-a92e-43e8-bcdd-2110de40b351` (STORY v9, ai-draft).

---

## V6-prep — Approve STORY

```
POST /pipeline/approve {"stage":"STORY","decision":"APPROVED"}
HTTP 200 → approval_id 1a9390c1-febc-407b-b28c-9718019555a4
```

---

## V6 — SCRIPT review gate

```
GET /pipeline/status
→ status=AWAITING_APPROVAL, current_stage=SCRIPT
```

| Field | Value |
|---|---|
| run_id | `ad45f3a7-e772-437b-be00-c62a9121cec1` |
| status | `AWAITING_APPROVAL` |
| current_stage | `SCRIPT` |
| updated_at | `2026-06-11T00:04:52.551693` |

---

## V-02 / AC-2 / AC-3 — SCRIPT asset

```
e96cae0b-29f5-4bdb-b26b-f95efeee175b|1|ai-draft|true|79528e51…|ba0c4636-…/SCRIPT/79528e51…
```

| Field | Value |
|---|---|
| asset_version_id | `e96cae0b-29f5-4bdb-b26b-f95efeee175b` |
| stage | `SCRIPT` |
| version | **1** (first script for project) |
| branch | `ai-draft` |
| is_ai_generated | `true` |
| content_hash | `79528e514e83d547e2ec35687c02c625ceb69ce80996716596770ffc9e5c2a4d` |

---

## V-03 — MinIO stat

```
Name: 79528e514e83d547e2ec35687c02c625ceb69ce80996716596770ffc9e5c2a4d
Size: 1.0 KiB
Content-Type: text/plain; charset=utf-8
```

Bucket: `aimpos-hot-assets`

---

## V-01 / AC-1 — Fountain sample (excerpt)

```
INT. RESEARCH LAB - DAWN

The lab is dimly lit, equipment humming. DR. ELARA VOSS (30s, weary but focused) …

DR. ELARA VOSS
(whispering)
If I send this... they'll come. But if I don't—

DR. MARCUS HALE
(voiceover)
You think silence protects them? It protects *you*.
```

Single scene heading (`INT. RESEARCH LAB - DAWN`); multiple dialogue blocks. Title-page metadata lines present above the heading (allowed by validator).

---

## V-05 / AC-4 — Lineage edge

```
c2fc462f-a92e-43e8-bcdd-2110de40b351|e96cae0b-29f5-4bdb-b26b-f95efeee175b|STORY|SCRIPT
```

Parent: STORY v9 (`c2fc462f-…`) → Child: SCRIPT v1 (`e96cae0b-…`).

---

## V-07 — Worker evidence

```
script_agent_completed
  workflow_id: spark-pipeline-ad45f3a7-e772-437b-be00-c62a9121cec1
  activity_id: 5
  asset_version_id: e96cae0b-29f5-4bdb-b26b-f95efeee175b
  model_id: qwen3:14b
  duration_ms: 11179
```

Also: `story_agent_completed` (activity 2) for STORY stage on same workflow.

---

## Audit chain (SCRIPT stage)

```
STAGE_STARTED      @00:04:41 → agent.screenwriter, stage=SCRIPT
AGENT_TASK_COMPLETED @00:04:52 → qwen3:14b, asset_version_id=e96cae0b-…, branch=ai-draft
ASSET_STORED       @00:04:52 → stage=SCRIPT, version=1, content_hash=79528e51…
```

STORY approval row: `STORY|APPROVED` @ `2026-06-11 00:04:41.237566`

---

## V-08 — Temporal history (excerpt)

After STORY approval signal, workflow schedules:

1. `sync_pipeline_status` → `RUNNING` / `SCRIPT`
2. **`run_script_agent`** (activity id 5, 5m timeout)
3. `sync_pipeline_status` → `AWAITING_APPROVAL` / `SCRIPT`

Full history: `logs/temporal-history.txt`

---

## D-40 attestation

Validator rules enforced before store (unit tests + successful Olares store):

- Fail when `scene_heading_count == 0`
- Fail when `scene_count != 1`
- Fail when `dialogue_count == 0`

Unit coverage: `worker/tests/unit/test_fountain_validate.py` (6 tests).

---

## Scope attestation

| In scope | Delivered |
|---|---|
| Screenwriter agent | ✅ |
| Fountain validator (D-40) | ✅ |
| SCRIPT asset (D-39) | ✅ |
| Lineage edge | ✅ |
| Workflow swap | ✅ |
| D-37 story resolution | ✅ |

| Out of scope | Status |
|---|---|
| API changes | None |
| Schema migrations | None |
| SCRIPT regenerate | 501 unchanged |
| Review UI | Deferred US-15 |
| Storyboard / video / export | Not touched |

---

## Formal closure request

All five Visual MVP ACs are evidenced on Olares with regression suites green. **Recommend ACCEPT** for US-14 formal closure review.
