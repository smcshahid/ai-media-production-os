# US-12 — Final Acceptance Evidence Package (Olares)

**Story:** US-12 Generate story from idea (FEAT-04)
**Date:** 2026-06-10
**Environment:** Olares One (`olares@10.0.0.34`), namespace `aimpos-mwayolares`, k3s
**Model:** `qwen3:14b` on shared Ollama (`http://ollama.ollamaserver-shared:11434`, 24GB GPU)
**Project:** `ba0c4636-817c-423b-9771-20100e080b76` (AIMPOS Spark Demo)
**Run:** `7e8699d1-35c6-4135-9a2b-404a737ad622`

**Recommendation: ACCEPT.** All nine acceptance criteria pass with evidence. No implementation change was required — the prior local failure was an environment defect (4GB GPU), confirmed by a clean run on the 24GB GPU.

---

## 1. What was deployed (deployment-only, no code change)

| Component | Action | Artifact |
|-----------|--------|----------|
| Worker image | Built locally, imported to containerd as `docker.io/library/aimpos-worker:us12` | `worker/Dockerfile` |
| Temporal + dedicated Postgres | New ephemeral manifests; Service named `temporal` (so API default `temporal:7233` and worker both resolve) | `deploy/k8s/us12-verify/temporal.yaml` |
| Worker Deployment | `envFrom` secret `aimpos-worker-env` | `deploy/k8s/us12-verify/worker.yaml` |
| Worker config | `OLLAMA_HOST=http://ollama.ollamaserver-shared:11434`, `TEMPORAL_ADDRESS=temporal:7233`, DB/MinIO from existing secrets | `aimpos-worker-env` |
| API | `rollout restart` to bind the now-present Temporal at lifespan startup | (no manifest change) |

Pre-existing on Olares (unchanged): PostgreSQL, MinIO, Redis, API, shared Ollama + `qwen3:14b`.

---

## 2. Acceptance criteria mapping

| AC | Criterion | Result | Evidence |
|----|-----------|--------|----------|
| AC-1 | `POST /ideas` creates IDEA asset | **PASS** | HTTP 201, asset `d585b232…`, stage=IDEA — `logs/01-02-idea-and-start.txt` |
| AC-2 | `POST /pipeline/start` triggers `run_story_agent` | **PASS** | run `7e8699d1…`, RUNNING/STORY; worker registers + executes `run_story_agent` |
| AC-3 | `qwen3:14b` generates story | **PASS** | `story.md` content (3-act treatment); `AGENT_TASK_COMPLETED` `model_id=qwen3:14b` |
| AC-4 | `story.md` stored in MinIO | **PASS** | `mc stat` 2.8 KiB text/markdown — `logs/04-minio-story-object.txt` |
| AC-5 | `asset_versions` row: STORY / ai-draft / is_ai_generated=true | **PASS** | `b87c4c5b…\|STORY\|1\|ai-draft\|true` — `logs/03-collect-ac-evidence.txt` |
| AC-6 | `AGENT_TASK_COMPLETED` audit, `model_id=qwen3:14b` | **PASS** | `AUDIT\|AGENT_TASK_COMPLETED\|qwen3:14b` |
| AC-7 | `ASSET_STORED` audit | **PASS** | `AUDIT\|ASSET_STORED\|qwen3:14b` |
| AC-8 | Pipeline `AWAITING_APPROVAL` / `current_stage=STORY` | **PASS** | status JSON + `RUN\|AWAITING_APPROVAL\|STORY` |
| AC-9 | Dashboard resolves to REVIEW | **PASS** | `AWAITING_APPROVAL → REVIEW` (`web/src/lib/pipelineDisplay.ts:22-23`), deterministic mapping of the verified AC-8 status |

---

## 3. Database evidence (`logs/03-collect-ac-evidence.txt`)

```
STORY_ROW|b87c4c5b-1f66-4699-b07c-f6c43d408723|STORY|1|ai-draft|true|52f69b19…|ba0c4636-…/STORY/52f69b19…
AUDIT|PIPELINE_STARTED|
AUDIT|STAGE_STARTED|
AUDIT|AGENT_TASK_COMPLETED|qwen3:14b
AUDIT|ASSET_STORED|qwen3:14b
RUN|AWAITING_APPROVAL|STORY
```

## 4. MinIO evidence (`logs/04-minio-story-object.txt`)

```
Name : 52f69b19da0449b4af5ea72d96e11916b72f741c18c88e6369b9ae7c395d6e58
Size : 2.8 KiB   Type: file   Content-Type: text/markdown
# Mars Garden US-12
**Logline:** A lone astronaut discovers a hidden garden on Mars…
### Act I: The Discovery … ### Act II: The Dilemma …
```

## 5. Temporal evidence

- Temporal server reached Ready (1/1); namespace `default` registered.
- Workflow `spark-pipeline-7e8699d1-…` started by API, executed `run_story_agent`, advanced to `AWAITING_APPROVAL` via `sync_pipeline_status`. See `logs/05-cluster-and-worker.txt`.

---

## 6. Risks / notes observed during verification

1. **API↔Temporal startup ordering** — API binds the Temporal client once at lifespan startup; deploying Temporal after the API requires an API restart. Runtime ordering, not a code defect.
2. **Timeout headroom** — Generation completed within ~1 minute (incl. cold model load) on the 24GB GPU, well inside the 5-min activity timeout. The local `300s < 600s` inversion never triggered here; remains an optional robustness fix.
3. **Ephemeral verification infra** — `temporal` + `temporal-db` use `emptyDir` and are verification-scoped (not production manifests). `deploy/k8s/us12-verify/` is reproducibility material.
4. **`scripts/smoke/test_us12_story.py`** is coupled to local compose (`127.0.0.1:8000`, `docker exec aimpos-spark-postgresql-1`); it cannot target Olares unchanged. This package collected equivalent authoritative evidence directly against the Olares API/DB/MinIO.

---

## 7. Closure recommendation

**ACCEPT — close US-12.** All acceptance criteria are met end-to-end on Olares with `qwen3:14b`. The implementation required no changes; the earlier local failure is confirmed as an environment defect.

Next story per backlog dependency order: **US-13 (Review and edit story)** — not started, per directive.
