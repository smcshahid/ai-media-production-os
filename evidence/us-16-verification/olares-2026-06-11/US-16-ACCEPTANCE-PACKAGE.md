# US-16 Acceptance Package — Olares Verification

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-11  
**Worker image:** `docker.io/library/aimpos-worker:us16`  
**API image:** unchanged from US-15 (`aimpos-api:us15`)  
**DB migration:** Alembic `0003` (STORYBOARD multi-frame partial unique indexes)  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Run:** `9949bb3a-d0f1-4e2c-a23d-2aae813a5b47`  
**Verify log:** `logs/us16-verify.log`  
**Implementation report:** `docs/sprints/sprint-3g-us16-implementation-report.md`

---

## Verification summary

| Check | Result |
|---|---|
| V-01 — Frame count (D-45 = 4) | **PASS** |
| V-02 — STORYBOARD rows (shared batch `version`, distinct `frame_index`) | **PASS** |
| V-03 — Lineage script → 4 frames | **PASS** |
| V-04 — Pipeline at STORYBOARD review gate (AC-4) | **PASS** |
| V-05 — GPU sequencing + storyboard completion (AC-2, AC-5) | **PASS** |
| V-06 — MinIO PNG sample (AC-1) | **PASS** |

**Closure recommendation:** **ACCEPT**

---

## Test gates before deployment

| Suite | Result |
|---|---|
| Worker unit | **33 passed** (+12 US-16) |
| API unit | **78 passed** (no API route changes) |

Local logs: `evidence/us-16-verification/local-2026-06-11/logs/`

---

## Prerequisites applied on Olares

1. **ComfyUI launcher** — shared ComfyUI pod requires `POST http://127.0.0.1:3000/api/start` (Launcher UI equivalent) before `/queue` returns HTTP 200 on port 8190.
2. **Worker env** — `COMFYUI_HOST=http://comfyui.comfyuisharev2server-shared:8190`.
3. **Migration 0003** — applied via `deploy/k8s/us16-verify/migrate_0003.sh` after discovering `uq_asset_versions_project_id_stage_version` blocked four rows at the same batch `version` (D-43 amendment). See § Migration 0003 rationale.

---

## Migration 0003 rationale

**Problem:** D-43 requires all frames in one batch to share a monotonic `version` per `(project_id, STORYBOARD)`, distinguished by `metadata_json.frame_index`. The original schema enforced `UNIQUE (project_id, stage, version)`, which permits only **one** row per version — frame 2+ failed with `UniqueViolation` during Olares verify (`b70e8c39`).

**Fix:** Alembic `0003_storyboard_multi_frame_version.py` replaces the global triple unique constraint with two partial indexes:

| Index | Scope | Uniqueness |
|---|---|---|
| `uq_asset_versions_project_stage_version_single` | `stage != 'STORYBOARD'` | One row per `(project_id, stage, version)` — unchanged for STORY/SCRIPT/etc. |
| `uq_asset_versions_storyboard_batch_frame` | `stage = 'STORYBOARD'` | One row per `(project_id, stage, version, frame_index)` |

**Verification:** After `0003`, pass run `9949bb3a` inserted 4 rows at `version=1` with `frame_index` 1–4 in one transaction (V-02).

**Amendment:** D-43 rationale in `DECISIONS.md` updated to document this migration (originally assumed no schema change).

---

## E2E run

```
POST /ideas → IDEA v13
POST /pipeline/start → run_id=9949bb3a-d0f1-4e2c-a23d-2aae813a5b47 (HTTP 201)
Approve STORY → SCRIPT generation
Approve SCRIPT → STORYBOARD generation (run_storyboard_agent)
```

**Wall-clock:** ~70 s from SCRIPT approve to STORYBOARD gate (4 SDXL frames on RTX 5090).

---

## V-01 / D-45 — Exactly 4 frames

```
FRAME_COUNT=4
```

---

## V-02 — STORYBOARD asset rows

All four rows share `version=1`; distinguished by `metadata_json.frame_index`:

| asset_version_id | version | content_hash (prefix) | frame_index |
|---|---|---|---|
| `92a9f9e6-4a50-4acd-85ce-5d91b01bd703` | 1 | `c5701f87…` | 1 |
| `0fbe5b1a-162a-4ab9-bb8b-c3461e1b6733` | 1 | `6b74839d…` | 2 |
| `c47d166c-e8d3-43aa-bfa4-2f02aa68565b` | 1 | `7df89617…` | 3 |
| `9ad9898c-33d2-4ba4-900f-0b4457049d96` | 1 | `d762fedb…` | 4 |

---

## V-03 / AC-3 — Lineage

```
SCRIPT_ID=ec74bae1-7638-4496-a454-42df7f749142
LINEAGE_COUNT=4
```

Each frame has a `lineage_edges` row: approved SCRIPT parent → frame child.

---

## V-04 / AC-4 — Review gate

```
GET /pipeline/status
→ status=AWAITING_APPROVAL, current_stage=STORYBOARD
```

---

## V-05 / AC-2 — GPU sequencing and agent completion

Worker log excerpts (attempt 1, success):

- `ollama_unloaded` (`model=qwen3:14b`) before ComfyUI calls
- `comfyui_queued` seeds 43–46 (4 frames)
- `storyboard_agent_completed` with `frame_count=4` and four `frame_asset_version_ids`

---

## V-06 / AC-1 — MinIO PNG

```
mc stat local/aimpos-hot-assets/ba0c4636-817c-423b-9771-20100e080b76/STORYBOARD/c5701f87…
→ 391 KiB, Content-Type: image/png
```

---

## D-44 attestation

Prior failed attempts (`e8dd92d9` ComfyUI 503; `b70e8c39` pre-0003 UniqueViolation) left **zero** STORYBOARD rows until the successful batch at `version=1`. No orphan partial batches.

---

## US-17 batch resolution query (D-43)

```sql
WITH latest AS (
  SELECT COALESCE(MAX(version), 0) AS v
  FROM asset_versions
  WHERE project_id = :project_id AND stage = 'STORYBOARD'
)
SELECT av.id, av.version, av.content_hash, av.minio_key,
       av.metadata_json->>'frame_index' AS frame_index
FROM asset_versions av, latest
WHERE av.project_id = :project_id
  AND av.stage = 'STORYBOARD'
  AND av.version = latest.v
ORDER BY (av.metadata_json->>'frame_index')::int;
```

---

## Governance attestation

| AC | Evidence |
|---|---|
| AC-1 — 4–6 PNG via ComfyUI | 4 PNG frames; MinIO stat; D-45 pins N=4 |
| AC-2 — Ollama unloaded before GPU | `ollama_unloaded` log before `comfyui_queued` |
| AC-3 — Lineage script → frames | 4 `lineage_edges` from approved SCRIPT |
| AC-4 — STORYBOARD review gate | `AWAITING_APPROVAL` / `STORYBOARD` |
| AC-5 — Retry then FAILED | Temporal `RetryPolicy(maximum_attempts=2)`; prior failures retried then FAILED with no partial rows |

**Request: formal governance closure of US-16.**
