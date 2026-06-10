# Sprint 3B — US-12 Story Architect (implementation brief)

**Scope:** Replace STORY-stage stub with real Ollama + LangGraph. Preserve all Sprint 2 contracts (D-32–D-34, D-33).  
**Prerequisites:** M1-DV ✅, M2 ✅, US-11 ✅ (`idea.txt` on `stage=IDEA`).

---

## 1. What gets replaced

| Today (Sprint 2) | US-12 change |
|------------------|--------------|
| `run_stub_stage` for **every** stage in `SparkPipelineWorkflow` | **STORY only:** call `run_story_agent` instead |
| Returns `stub-story-{run_id}` | Returns `asset_version_id` for `story.md` |

**Unchanged in workflow:** stage loop order (`STORY` → `SCRIPT` → `STORYBOARD`), `sync_pipeline_status` before/after generation, `approve`/`reject` signals, `wait_condition` reject-then-approve path, 30-day approval timeout.

**`SparkPipelineWorkflow` diff (conceptual):**

```python
# inside the per-stage loop, after sync RUNNING:
if stage == PipelineStage.STORY:
    await workflow.execute_activity(run_story_agent, args=[project_id, run_id], ...)
else:
    await workflow.execute_activity(run_stub_stage, args=[stage.value, run_id], ...)
```

No workflow rename, no new signals, no API route changes.

---

## 2. Worker / agents layout (new files)

```
worker/app/
├── agents/
│   └── story_architect/
│       ├── graph.py          # LangGraph StateGraph (T-12-01)
│       ├── state.py          # StoryArchitectState dataclass
│       └── nodes.py          # load_idea, generate, finalize
├── temporal/activities/
│   ├── stub.py               # keep — SCRIPT/STORYBOARD
│   └── story.py              # run_story_agent (T-12-02)
└── tools/
    ├── ollama.py             # HTTP client → Ollama /api/generate
    └── assets.py             # sync MinIO + asset_versions writer (mirrors api store_asset)
```

Register in `worker/app/main.py`: `run_story_agent` activity; keep `run_stub_stage`, `sync_pipeline_status`.

**Boundary:** LangGraph runs **inside** `run_story_agent` only. Temporal owns durability, retries, and approval gates.

---

## 3. LangGraph graph boundaries

**In graph (ephemeral, single activity invocation):**

| Node | Responsibility |
|------|----------------|
| `load_idea` | Fetch latest `asset_versions` row `stage=IDEA`; download `idea.txt`; read `metadata_json.style_note` if present |
| `draft_story` | Call Ollama; produce markdown treatment |
| `finalize` | Validate non-empty markdown; attach `model_id`, token/latency stats to state |

**Out of graph (Temporal / existing API):**

- Pipeline status (`RUNNING` / `AWAITING_APPROVAL`) — `sync_pipeline_status`
- Human approve/reject — `POST /pipeline/approve` → Temporal signals (unchanged)
- Dashboard polling — `GET /pipeline/status` reads DB only (D-34)
- Regenerate after reject — **stubbed** until US-09 (reject still blocks at same stage; no re-invoke on reject)

**MVP graph:** linear `load_idea → draft_story → finalize`. No `kg_query`, no multi-agent loops (deferred per Scope Freeze).

---

## 4. Prompt management

| Artifact | Location |
|----------|----------|
| System + user templates | `configs/prompts/story_architect/v1.yaml` (new) |
| Model pin | `configs/ollama/models.json` → `stages.story` (`qwen3:14b`, D-36) |
| Agent id constant | `aimpos_core` or `worker/app/agents/story_architect/constants.py` → `agent.story_architect` |

**Rules:**

- Prompts are **versioned files in git**, not DB rows.
- Activity loads template by fixed path (`v1` for US-12); bump `v2` only via decision/SCR.
- Inject: `idea.txt` body, optional `style_note`, genre/format guardrails from template.
- Output contract: UTF-8 markdown file named **`story.md`** (treatment: title, logline, 3-act beat summary — keep template concise for MVP).

---

## 5. Asset outputs

| Field | Value |
|-------|-------|
| `stage` | `STORY` (`AssetStage.STORY`) |
| `branch` | **`ai-draft`** (US-12 AC; not `main`) |
| `is_ai_generated` | `true` |
| `content_type` | `text/markdown` |
| Bytes | LangGraph `finalize` output |
| Storage | Existing `store_asset` semantics: SHA-256 key, version increment per `(project, stage)` |

**Input dependency:** latest IDEA version for `project_id`. If none → activity fails fast with clear error (no workflow advance to approval).

**Downstream:** US-13 reads `stage=STORY`, `branch=ai-draft` for review UI; US-14 (later) reads approved story — promotion to `main` is US-13 scope, not US-12.

---

## 6. Audit schema additions (worker-emitted)

Use existing `audit_events` columns — **no migration** for US-12.

