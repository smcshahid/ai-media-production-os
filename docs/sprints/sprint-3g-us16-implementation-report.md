# Sprint 3G — US-16 Implementation Report

**Date:** 2026-06-11  
**Status:** **COMPLETE** — Olares verification PASS; closed at `v0.3.5-us16`.  
**Baseline:** `v0.3.4-us15`  
**Governance:** `D-43`, `D-44`, `D-45`, `docs/sprints/sprint-3g-us16-brief.md`, `docs/sprints/sprint-3g-us16-implementation-plan.md`

---

## 1. Summary

US-16 replaces the STORYBOARD Temporal stub with a real **Cinematography agent** (Ollama shot planning) and **ComfyUI SDXL inference**, storing **exactly 4 PNG frames** per generation (`D-45`) with **script lineage** (`D-43`) and **atomic batch persistence** (`D-44`). Work is **worker-only** plus config, verify scripts, and one **Alembic migration** (`0003`) required to honour D-43 multi-frame batch versioning.

| Deliverable | Status |
|---|---|
| Cinematography LangGraph planner | ✅ |
| ComfyUI HTTP client + production workflow JSON | ✅ |
| GPU sequencer (`unload_ollama_before_comfyui`, D-08) | ✅ |
| `run_storyboard_agent` Temporal activity | ✅ |
| `store_storyboard_batch()` atomic MinIO → DB | ✅ |
| Workflow swap STORYBOARD → real agent | ✅ |
| Alembic `0003` partial unique indexes | ✅ |
| API routes / web gallery (US-17) | ❌ Not added |
| STORYBOARD human-edit / regenerate | ❌ Not added |

---

## 2. Decision records

| ID | Title | Notes |
|---|---|---|
| D-43 | Storyboard frame asset contract | Shared batch `version`; `metadata_json.frame_index`; amended for migration `0003` |
| D-44 | Batch completeness | All-or-nothing store; no partial frames on failure |
| D-45 | Frame count = 4 | Pinned count (Issue 38 allows 4–6; US-16 ships 4) |

---

## 3. Schema amendment (0003)

The original `(project_id, stage, version)` unique constraint permitted only **one** row per version. D-43 requires **N frames** at the same batch version. Migration `api/alembic/versions/0003_storyboard_multi_frame_version.py`:

- Drops `uq_asset_versions_project_id_stage_version`
- Adds partial unique index for non-STORYBOARD stages (unchanged semantics)
- Adds partial unique index on `(project_id, stage, version, frame_index)` for STORYBOARD

Olares apply script: `deploy/k8s/us16-verify/migrate_0003.sh`

---

## 4. Files changed

### Worker
- `worker/app/agents/cinematography/` — state, nodes, graph, validate, constants
- `worker/app/tools/comfyui.py` — queue/poll/view PNG
- `worker/app/infrastructure/gpu/sequencer.py` — Ollama unload before ComfyUI
- `worker/app/tools/assets.py` — `store_storyboard_batch()`, `validate_storyboard_frame()`
- `worker/app/temporal/activities/storyboard.py` — `run_storyboard_agent`
- `worker/app/temporal/workflows/spark_pipeline.py` — STORYBOARD activity swap
- `worker/app/main.py` — register activity
- `worker/tests/unit/test_*storyboard*`, `test_comfyui_tool.py`, `test_cinematography_*`, `test_gpu_sequencer.py`

### Config / deploy
- `configs/prompts/cinematography/v1.yaml`
- `configs/comfyui/workflows/sdxl_storyboard_production.json`
- `configs/ollama/models.json` — `storyboard` stage model pin
- `packages/aimpos-config/aimpos_config/settings.py` — `COMFYUI_HOST`
- `deploy/compose/docker-compose.yml` — worker env
- `deploy/k8s/us16-verify/` — verify, deploy, migrate scripts

### API (migration only)
- `api/alembic/versions/0003_storyboard_multi_frame_version.py`
- `api/app/infrastructure/db/models/asset_version.py` — constraint moved to migration

### Governance / evidence
- `DECISIONS.md` — D-43..D-45
- `evidence/us-16-verification/` — local + Olares packages

---

## 5. Test results

| Suite | Result |
|---|---|
| Worker unit | **33 passed** (+12) |
| API unit | **78 passed** (unchanged) |

Log: `evidence/us-16-verification/local-2026-06-11/logs/`

---

## 6. AC implementation mapping

| AC | Implementation | Olares evidence |
|---|---|---|
| AC-1 — PNG via ComfyUI | `generate_storyboard_png()` × 4; `sdxl_storyboard_production.json` | V-06 MinIO stat; 4 frames in ~70 s |
| AC-2 — Ollama unload | `unload_ollama_before_comfyui()` | V-05 `ollama_unloaded` before `comfyui_queued` |
| AC-3 — Lineage | `store_storyboard_batch()` inserts 4 edges | V-03 `LINEAGE_COUNT=4` |
| AC-4 — Review gate | Workflow sync after activity | V-04 `AWAITING_APPROVAL`/`STORYBOARD` |
| AC-5 — Retry 2× | `RetryPolicy(maximum_attempts=2)` on activity | Failed runs retried; no partial rows (D-44) |

---

## 7. Olares verification

**Pass run:** `9949bb3a-d0f1-4e2c-a23d-2aae813a5b47`  
**Log:** `evidence/us-16-verification/olares-2026-06-11/logs/us16-verify.log`  
**Package:** `evidence/us-16-verification/olares-2026-06-11/US-16-ACCEPTANCE-PACKAGE.md`

**Operational notes for future runs:**

1. Start ComfyUI via Olares Launcher (`POST /api/start` on launcher port 3000) before verify.
2. Apply Alembic `0003` on any environment that has not migrated.
3. Cancel or complete stale runs before `pipeline/start` (409 lesson from US-15).

---

## 8. US-17 handoff

Latest storyboard batch query documented in acceptance package (§ batch resolution). Gallery should filter `stage=STORYBOARD`, `version=MAX(version)`, order by `metadata_json.frame_index`.

---

## 9. Closure recommendation

All five Visual MVP ACs are evidenced on Olares with unit regression green. **Recommend ACCEPT** and tag `v0.3.5-us16` after commit authorization.
