# Sprint 3F — US-15 Implementation Report

**Date:** 2026-06-11  
**Status:** **COMPLETE** — Olares verification PASS (`evidence/us-15-verification/olares-2026-06-11/`)  
**Baseline:** `v0.3.3-us14`  
**Governance:** `D-41`, `D-42`, `docs/sprints/sprint-3f-us15-brief.md`, `docs/sprints/sprint-3f-us15-implementation-plan.md`

---

## 1. Summary

US-15 completes the SCRIPT review gate: Fountain HTML preview, SCRIPT approve/reject/regenerate, extended content-read API, and worker regeneration with D-42 input contract. No schema migrations, no storyboard agent, no human-edit.

| Deliverable | Status |
|---|---|
| SCRIPT review mode + Fountain preview | ✅ |
| `GET /assets/{id}/content` for SCRIPT | ✅ |
| `POST /pipeline/regenerate` for SCRIPT | ✅ |
| `run_script_agent(rejection_note)` + D-42 DB rationale | ✅ |
| `fetch_approved_script` (D-41) | ✅ |
| Storyboard agent / ComfyUI | ❌ Not added (US-16) |
| SCRIPT human-edit | ❌ Not added |
| Alembic migration | ❌ Not added |

---

## 2. Decision records

### D-41 — Approved script resolution

Recorded in `DECISIONS.md`. Approved script = latest SCRIPT version + `APPROVED` `approvals` row; no branch promotion; `fetch_approved_script()` for US-16.

### D-42 — Script regeneration input contract

Recorded in `DECISIONS.md`. Regeneration inputs: **latest approved STORY** (`fetch_approved_story`) + **latest rejected SCRIPT rationale** (`fetch_latest_script_rejection_rationale`). Prior SCRIPT drafts are never fed to the agent.

---

## 3. Files changed

### API
- `api/app/routes/assets.py` — `GET /assets/{id}/content` for STORY \| SCRIPT
- `api/app/routes/pipeline.py` — SCRIPT in `_SUPPORTED_REGENERATE_STAGES`
- `api/tests/unit/test_assets_us15.py` — content-read tests
- `api/tests/unit/test_pipeline_regenerate.py` — SCRIPT regen happy path

### Worker
- `worker/app/tools/assets.py` — `fetch_approved_script`, `fetch_latest_script_rejection_rationale`
- `worker/app/temporal/activities/script.py` — D-42 input resolution
- `worker/app/agents/screenwriter/{state,graph,nodes}.py` — rejection note injection
- `worker/app/temporal/workflows/spark_pipeline.py` — pass `rejection_note` to SCRIPT activity
- `worker/tests/unit/test_screenwriter.py` — rejection note test
- `worker/tests/unit/test_script_approved.py` — D-41/D-42 helpers

### Web
- `web/src/lib/fountainFormat.ts` — Fountain → HTML formatter
- `web/src/lib/scriptReview.ts` — ai-draft SCRIPT selection
- `web/src/routes/ReviewPage.tsx` — script mode + regen
- `web/src/styles.css` — fountain preview styles
- `web/src/tests/fountainFormat.test.ts`, `scriptReview.test.ts`

### Governance / evidence
- `DECISIONS.md` — D-42 appended
- `deploy/k8s/us15-verify/` — Olares scripts
- `evidence/us-15-verification/` — test + Olares packages

---

## 4. Test results

| Suite | Result |
|---|---|
| API unit | **78 passed** (+2) |
| Worker unit | **21 passed** (+5) |
| Web unit | **20 passed** (+6) |

---

## 5. AC implementation mapping

| AC | Implementation | Evidence |
|---|---|---|
| AC-1 Fountain formatted preview | `fountainFormat.ts` + script mode UI + content-read | Unit tests + Olares Fountain sample |
| AC-2 Approve → STORYBOARD | Reuse `POST /pipeline/approve` | Olares status `AWAITING_APPROVAL`/`STORYBOARD` |
| AC-3 Reject/regenerate | API SCRIPT regen + worker D-42 + UI regen | Olares v1→v4 chain + 429 |
| AC-4 Approved version in DB | D-41 `approvals` + latest SCRIPT v4 | Olares SQL |

---

## 6. Olares verification

**Run:** `ad45f3a7-e772-437b-be00-c62a9121cec1` (continued from US-14; SCRIPT gate at verify start)  
**Images:** `aimpos-api:us15`, `aimpos-worker:us15`

| Check | Result |
|---|---|
| V-01 Fountain sample | **PASS** |
| V-02 SCRIPT reject | **PASS** |
| V-03 Regenerate #1–#3 (v1→v4) | **PASS** |
| V-04 4th regen → 429 | **PASS** |
| V-05 Approve → STORYBOARD gate | **PASS** |
| V-06 D-41 latest SCRIPT v4 + APPROVED | **PASS** |
| V-07 D-42 worker regen logs | **PASS** |

**Note:** Regen #2 activity attempt 1 failed D-40 (`dialogue_count == 0`); Temporal retry succeeded on attempt 2 — expected validator behavior.

---

## 7. Closure recommendation

**ACCEPT** — All four Visual MVP ACs evidenced on Olares. US-16 unblocked via D-41 `fetch_approved_script`.
