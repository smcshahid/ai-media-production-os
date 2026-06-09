# AIMPOS-Spark — Product Backlog

**Document Type:** Product Backlog (Epics → Features → Stories → Tasks)  
**Version:** 1.0  
**Date:** June 8, 2026  
**Product:** AIMPOS-Spark MVP  
**Parent:** [MVP Definition.md](./MVP%20Definition.md)

---

## Import Files

| File | Purpose |
|------|---------|
| [backlog/aimpos-spark-backlog.csv](./backlog/aimpos-spark-backlog.csv) | Universal import (all work item types) |
| [backlog/aimpos-spark-backlog-jira.csv](./backlog/aimpos-spark-backlog-jira.csv) | Jira-optimized columns |
| [backlog/aimpos-spark-backlog-ado.csv](./backlog/aimpos-spark-backlog-ado.csv) | Azure DevOps-optimized columns |

See [§ Import Instructions](#import-instructions) at the end of this document.

---

## Backlog Summary

| Level | Count | Story Points |
|-------|-------|--------------|
| Epics | 6 | — |
| Features | 17 | — |
| User Stories | 27 | 95 |
| Tasks | 115 | — |

**Sprints:** S1–S5 (2 weeks each · 10 weeks total)

---

## Epic Index

| Epic ID | Title | Sprint | Features |
|---------|-------|--------|----------|
| EPIC-01 | Platform Foundation | S1 | — |
| EPIC-02 | Pipeline Orchestration | S2 | F-03, F-16 |
| EPIC-03 | Idea, Story & Script Stages | S3 | F-01, F-02, F-04–F-07 |
| EPIC-04 | Storyboard Stage | S4 | F-08, F-09 |
| EPIC-05 | Video & Pipeline Completion | S5 | F-10, F-11, F-14, F-15 |
| EPIC-06 | Governance, Assets & Console | S1–S5 | F-12, F-13, F-16 + UI |

---

# EPIC-01: Platform Foundation

**Sprint:** S1 (Weeks 1–2)  
**Goal:** Runnable Olares stack — PostgreSQL, MinIO, Redis, Ollama, ComfyUI, API skeleton, health checks.

**Epic acceptance criteria:**
- Docker Compose starts all services on Olares One with one command
- `/health` returns OK for API, PostgreSQL, MinIO, Ollama
- ComfyUI generates a test image via API/script
- Ollama responds to a test prompt locally with zero egress

---

## FEAT-01: Project Bootstrap

| Field | Value |
|-------|-------|
| **Feature ID** | F-01 |
| **Priority** | P0 |
| **Parent Epic** | EPIC-03 *(delivered in S1 as data model)* |

### US-01: Create default project

**As a** creator  
**I want** a default project created when the platform starts  
**So that** I can begin production without setup overhead

**Story Points:** 2 · **Sprint:** S1

**Acceptance criteria:**
- Given a fresh deployment, when the API starts, then one project `AIMPOS Spark Demo` exists
- Given the project exists, when I call `GET /projects`, then I receive the project with `id`, `title`, `status=ACTIVE`
- Given the project, when I query pipeline runs, then the list is empty

**Tasks:**

| Task ID | Task | Owner |
|---------|------|-------|
| T-01-01 | Create `projects` table migration | Backend |
| T-01-02 | Implement seed script for default project | Backend |
| T-01-03 | Add `GET /projects` endpoint | Backend |
| T-01-04 | Unit test project repository | Backend |

---

## FEAT-INFRA: Infrastructure (enabler)

| Field | Value |
|-------|-------|
| **Feature ID** | F-INFRA |
| **Priority** | P0 |
| **Parent Epic** | EPIC-01 |

### US-02: Deploy MVP stack on Olares

**As a** platform engineer  
**I want** Docker Compose for all MVP services  
**So that** the team can run the full stack locally on Olares One

**Story Points:** 5 · **Sprint:** S1

**Acceptance criteria:**
- Given Olares One with Docker, when I run `docker compose up`, then all 9 containers reach healthy state within 5 minutes
- Given the stack is running, when I curl API `/health`, then response is `200` with dependency statuses
- Given MinIO, when I upload a test file via S3 API, then download returns identical bytes
- Given the compose file, when I inspect networks, then all services are on `aimpos-spark` network only

**Tasks:**

| Task ID | Task |
|---------|------|
| T-02-01 | Write `docker-compose.yml` (api, worker, web, temporal, postgresql, minio, redis, ollama, comfyui) |
| T-02-02 | Configure PostgreSQL volume and init scripts |
| T-02-03 | Configure MinIO bucket `aimpos-hot-assets` on startup |
| T-02-04 | Pin Ollama model `llama3.1:13b` in compose init |
| T-02-05 | Document Olares deployment in README |
| T-02-06 | Verify zero egress during compose startup |

### US-03: API health and logging

**As a** platform engineer  
**I want** health checks and structured logs  
**So that** I can verify service readiness and debug failures

**Story Points:** 2 · **Sprint:** S1

**Acceptance criteria:**
- Given running API, when `GET /health` is called, then JSON includes `postgresql`, `minio`, `redis`, `temporal` status
- Given any API request, when it completes, then a structured JSON log line is emitted with `request_id`, `path`, `status`, `duration_ms`
- Given a dependency is down, when `/health` is called, then status is `503` with failed dependency named

**Tasks:**

| Task ID | Task |
|---------|------|
| T-03-01 | Implement `/health` with dependency probes |
| T-03-02 | Add structured logging middleware |
| T-03-03 | Add request ID propagation |

### US-04: Database schema foundation

**As a** backend developer  
**I want** core database tables migrated  
**So that** pipeline, assets, and audit data can be persisted

**Story Points:** 3 · **Sprint:** S1

**Acceptance criteria:**
- Given Alembic migrations, when applied, then tables exist: `projects`, `pipeline_runs`, `asset_versions`, `approvals`, `audit_events`, `lineage_edges`
- Given a migration rollback, when executed, then schema reverts without data corruption on empty DB
- Given `asset_versions`, when inspected, then columns include `stage`, `version`, `minio_key`, `content_hash`, `is_ai_generated`

**Tasks:**

| Task ID | Task |
|---------|------|
| T-04-01 | Define SQLAlchemy models for all core tables |
| T-04-02 | Create initial Alembic migration |
| T-04-03 | Add repository layer interfaces |

### US-05: MinIO asset upload service

**As a** backend developer  
**I want** a reusable asset upload function  
**So that** all stages store files content-addressably

**Story Points:** 3 · **Sprint:** S1

**Acceptance criteria:**
- Given file bytes, when `store_asset(bytes, stage, project_id)` is called, then SHA-256 is computed and object is stored at hash-based key
- Given stored asset, when metadata row is created, then `content_hash` matches object ETag
- Given duplicate bytes, when stored twice, then deduplication uses same `content_hash` (new version row, same blob)

**Tasks:**

| Task ID | Task |
|---------|------|
| T-05-01 | Implement MinIO client wrapper |
| T-05-02 | Implement content-hash key generator |
| T-05-03 | Implement `AssetVersion` create on upload |
| T-05-04 | Integration test upload round-trip |

### US-06: Ollama and ComfyUI smoke test

**As an** AI engineer  
**I want** verified local model endpoints  
**So that** agent development can begin in Sprint 3

**Story Points:** 3 · **Sprint:** S1

**Acceptance criteria:**
- Given Ollama running, when test script calls `generate("Hello")`, then response received in < 30s
- Given ComfyUI running, when test workflow executes, then PNG written to MinIO
- Given GPU on Olares, when Ollama and ComfyUI run sequentially, then no OOM error

**Tasks:**

| Task ID | Task |
|---------|------|
| T-06-01 | Create Ollama connectivity test script |
| T-06-02 | Pin and test ComfyUI SDXL workflow JSON |
| T-06-03 | Document GPU sequencing rule in worker README |

---

# EPIC-02: Pipeline Orchestration

**Sprint:** S2 (Weeks 3–4)  
**Goal:** Temporal workflow skeleton with start, status, approve/reject signals, audit events.

**Epic acceptance criteria:**
- User can start pipeline and see status transitions in UI/API
- Workflow pauses at each review gate awaiting signal
- Approve signal advances workflow; reject keeps stage open
- All transitions written to `audit_events`

---

## FEAT-03: Start Production Pipeline

| Field | Value |
|-------|-------|
| **Feature ID** | F-03 |
| **Priority** | P0 |

### US-07: Start pipeline workflow

**As a** creator  
**I want** to start the production pipeline after entering my idea  
**So that** AI-assisted production begins automatically

**Story Points:** 5 · **Sprint:** S2

**Acceptance criteria:**
- Given an idea is saved, when I `POST /pipeline/start`, then Temporal `SparkPipelineWorkflow` instance is created
- Given workflow started, when I `GET /pipeline/status`, then `current_stage` is `STORY_GENERATING` or `STORY_REVIEW`
- Given a pipeline already running, when I start again, then API returns `409 Conflict`
- Given workflow started, then audit event `PipelineStarted` is recorded with `workflow_id`

**Tasks:**

| Task ID | Task |
|---------|------|
| T-07-01 | Deploy Temporal server with PostgreSQL persistence |
| T-07-02 | Implement `SparkPipelineWorkflow` skeleton (5 stages, wait signals) |
| T-07-03 | Implement `POST /pipeline/start` API |
| T-07-04 | Implement `GET /pipeline/status` API |
| T-07-05 | Register Temporal worker pod |
| T-07-06 | Write audit event on pipeline start |

### US-08: Approve or reject stage output

**As a** creator  
**I want** to approve or reject AI output at each stage  
**So that** only content I accept advances the pipeline

**Story Points:** 5 · **Sprint:** S2

**Acceptance criteria:**
- Given workflow at review gate, when I `POST /pipeline/approve` with `stage` and `decision=GRANT`, then immutable `approvals` row is created
- Given approval, when workflow receives signal, then it advances to next stage
- Given reject, when I `POST` with `decision=REJECT` and `note`, then workflow stays at current stage and `note` is stored
- Given approval, then audit event `ApprovalGranted` includes `principal`, `stage`, `timestamp`

**Tasks:**

| Task ID | Task |
|---------|------|
| T-08-01 | Implement approval API endpoints |
| T-08-02 | Wire Temporal `approve` / `reject` signals |
| T-08-03 | Create immutable `approvals` table writes |
| T-08-04 | Handle reject without workflow advance |
| T-08-05 | Integration test approve advances stage |

### US-09: Regenerate after rejection

**As a** creator  
**I want** to regenerate AI output after rejecting it  
**So that** I can get improved results without restarting the pipeline

**Story Points:** 3 · **Sprint:** S2

**Acceptance criteria:**
- Given a rejected stage, when I `POST /pipeline/regenerate`, then new agent run is triggered for current stage only
- Given regenerate, when agent completes, then new `asset_version` is created with incremented version number
- Given 3 regenerations at same stage, when I regenerate again, then API returns `429` with limit message
- Given rejection note, when regenerate runs, then note is passed to agent context

**Tasks:**

| Task ID | Task |
|---------|------|
| T-09-01 | Implement regenerate endpoint |
| T-09-02 | Pass rejection note to activity input |
| T-09-03 | Enforce max 3 regenerations per stage |
| T-09-04 | Increment version on regenerate |

## FEAT-16: Pipeline Status Dashboard

| Field | Value |
|-------|-------|
| **Feature ID** | F-16 |
| **Priority** | P0 |

### US-10: View pipeline status

**As a** creator  
**I want** a dashboard showing current pipeline stage and progress  
**So that** I know what is happening and what action I need to take

**Story Points:** 3 · **Sprint:** S2

**Acceptance criteria:**
- Given active pipeline, when dashboard loads, then it shows: current stage name, status (`GENERATING`, `REVIEW`, `COMPLETED`, `FAILED`), progress indicator (1–5)
- Given stage is `REVIEW`, when dashboard renders, then primary CTA is `Go to Review`
- Given stage is `GENERATING`, when dashboard polls every 5s, then status updates without page reload
- Given pipeline failed, when dashboard loads, then error message and `Retry` action are shown

**Tasks:**

| Task ID | Task |
|---------|------|
| T-10-01 | Implement dashboard API aggregation endpoint |
| T-10-02 | Build Dashboard screen (React) |
| T-10-03 | Add 5-stage progress stepper component |
| T-10-04 | Implement status polling hook |

---

# EPIC-03: Idea, Story & Script Stages

**Sprint:** S3 (Weeks 5–6)  
**Goal:** Idea capture through approved script using Story Architect and Screenwriter agents.

**Epic acceptance criteria:**
- Creator completes Idea → approved Story → approved Script in one pipeline run
- Story and script stored as versioned assets in MinIO
- Agent invocations logged with model ID in audit trail

---

## FEAT-02: Capture Idea

| Field | Value |
|-------|-------|
| **Feature ID** | F-02 |
| **Priority** | P0 |

### US-11: Enter production idea

**As a** creator  
**I want** to enter my idea as title, paragraph, and optional style note  
**So that** the AI has creative context for story generation

**Story Points:** 2 · **Sprint:** S3

**Acceptance criteria:**
- Given project dashboard, when I submit idea form with title (required) and paragraph (required, 50–2000 chars), then `idea.txt` v1 is stored in MinIO
- Given optional style note, when provided, then stored as metadata on asset version
- Given idea saved, when I view assets, then `idea.txt` appears under stage `IDEA`
- Given missing title, when I submit, then validation error is shown

**Tasks:**

| Task ID | Task |
|---------|------|
| T-11-01 | Implement `POST /ideas` endpoint |
| T-11-02 | Build idea capture form on Dashboard |
| T-11-03 | Validate input length and required fields |
| T-11-04 | Store idea as `asset_version` stage=IDEA |

## FEAT-04: AI Story Generation

| Field | Value |
|-------|-------|
| **Feature ID** | F-04 |
| **Priority** | P0 |

### US-12: Generate story from idea

**As a** creator  
**I want** the Story Architect agent to generate a treatment from my idea  
**So that** I have a structured story foundation for my scene

**Story Points:** 5 · **Sprint:** S3

**Acceptance criteria:**
- Given approved idea and pipeline at S1, when story activity runs, then LangGraph Story Architect agent is invoked
- Given agent completes, then `story.md` is stored on branch `ai-draft` with `is_ai_generated=true`
- Given agent run, then audit logs include `model_id=llama3.1:13b`, `agent=story_architect`, `input_asset=idea.txt`
- Given Ollama call, when inspected, then request stays on `localhost` / Olares network only
- Given story generated, then workflow transitions to `STORY_REVIEW`

**Tasks:**

| Task ID | Task |
|---------|------|
| T-12-01 | Implement LangGraph Story Architect graph |
| T-12-02 | Implement `run_story_agent` Temporal activity |
| T-12-03 | Create story prompt template with idea + style injection |
| T-12-04 | Store story output as asset version |
| T-12-05 | Log agent invocation to audit_events |
| T-12-06 | Integration test story generation (mock Ollama) |

## FEAT-05: Story Review & Approval

| Field | Value |
|-------|-------|
| **Feature ID** | F-05 |
| **Priority** | P0 |

### US-13: Review and edit story

**As a** creator  
**I want** to read, edit, and approve the generated story  
**So that** the treatment reflects my creative intent before scripting

**Story Points:** 3 · **Sprint:** S3

**Acceptance criteria:**
- Given story ready for review, when Review screen loads, then treatment text is displayed in editable textarea
- Given I edit story text and save, then new `story.md` version is created on branch `human-edit`
- Given I click Approve, then approval is recorded and pipeline advances to script generation
- Given I click Reject with note, then pipeline stays at story stage and regenerate is enabled

**Tasks:**

| Task ID | Task |
|---------|------|
| T-13-01 | Build Review screen — story mode |
| T-13-02 | Implement `PUT /assets/{id}` text update |
| T-13-03 | Wire Approve/Reject buttons to pipeline API |
| T-13-04 | Display rejection note input on reject |

## FEAT-06: AI Script Generation

| Field | Value |
|-------|-------|
| **Feature ID** | F-06 |
| **Priority** | P0 |

### US-14: Generate one-scene script

**As a** creator  
**I want** the Screenwriter agent to generate a single-scene screenplay  
**So that** I have dialogue and action ready for storyboarding

**Story Points:** 5 · **Sprint:** S3

**Acceptance criteria:**
- Given approved story, when script activity runs, then Screenwriter agent produces Fountain-format script for exactly 1 scene
- Given script output, then `script.fountain` stored with `is_ai_generated=true`
- Given script, when parsed, then it contains scene heading, action, and at least one dialogue block
- Given agent run, then lineage edge `story.md → script.fountain` is recorded
- Given script generated, then workflow moves to `SCRIPT_REVIEW`

**Tasks:**

| Task ID | Task |
|---------|------|
| T-14-01 | Implement LangGraph Screenwriter graph |
| T-14-02 | Implement `run_script_agent` Temporal activity |
| T-14-03 | Add Fountain format validation |
| T-14-04 | Record lineage edge story → script |
| T-14-05 | Store script asset version |

## FEAT-07: Script Review & Approval

| Field | Value |
|-------|-------|
| **Feature ID** | F-07 |
| **Priority** | P0 |

### US-15: Review and approve script

**As a** creator  
**I want** to preview the script in readable format and approve it  
**So that** only my accepted script proceeds to visual production

**Story Points:** 3 · **Sprint:** S3

**Acceptance criteria:**
- Given script ready, when Review screen loads, then Fountain is rendered with scene heading and dialogue formatted
- Given I approve script, then pipeline advances to `STORYBOARD_GENERATING`
- Given I reject and regenerate, then new script version created with rejection note in context
- Given approved script, then it is marked as current approved version for stage SCRIPT

**Tasks:**

| Task ID | Task |
|---------|------|
| T-15-01 | Build Review screen — script mode with Fountain preview |
| T-15-02 | Add basic Fountain-to-HTML formatter |
| T-15-03 | Wire approve/reject for script stage |
| T-15-04 | Mark approved script version in DB |

---

# EPIC-04: Storyboard Stage

**Sprint:** S4 (Weeks 7–8)  
**Goal:** ComfyUI storyboard frames from approved script, gallery review, approval.

**Epic acceptance criteria:**
- 4–6 storyboard frames generated locally via ComfyUI
- Frames viewable in gallery with approve/reject/regenerate
- GPU jobs sequenced without OOM on Olares

---

## FEAT-08: AI Storyboard Generation

| Field | Value |
|-------|-------|
| **Feature ID** | F-08 |
| **Priority** | P0 |

### US-16: Generate storyboard frames

**As a** creator  
**I want** the Cinematography agent to generate 4–6 storyboard images from my script  
**So that** I can visualize the scene before video production

**Story Points:** 8 · **Sprint:** S4

**Acceptance criteria:**
- Given approved script, when storyboard activity runs, then agent produces 4–6 PNG frames via ComfyUI
- Given each frame, then stored as `frame_{n}.png` with `is_ai_generated=true`
- Given generation, then Ollama is unloaded before ComfyUI GPU job starts
- Given frames, then lineage edges `script.fountain → frame_n.png` exist
- Given completion, then workflow moves to `STORYBOARD_REVIEW`
- Given ComfyUI failure, then activity retries up to 2 times then marks pipeline `FAILED` with error

**Tasks:**

| Task ID | Task |
|---------|------|
| T-16-01 | Implement Cinematography agent (planning via Ollama) |
| T-16-02 | Implement ComfyUI tool — SDXL/Flux workflow |
| T-16-03 | Implement `run_storyboard_agent` Temporal activity |
| T-16-04 | GPU sequencing: unload Ollama before ComfyUI |
| T-16-05 | Store multiple frame assets per run |
| T-16-06 | Record lineage edges script → frames |
| T-16-07 | ComfyUI error handling and retry |

## FEAT-09: Storyboard Gallery Review

| Field | Value |
|-------|-------|
| **Feature ID** | F-09 |
| **Priority** | P0 |

### US-17: Review storyboard gallery

**As a** creator  
**I want** to view all frames in a grid and approve or reject the set  
**So that** I control which visuals proceed to video generation

**Story Points:** 3 · **Sprint:** S4

**Acceptance criteria:**
- Given frames ready, when Review screen loads, then 4–6 images displayed in responsive grid
- Given I click a frame, then enlarged preview opens
- Given I approve all, then all frames marked approved and pipeline advances to video stage
- Given I reject, then regenerate triggers new frame set; prior versions retained in history
- Given frames, then each shows `AI Generated` badge and model attribution

**Tasks:**

| Task ID | Task |
|---------|------|
| T-17-01 | Build Review screen — storyboard gallery mode |
| T-17-02 | Implement image preview lightbox |
| T-17-03 | Wire approve-all / reject for storyboard stage |
| T-17-04 | Display AI badge and model on frames |

---

# EPIC-05: Video & Pipeline Completion

**Sprint:** S5 (Weeks 9–10)  
**Goal:** Short video generation, approval, export bundle, lineage summary.

**Epic acceptance criteria:**
- 15–30 second video generated locally from approved frames
- Full pipeline completable end-to-end per demo script
- Export ZIP contains all approved assets and manifest

---

## FEAT-10: AI Short Video Generation

| Field | Value |
|-------|-------|
| **Feature ID** | F-10 |
| **Priority** | P0 |

### US-18: Generate short video clip

**As a** creator  
**I want** a short video generated from my approved storyboard frames  
**So that** I can preview my scene as motion video

**Story Points:** 8 · **Sprint:** S5

**Acceptance criteria:**
- Given approved frames, when video activity runs, then ComfyUI produces `scene_video.mp4` (15–30s, ≤480p for MVP)
- Given video, then stored with `is_ai_generated=true` and `mime_type=video/mp4`
- Given video generation, then lineage edges `frame_n.png → scene_video.mp4` recorded
- Given success, then workflow moves to `VIDEO_REVIEW`
- Given video failure after retries, then fallback creates slideshow MP4 from frames (documented degradation)

**Tasks:**

| Task ID | Task |
|---------|------|
| T-18-01 | Implement ComfyUI image-to-video workflow (SVD/AnimateDiff) |
| T-18-02 | Implement `run_video_agent` Temporal activity |
| T-18-03 | Implement slideshow fallback generator (FFmpeg) |
| T-18-04 | Store video asset with metadata (duration, resolution) |
| T-18-05 | Record lineage frames → video |
| T-18-06 | End-to-end GPU test on Olares hardware |

## FEAT-11: Video Preview & Approval

| Field | Value |
|-------|-------|
| **Feature ID** | F-11 |
| **Priority** | P0 |

### US-19: Preview and approve video

**As a** creator  
**I want** to preview the video in-browser and approve it  
**So that** my production pipeline completes with my sign-off

**Story Points:** 3 · **Sprint:** S5

**Acceptance criteria:**
- Given video ready, when Review screen loads, then HTML5 video player renders `scene_video.mp4`
- Given I approve video, then pipeline status becomes `COMPLETED`
- Given I reject video, then regenerate available; prior video versions in history
- Given completion, then audit event `PipelineCompleted` recorded

**Tasks:**

| Task ID | Task |
|---------|------|
| T-19-01 | Build Review screen — video player mode |
| T-19-02 | Wire approve/reject for video stage |
| T-19-03 | Set pipeline status COMPLETED on final approval |
| T-19-04 | Write PipelineCompleted audit event |

## FEAT-14: Lineage Summary

| Field | Value |
|-------|-------|
| **Feature ID** | F-14 |
| **Priority** | P1 |

### US-20: View asset lineage chain

**As a** creator  
**I want** to see the chain from idea to video  
**So that** I understand how each asset was derived

**Story Points:** 3 · **Sprint:** S5

**Acceptance criteria:**
- Given completed pipeline, when I open Lineage view, then ordered chain shows: idea → story → script → frames → video
- Given I click any node, then asset metadata and version shown
- Given video node, then parent frames listed with `ai_generated` flags
- Given lineage query, then data comes from `lineage_edges` in PostgreSQL (no Neo4j)

**Tasks:**

| Task ID | Task |
|---------|------|
| T-20-01 | Implement `GET /lineage/{pipeline_run_id}` API |
| T-20-02 | Build Lineage summary component on Export screen |
| T-20-03 | Render chain visualization (simple list/tree) |

## FEAT-15: Export Final Bundle

| Field | Value |
|-------|-------|
| **Feature ID** | F-15 |
| **Priority** | P1 |

### US-21: Download production bundle

**As a** creator  
**I want** to download a ZIP of all approved assets with a manifest  
**So that** I can archive or share my completed scene production

**Story Points:** 3 · **Sprint:** S5

**Acceptance criteria:**
- Given pipeline completed, when I click Export, then ZIP downloads containing: `idea.txt`, `story.md`, `script.fountain`, `frame_*.png`, `scene_video.mp4`, `manifest.json`
- Given `manifest.json`, then includes `content_hash` per file, approval timestamps, model IDs
- Given manifest hashes, when verified against files, then all match
- Given export, then audit event `BundleExported` recorded

**Tasks:**

| Task ID | Task |
|---------|------|
| T-21-01 | Implement `finalize_export` Temporal activity |
| T-21-02 | Implement `GET /export/{pipeline_run_id}` ZIP builder |
| T-21-03 | Generate manifest.json with hashes and metadata |
| T-21-04 | Build Export screen with download button |

---

# EPIC-06: Governance, Assets & Console

**Sprint:** S1–S5 (cross-cutting)  
**Goal:** Asset history, audit log, auth token, navigation shell, durability.

**Epic acceptance criteria:**
- All assets versioned and browsable
- Full audit trail visible for pipeline run
- Pipeline survives worker restart
- Simple API token auth on all mutating endpoints

---

## FEAT-12: Asset Version History

| Field | Value |
|-------|-------|
| **Feature ID** | F-12 |
| **Priority** | P0 |

### US-22: Browse asset versions

**As a** creator  
**I want** to see all versions of assets per stage  
**So that** I can compare AI drafts, edits, and approved outputs

**Story Points:** 3 · **Sprint:** S4

**Acceptance criteria:**
- Given pipeline with multiple versions, when Assets screen loads, then versions grouped by stage (IDEA, STORY, SCRIPT, STORYBOARD, VIDEO)
- Given version list, when sorted, then newest version first with version number and timestamp
- Given I click a version, then I can preview (text or media) or download
- Given version, then `is_ai_generated`, `branch`, and `content_hash` displayed

**Tasks:**

| Task ID | Task |
|---------|------|
| T-22-01 | Implement `GET /assets?project_id=&stage=` API |
| T-22-02 | Build Assets screen with stage tabs |
| T-22-03 | Implement version list and preview components |
| T-22-04 | Add download link per version |

## FEAT-13: Audit Log Viewer

| Field | Value |
|-------|-------|
| **Feature ID** | F-13 |
| **Priority** | P0 |

### US-23: View audit trail

**As a** creator  
**I want** to see a chronological log of pipeline events  
**So that** I can verify what happened, when, and which models were used

**Story Points:** 3 · **Sprint:** S3

**Acceptance criteria:**
- Given pipeline run, when Audit screen loads, then events sorted newest-first include: `PipelineStarted`, `AgentTaskCompleted`, `ApprovalGranted`, `ApprovalRejected`, `PipelineCompleted`
- Given agent event, then shows `model_id`, `agent_name`, `input_assets`
- Given audit entries, then they are append-only (no edit/delete in UI)
- Given export, then audit JSON included in manifest

**Tasks:**

| Task ID | Task |
|---------|------|
| T-23-01 | Implement `GET /audit?pipeline_run_id=` API |
| T-23-02 | Build Audit screen table |
| T-23-03 | Standardize audit event schema across worker |
| T-23-04 | Include audit summary in export manifest |

### US-24: Pipeline survives worker restart

**As a** platform engineer  
**I want** the pipeline to resume after worker or API restart  
**So that** creators don't lose progress on long GPU workflows

**Story Points:** 3 · **Sprint:** S2

**Acceptance criteria:**
- Given workflow running at SCRIPT_GENERATING, when worker pod restarts, then workflow resumes from last checkpoint within 2 minutes
- Given workflow at REVIEW gate, when API restarts, then approve signal still accepted and workflow advances
- Given restart, then no duplicate asset versions created
- Given restart scenario, then audit event `WorkerRecovered` optional log entry

**Tasks:**

| Task ID | Task |
|---------|------|
| T-24-01 | Configure Temporal worker graceful shutdown |
| T-24-02 | Test worker restart during review wait |
| T-24-03 | Test worker restart during activity execution |
| T-24-04 | Document recovery behavior |

### US-25: API token authentication

**As a** platform engineer  
**I want** simple API token auth on mutating endpoints  
**So that** the MVP is not completely open on the local network

**Story Points:** 2 · **Sprint:** S2

**Acceptance criteria:**
- Given no token, when calling `POST /pipeline/start`, then `401 Unauthorized`
- Given valid `Authorization: Bearer <token>` from env, when calling mutating endpoints, then request succeeds
- Given web console, when configured with token in env, then API calls include header automatically
- Given read-only `GET` endpoints, when called without token on LAN, then allowed (MVP dev mode) OR configurable

**Tasks:**

| Task ID | Task |
|---------|------|
| T-25-01 | Implement Bearer token middleware |
| T-25-02 | Configure token via environment variable |
| T-25-03 | Wire token into React API client |

### US-26: App navigation shell

**As a** creator  
**I want** consistent navigation between Dashboard, Review, Assets, Audit, and Export  
**So that** I can move through the production process easily

**Story Points:** 2 · **Sprint:** S2

**Acceptance criteria:**
- Given any screen, when app loads, then nav bar shows: Dashboard, Review, Assets, Audit, Export
- Given pipeline not started, when Review/Export clicked, then empty state message shown
- Given pipeline at review stage, when Dashboard clicked, then CTA reflects current stage
- Given mobile-width viewport (≥768px min for MVP), then layout remains usable

**Tasks:**

| Task ID | Task |
|---------|------|
| T-26-01 | Build app shell with React Router |
| T-26-02 | Implement nav bar and route guards |
| T-26-03 | Add empty states per screen |

### US-27: MVP demo acceptance validation

**As a** product owner  
**I want** the demo acceptance script executable end-to-end  
**So that** MVP readiness is objectively verified

**Story Points:** 2 · **Sprint:** S5

**Acceptance criteria:**
- All 10 steps in MVP Definition §9.3 demo script pass without manual DB intervention
- SC-01 through SC-08 success metrics verified and documented
- Known limitations documented in release notes
- Stakeholder demo recorded or signed off

**Tasks:**

| Task ID | Task |
|---------|------|
| T-27-01 | Execute demo acceptance script |
| T-27-02 | Document success metrics results |
| T-27-03 | Write MVP release notes |
| T-27-04 | Stakeholder demo and sign-off |

---

## Sprint Allocation

| Sprint | Epics | Key Stories | Points |
|--------|-------|-------------|--------|
| **S1** | EPIC-01, EPIC-06 (partial) | US-01–06 | 18 |
| **S2** | EPIC-02, EPIC-06 (partial) | US-07–10, US-24–26 | 23 |
| **S3** | EPIC-03, EPIC-06 (partial) | US-11–15, US-23 | 21 |
| **S4** | EPIC-04, EPIC-06 (partial) | US-16–17, US-22 | 14 |
| **S5** | EPIC-05, EPIC-06 (partial) | US-18–21, US-27 | 19 |
| **Total** | | **27 stories** | **95** |

---

## Traceability Matrix

| Feature | User Stories | Success Criteria |
|---------|--------------|------------------|
| F-01 | US-01 | SC-04 |
| F-02 | US-11 | SC-01 |
| F-03 | US-07 | SC-01, SC-06 |
| F-04 | US-12 | SC-02, SC-05, SC-07 |
| F-05 | US-13 | SC-03 |
| F-06 | US-14 | SC-02, SC-05 |
| F-07 | US-15 | SC-03 |
| F-08 | US-16 | SC-02, SC-05 |
| F-09 | US-17 | SC-03 |
| F-10 | US-18 | SC-01, SC-02 |
| F-11 | US-19 | SC-01, SC-03 |
| F-12 | US-22 | SC-04 |
| F-13 | US-23 | SC-05 |
| F-14 | US-20 | SC-01 |
| F-15 | US-21 | SC-11 |
| F-16 | US-10 | SC-08 |

---

# Import Instructions

## Universal CSV (`backlog/aimpos-spark-backlog.csv`)

Columns: `Work Item Type`, `ID`, `Title`, `Description`, `Parent ID`, `Epic ID`, `Feature ID`, `Priority`, `Story Points`, `Sprint`, `Labels`, `Acceptance Criteria`

## Jira Import

1. Use `backlog/aimpos-spark-backlog-jira.csv`
2. **Import CSV** → Map: Issue Type → Issue Type, Epic Name → Epic Link (for Stories)
3. Mapping: Epic → Epic, Feature → Story (label: `feature`), User Story → Story, Task → Sub-task
4. After import, link Sub-tasks to parent Stories via Parent column
5. Set Sprint field from `Sprint` column after board creation

**Jira issue type mapping:**

| CSV Type | Jira Type |
|----------|-----------|
| Epic | Epic |
| Feature | Story (+ label `type:feature`) |
| User Story | Story |
| Task | Sub-task |

## Azure DevOps Import

1. Use `backlog/aimpos-spark-backlog-ado.csv`
2. **Boards → Queries → Import work items**
3. Native mapping: Epic → Feature → User Story → Task
4. Set Area Path: `AIMPOS-Spark`
5. Set Iteration from `Iteration Path` column (Sprint 1–5)

## GitHub Projects Import

1. Create labels: `epic`, `feature`, `user-story`, `task`, `sprint-1` … `sprint-5`
2. Import `aimpos-spark-backlog.csv` via **GitHub CLI** or third-party CSV importer (e.g. GitHub Issue Import)
3. Alternative: run provided issue creation script pattern:
   - Create milestones: `Sprint 1` … `Sprint 5`
   - Each row → GitHub Issue with labels `epic-01`, `feature-F-03`, etc.
4. Use **GitHub Projects (v2)** parent issue relationships for hierarchy

**GitHub label convention:** `epic:EPIC-01`, `feature:F-03`, `sprint:1`, `priority:P0`

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-08 | Initial MVP backlog — 6 epics, 16 features, 27 stories, 96 tasks |

*End of document*
