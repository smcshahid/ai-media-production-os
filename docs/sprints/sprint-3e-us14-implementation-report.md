# Sprint 3E — US-14 Implementation Report

**Date:** 2026-06-10  
**Status:** **COMPLETE** — Olares verification PASS (`evidence/us-14-verification/olares-2026-06-10/`)  
**Baseline:** `v0.3.2-us09`  
**Governance:** `D-39`, `D-40`, `D-37`, `docs/sprints/sprint-3e-us14-brief.md`, `docs/sprints/sprint-3e-us14-implementation-plan.md`

---

## 1. Summary

US-14 replaces the SCRIPT-stage stub with a real Ollama Screenwriter agent. Work is **worker-only**: LangGraph agent, Fountain validator (`D-40`), `run_script_agent` activity, asset store, lineage insert, and a minimal workflow dispatch change. No API routes, web UI, or schema migrations.

| Deliverable | Status |
|---|---|
| Screenwriter LangGraph agent (`agent.screenwriter`) | ✅ |
| `configs/prompts/screenwriter/v1.yaml` | ✅ |
| Fountain validator (`D-40`) | ✅ |
| `store_script_fountain` + MinIO write (`D-39`) | ✅ |
| `fetch_approved_story` per `D-37` | ✅ |
| `lineage_edges` story → script | ✅ |
| Workflow SCRIPT → `run_script_agent` | ✅ |
| `POST /pipeline/regenerate` for SCRIPT | ❌ Not added (501 preserved) |
| Script review UI | ❌ Not added (US-15) |
| Alembic migration | ❌ Not added |

---

## 2. Decision records

### D-39 — Script asset semantics

Recorded in `DECISIONS.md`. SCRIPT assets use `stage=SCRIPT`, `branch=ai-draft`, `is_ai_generated=true`, append-only versioning, MinIO key `{project_id}/SCRIPT/{content_hash}`, lineage edge from approved story parent.

### D-40 — Fountain validation gate

Recorded in `DECISIONS.md`. `validate_fountain()` must fail (no store) when:

- `scene_heading_count == 0`
- `scene_count != 1`
- `dialogue_count == 0`

Implemented in `worker/app/agents/screenwriter/validate.py`; invoked in `finalize_script` node before activity persistence.

---

## 3. Files changed

### Config
- `configs/prompts/screenwriter/v1.yaml` — Screenwriter system/user templates; one-scene guardrails

### Worker — new modules
- `worker/app/agents/screenwriter/constants.py`
- `worker/app/agents/screenwriter/state.py`
- `worker/app/agents/screenwriter/nodes.py` — `load_story_context`, `draft_script`, `finalize_script`
- `worker/app/agents/screenwriter/validate.py` — `validate_fountain()` per D-40
- `worker/app/agents/screenwriter/graph.py` — `run_screenwriter_graph()`
- `worker/app/temporal/activities/script.py` — `run_script_agent` activity

### Worker — modified
- `worker/app/tools/config_paths.py` — `load_script_model`, `load_script_prompt`
- `worker/app/tools/assets.py` — `fetch_approved_story`, `store_script_fountain`, `insert_lineage_edge`
- `worker/app/temporal/workflows/spark_pipeline.py` — SCRIPT branch calls `run_script_agent`
- `worker/app/main.py` — register `run_script_agent`
- `worker/app/temporal/activities/__init__.py` — export `run_script_agent`

### Tests
- `worker/tests/unit/test_fountain_validate.py` — D-40 positive/negative fixtures
- `worker/tests/unit/test_screenwriter.py` — graph finalize + mocked Ollama path

### Governance / evidence
- `DECISIONS.md` — D-39, D-40 appended
- `deploy/k8s/us14-verify/` — Olares verify, collect, deploy, cancel scripts
- `evidence/us-14-verification/` — local + Olares acceptance package

### Unchanged (by design)
- `api/` — no route changes
- `web/` — no UI changes
- `alembic/` — no migrations

---

## 4. Test results

| Suite | Result |
|---|---|
| Worker unit | **16 passed** (+11 US-14) |
| API unit | **76 passed** (regression, zero changes) |
| Web unit | **14 passed** (regression, zero changes) |

Key US-14 tests:
- `test_fountain_validate_*` — D-40 failure modes (0 headings, 2 scenes, no dialogue)
- `test_finalize_script_node_passes_valid_fountain`
- `test_run_screenwriter_graph_with_mocked_ollama`

Logs: `evidence/us-14-verification/local-2026-06-10/logs/`

---

## 5. AC implementation mapping

| AC | Implementation | Evidence |
|---|---|---|
| AC-1 Exactly 1 scene Fountain | Prompt + `validate_fountain` D-40 | Unit tests + Olares Fountain sample (1 `INT.` block) |
| AC-2 SCRIPT asset stored | `store_script_fountain` | Olares SQL v1 `stage=SCRIPT` |
| AC-3 Fountain, `is_ai_generated=true` | `branch=ai-draft`, `text/plain` MinIO | Olares SQL + `mc stat` Content-Type |
| AC-4 Lineage story → script | `insert_lineage_edge` after store | Olares SQL join STORY→SCRIPT |
| AC-5 Workflow to SCRIPT review | Existing `sync_pipeline_status(AWAITING_APPROVAL, SCRIPT)` | Olares `GET /pipeline/status` |

---

## 6. Olares deployment

| Item | Value |
|---|---|
| Host | `olares@10.0.0.34` |
| Namespace | `aimpos-mwayolares` |
| Worker image | `docker.io/library/aimpos-worker:us14` |
| API image | `docker.io/library/aimpos-api:us09` (unchanged) |
| Build | `nerdctl -n k8s.io build` on Olares node |

**Stale-run note:** The prior US-09 verification run (`980617a8-…`) reached SCRIPT under the stub workflow. After the US-14 worker swap, replaying that history caused `TMPRL1100` nondeterminism (`run_stub_stage` vs `run_script_agent`). The run was marked `CANCELLED` in `pipeline_runs` before fresh verification (`deploy/k8s/us14-verify/cancel_stale_run.sh`). New runs are required after workflow activity-type changes.

---

## 7. Olares verification summary

**Run:** `ad45f3a7-e772-437b-be00-c62a9121cec1`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`

| Check | Result |
|---|---|
| V-01 Fountain sample | **PASS** |
| V-02 SCRIPT `asset_versions` row | **PASS** |
| V-03 MinIO stat | **PASS** |
| V-04 Validator pass (implied by store) | **PASS** |
| V-05 `lineage_edges` join | **PASS** |
| V-06 Status `AWAITING_APPROVAL`/`SCRIPT` | **PASS** |
| V-07 Worker `script_agent_completed` (`qwen3:14b`) | **PASS** |
| V-08 Temporal `run_script_agent` scheduled post STORY approve | **PASS** |

Full evidence: `evidence/us-14-verification/olares-2026-06-10/US-14-ACCEPTANCE-PACKAGE.md`

---

## 8. Closure recommendation

**ACCEPT** — All five Visual MVP ACs evidenced on Olares with worker-only changes within authorized scope. Ready for formal closure review.
