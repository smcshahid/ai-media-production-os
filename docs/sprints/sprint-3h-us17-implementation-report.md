# Sprint 3H — US-17 Implementation Report

**Date:** 2026-06-11  
**Status:** **CLOSED** — Olares verification PASS; release `v0.3.6-us17`.  
**Baseline:** `v0.3.5-us16` (`4f52bb5`)  
**Governance:** `D-46`, `D-47`, `docs/sprints/sprint-3h-us17-brief.md`, `docs/sprints/sprint-3h-us17-implementation-plan.md`

---

## 1. Summary

US-17 completes the Visual MVP human review path by adding a **storyboard batch gallery** on the Review route, **STORYBOARD PNG content-read**, **batch approve → COMPLETED**, and **reject + regenerate** at STORYBOARD stage (version+1 batch, D-47 rejection rationale). No schema migrations, no lineage/history UI, no video stage.

| Deliverable | Status |
|---|---|
| `GET /assets/{id}/content` for STORYBOARD PNG | ✅ |
| `POST /pipeline/regenerate` stage=STORYBOARD | ✅ |
| Worker D-47 rejection rationale + workflow arg | ✅ |
| Review gallery 2×2 + lightbox + AI badge | ✅ |
| Batch approve/reject/regenerate wiring | ✅ |
| Unit tests (API/worker/web) | ✅ |
| Olares verify scripts + E2E | ✅ PASS (`806b671a`) |

---

## 2. Decision records

| ID | Title | Notes |
|---|---|---|
| D-46 | Approved storyboard batch resolution | MAX(version) 4-frame set + STORYBOARD APPROVED approval; no branch promotion |
| D-47 | Storyboard regeneration input contract | Approved script + latest STORYBOARD rejection note; no prior frame bytes |

---

## 3. Files changed

### API
- `api/app/routes/assets.py` — STORYBOARD in readable stages; `image/png` delivery
- `api/app/routes/pipeline.py` — STORYBOARD in supported regenerate stages
- `api/tests/unit/test_assets_us17.py` — PNG content-read
- `api/tests/unit/test_pipeline_regenerate.py` — STORYBOARD regenerate happy path

### Worker
- `worker/app/tools/assets.py` — `fetch_latest_storyboard_rejection_rationale()`
- `worker/app/temporal/activities/storyboard.py` — `rejection_note` arg; D-47 resolution
- `worker/app/agents/cinematography/state.py`, `nodes.py`, `graph.py` — rejection note in planner prompt
- `worker/app/temporal/workflows/spark_pipeline.py` — pass rejection_note to storyboard activity
- `worker/tests/unit/test_storyboard_regen.py` — D-47 tests

### Web
- `web/src/lib/storyboardReview.ts` — `selectLatestStoryboardBatch()`
- `web/src/components/StoryboardLightbox.tsx` — enlarged frame preview
- `web/src/routes/ReviewPage.tsx` — storyboard gallery mode
- `web/src/api/client.ts` — `getAssetContentBlob()`
- `web/src/styles.css` — gallery + lightbox styles
- `web/src/tests/storyboardReview.test.ts`

### Deploy / evidence
- `deploy/k8s/us17-verify/` — verify, E2E, deploy, collect scripts
- `DECISIONS.md` — D-46, D-47
- `evidence/us-17-verification/`

---

## 4. Test results (local)

| Suite | Result |
|---|---|
| API unit | **81 passed** |
| Worker unit | **36 passed** |
| Web unit | **23 passed** |

Logs: `evidence/us-17-verification/local-2026-06-11/logs/`

---

## 5. Acceptance criteria mapping

| AC | Implementation | Evidence |
|---|---|---|
| AC-1 Grid 4 images | `ReviewPage` 2×2 grid; `selectLatestStoryboardBatch()` | Web unit test; Olares V-01 |
| AC-2 Lightbox | `StoryboardLightbox.tsx` | Component + manual UI |
| AC-3 Approve → COMPLETED | Existing approve route + workflow terminal | Olares V-04 |
| AC-4 Reject → regen | Regenerate STORYBOARD + D-47 worker path | API/worker tests; Olares V-03 |
| AC-5 AI badge | Badge on each grid tile | ReviewPage markup |

---

## 6. Olares verification

**Images:** `aimpos-api:us17`, `aimpos-worker:us17`  
**Script:** `deploy/k8s/us17-verify/verify_us17_e2e.sh`  
**Run:** `806b671a-29fe-4b62-8229-d57009a0792e`  
**Result:** **PASS** — reject/regen v2→v3, approve → COMPLETED, PNG content-read HTTP 200  
**Package:** `evidence/us-17-verification/olares-2026-06-11/US-17-ACCEPTANCE-PACKAGE.md`  
**Log:** `evidence/us-17-verification/olares-2026-06-11/logs/us17-e2e.log`

## 7. Repository status

Implementation complete on working tree; **not committed** (awaiting governance closure request). Olares E2E PASS documented in acceptance package.

**Frontier after US-17:** US-V01 Visual MVP E2E sign-off.