| Event | When | `model_id` | `payload` (JSON) |
|-------|------|------------|------------------|
| `STAGE_STARTED` | Start of `run_story_agent` | — | `{stage, agent: "agent.story_architect"}` |
| `AGENT_TASK_COMPLETED` | After successful `store_asset` | `qwen3:14b` | `{agent, asset_version_id, minio_key, duration_ms, prompt_version: "v1"}` |
| `ASSET_STORED` | Same commit (optional duplicate for SC-05) | `qwen3:14b` | `{stage: "STORY", branch: "ai-draft", content_hash}` |
| `PIPELINE_FAILED` | Terminal activity failure | model if known | `{stage: "STORY", error, attempt}` |

API continues to emit only `PIPELINE_STARTED` and `APPROVAL_RECORDED` (D-33). Worker appends via sync SQLAlchemy (same pattern as `sync_pipeline_status`).

---

## 7. Failure / retry

| Layer | Policy |
|-------|--------|
| **Temporal activity** | `RetryPolicy(maximum_attempts=3)` — match existing activities |
| **Ollama** | Retry transient HTTP/timeout inside tool; surface model-missing as non-retryable |
| **Empty/invalid LLM output** | Retryable once (graph `finalize` raises); then fail activity |
| **Missing IDEA asset** | Non-retryable — fail immediately |
| **Terminal failure** | Activity raises → workflow run fails; add `sync_pipeline_status(run_id, "FAILED", "STORY")` + `PIPELINE_FAILED` audit in activity `except` path **or** workflow catch block (pick one; prefer activity `finally` helper) |

**Reject path unchanged:** user reject does **not** re-run agent (US-09 adds regenerate). Workflow waits for approve signal at same stage.

**GPU (D-08):** STORY uses Ollama only — no ComfyUI unload required for this stage.

---

## 8. Integration with `SparkPipelineWorkflow`

Sequence for **STORY** (contracts preserved):

```
sync_pipeline_status(RUNNING, STORY)     # dashboard → GENERATING
run_story_agent(project_id, run_id)      # NEW — replaces run_stub_stage
sync_pipeline_status(AWAITING_APPROVAL, STORY)  # dashboard → REVIEW (D-34)
wait_condition(approve | reject)         # unchanged
```

**Status vocabulary:** Issue AC says "STORY_REVIEW" — that is **presentation only** (`AWAITING_APPROVAL` + `current_stage=STORY`). Do not add new DB enum values.

**Activity args:** pass `project_id` (str UUID) + `run_id` so audit + asset rows link to `pipeline_run_id`.

---

## 9. Ollama invocation (`qwen3:14b`)

| Setting | Source |
|---------|--------|
| Host | `OLLAMA_HOST` / settings (`http://ollama:11434` compose; Olares hybrid FQDN in env) |
| Model | `configs/ollama/models.json` → `stages.story` → **`qwen3:14b`** |
| API | `POST /api/generate` with `stream: false` |
| Params | `num_predict` ≥ 1024 for treatment length; temperature pinned in prompt config |
| Thinking model | Handle empty `response` — read `thinking` field if needed (M1-DV lesson, D-36) |
| Egress | Local Ollama only — zero cloud APIs (US-06 / SC-05) |

Tool: `worker/app/tools/ollama.py` — thin httpx wrapper; no LangChain chat wrapper required for MVP.

---

## 10. What stays stubbed (Sprint 3B)

| Item | Sprint |
|------|--------|
| `run_stub_stage` for **SCRIPT** | US-14 (3C) |
| `run_stub_stage` for **STORYBOARD** | US-16 (S4) |
| US-09 regenerate on reject | Sprint 3+ (API may exist; worker re-invoke not wired) |
| US-13 review UI / `PUT /assets` | Sprint 3B sibling story — not US-12 |
| ComfyUI / GPU sequencer on STORY path | N/A |
| `kg_query`, beat_analyze tools | Deferred (Multi-Agent Architecture) |

---

## 11. Verification (exit for US-12)

1. `POST /ideas` → `POST /pipeline/start` → status `RUNNING`/`STORY`.
2. Worker completes `run_story_agent` → `story.md` on MinIO, `branch=ai-draft`, `is_ai_generated=true`.
3. Status → `AWAITING_APPROVAL`/`STORY`; dashboard shows REVIEW (D-34).
4. `POST /pipeline/approve` → workflow advances to SCRIPT stub (unchanged M2 behavior for later stages).
5. Audit rows: `STAGE_STARTED`, `AGENT_TASK_COMPLETED` with `model_id=qwen3:14b`.
6. `scripts/smoke/test_m2_e2e.py` updated or sibling `test_story_pipeline.py` with live Ollama gate.

---

## 12. Dependencies to add (`worker/pyproject.toml`)

- `langgraph` (pinned major)
- `httpx`
- `minio`
- `pyyaml` (prompt templates)

---

## 13. Non-goals (Sprint 3B)

- API calling Ollama/LangGraph (forbidden — coding-standards)
- Changing approval API shape or Temporal signal names
- Branch merge UI / LakeFS
- US-14 Screenwriter or US-16 storyboard agents
