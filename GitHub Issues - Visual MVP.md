# AIMPOS-Spark Visual — GitHub Issues

**Scope:** Idea → Story → Script → Storyboard · **Local AI only** (Ollama + ComfyUI)  
**Total Issues:** 43  
**Codename:** `AIMPOS-Spark-Visual`  

## What This MVP Delivers

| Stage | Human | Local AI | Output |
|-------|-------|----------|--------|
| Idea | Write paragraph | — | `idea.txt` |
| Story | Approve / edit | Ollama Story Architect | `story.md` |
| Script | Approve / edit | Ollama Screenwriter | `script.fountain` |
| Storyboard | Approve frames | ComfyUI + Ollama planning | `frame_*.png` |

**Pipeline completes** when storyboard frames are approved (`COMPLETED`).

## Explicitly Deferred (Post–Visual MVP)

| Excluded | IDs |
|----------|-----|
| Short video generation | F-10, US-18 |
| Video review | F-11, US-19 |
| Export bundle | F-15, US-21 |
| Full 5-stage demo | US-27, EPIC-05 |

## Sprint Plan (8 weeks)

| Sprint | Weeks | Deliverable |
|--------|-------|-------------|
| S1 | 1–2 | Platform running on Olares |
| S2 | 3–4 | 4-stage workflow + dashboard |
| S3 | 5–6 | Idea → approved script |
| S4 | 7–8 | Storyboard + lineage + **Visual MVP sign-off** |

## Import

```bash
gh issue create --title "[US-02] Deploy MVP stack on Olares" \
  --label "aimpos-spark,visual-mvp,user-story,sprint:s1,priority:p0" \
  --milestone "Sprint 1"
```

---

## Issue Index (Dependency Order)

| Order | ID | Type | Title | Priority | Sprint |
|------:|-----|------|-------|----------|--------|
| 1 | EPIC-01 | Epic | Platform Foundation | P0 | S1 |
| 2 | FEAT-INFRA | Feature | Infrastructure Enabler | P0 | S1 |
| 3 | US-02 | User Story | Deploy MVP stack on Olares | P0 | S1 |
| 4 | US-04 | User Story | Database schema foundation | P0 | S1 |
| 5 | US-03 | User Story | API health and logging | P0 | S1 |
| 6 | US-05 | User Story | MinIO asset upload service | P0 | S1 |
| 7 | US-06 | User Story | Ollama and ComfyUI smoke test | P0 | S1 |
| 8 | US-01 | User Story | Create default project | P0 | S1 |
| 9 | EPIC-02 | Epic | Pipeline Orchestration | P0 | S2 |
| 10 | FEAT-03 | Feature | Start Production Pipeline | P0 | S2 |
| 11 | FEAT-16 | Feature | Pipeline Status Dashboard | P0 | S2 |
| 12 | US-26 | User Story | App navigation shell | P0 | S2 |
| 13 | US-07 | User Story | Start pipeline workflow | P0 | S2 |
| 14 | US-08 | User Story | Approve or reject stage output | P0 | S2 |
| 15 | US-09 | User Story | Regenerate after rejection | P0 | S2 |
| 16 | US-24 | User Story | Pipeline survives worker restart | P0 | S2 |
| 17 | US-25 | User Story | API token authentication | P0 | S2 |
| 18 | US-10 | User Story | View pipeline status dashboard | P0 | S2 |
| 19 | EPIC-03 | Epic | Idea, Story & Script Stages | P0 | S3 |
| 20 | FEAT-01 | Feature | Project Bootstrap | P0 | S1 |
| 21 | FEAT-02 | Feature | Capture Idea | P0 | S3 |
| 22 | FEAT-04 | Feature | AI Story Generation | P0 | S3 |
| 23 | FEAT-05 | Feature | Story Review & Approval | P0 | S3 |
| 24 | FEAT-06 | Feature | AI Script Generation | P0 | S3 |
| 25 | FEAT-07 | Feature | Script Review & Approval | P0 | S3 |
| 26 | FEAT-13 | Feature | Audit Log Viewer | P0 | S3 |
| 27 | US-11 | User Story | Enter production idea | P0 | S3 |
| 28 | US-12 | User Story | Generate story from idea | P0 | S3 |
| 29 | US-13 | User Story | Review and edit story | P0 | S3 |
| 30 | US-14 | User Story | Generate one-scene script | P0 | S3 |
| 31 | US-15 | User Story | Review and approve script | P0 | S3 |
| 32 | US-23 | User Story | View audit trail | P0 | S3 |
| 33 | EPIC-04 | Epic | Storyboard Stage | P0 | S4 |
| 34 | FEAT-08 | Feature | AI Storyboard Generation | P0 | S4 |
| 35 | FEAT-09 | Feature | Storyboard Gallery Review | P0 | S4 |
| 36 | FEAT-12 | Feature | Asset Version History | P0 | S4 |
| 37 | FEAT-14 | Feature | Lineage Summary | P1 | S4 |
| 38 | US-16 | User Story | Generate storyboard frames | P0 | S4 |
| 39 | US-17 | User Story | Review storyboard gallery | P0 | S4 |
| 40 | US-20 | User Story | View asset lineage chain | P1 | S4 |
| 41 | US-22 | User Story | Browse asset versions | P0 | S4 |
| 42 | EPIC-06 | Epic | Governance, Assets & Console | P0 | S1-S5 |
| 43 | US-V01 | User Story | Visual MVP demo acceptance validation | P0 | S4 |

---
## Issue 1: [EPIC-01] Platform Foundation

**Type:** Epic  
**Milestone:** S1  
**Implementation Order:** 1  
**Epic:** #EPIC-01  

### Title
[EPIC-01] Platform Foundation

### Description
Runnable Olares stack: PostgreSQL, MinIO, Redis, Ollama, ComfyUI, API skeleton, health checks.

### Business Value
Runnable local-AI platform on Olares. Prerequisite for Ollama (text) and ComfyUI (images).

### Acceptance Criteria
- [ ] Docker Compose starts all services with one command
- [ ] /health returns OK
- [ ] ComfyUI test image succeeds
- [ ] Ollama responds locally with zero egress

### Dependencies
_None._

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `epic`, `sprint:s1`, `epic:EPIC-01`, `priority:p0`, `aimpos-spark`, `foundation`, `olares`

### Estimated Complexity
XL

### Definition of Done
- [ ] All child P0 features and stories closed
- [ ] Epic AC verified on Olares
- [ ] No P0 defects

---

## Issue 2: [FEAT-INFRA] Infrastructure Enabler

**Type:** Feature  
**Milestone:** S1  
**Implementation Order:** 2  
**Parent:** #EPIC-01  
**Epic:** #EPIC-01  

### Title
[FEAT-INFRA] Infrastructure Enabler

### Description
Docker Compose, health, schema, MinIO, Ollama/ComfyUI smoke tests.

### Business Value
Docker Compose, health, schema, MinIO, Ollama/ComfyUI smoke tests.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `feature`, `infrastructure`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 3: [US-02] Deploy MVP stack on Olares

**Type:** User Story  
**Milestone:** S1  
**Implementation Order:** 3  
**Story Points:** 5  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  

### Title
[US-02] Deploy MVP stack on Olares

### Description
As a platform engineer, I want Docker Compose for all MVP services.

### Business Value
One-command Olares deployment.

### Acceptance Criteria
- [ ] docker compose up brings 9 containers healthy within 5 min
- [ ] /health returns 200
- [ ] MinIO upload/download round-trip works
- [ ] All services on aimpos-spark network

### Dependencies
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `user-story`, `devops`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-02-01` — Write docker-compose.yml for all 9 services
- [ ] `T-02-02` — Configure PostgreSQL volume and init scripts
- [ ] `T-02-03` — Configure MinIO bucket aimpos-hot-assets on startup
- [ ] `T-02-04` — Pin Ollama model llama3.1:13b in compose init
- [ ] `T-02-05` — Document Olares deployment in README
- [ ] `T-02-06` — Verify zero egress during compose startup

---

## Issue 4: [US-04] Database schema foundation

**Type:** User Story  
**Milestone:** S1  
**Implementation Order:** 4  
**Story Points:** 3  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  

### Title
[US-04] Database schema foundation

### Description
As a backend developer, I want core tables migrated.

### Business Value
PostgreSQL system of record.

### Acceptance Criteria
- [ ] Tables: projects, pipeline_runs, asset_versions, approvals, audit_events, lineage_edges
- [ ] Rollback works on empty DB
- [ ] asset_versions has stage, version, minio_key, content_hash, is_ai_generated

### Dependencies
- #FEAT-INFRA (must be closed first)
- #US-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `user-story`, `backend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-04-01` — Define SQLAlchemy models for core tables
- [ ] `T-04-02` — Create initial Alembic migration
- [ ] `T-04-03` — Add repository layer interfaces

---

## Issue 5: [US-03] API health and logging

**Type:** User Story  
**Milestone:** S1  
**Implementation Order:** 5  
**Story Points:** 2  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  

### Title
[US-03] API health and logging

### Description
As a platform engineer, I want health checks and structured logs.

### Business Value
Integration health visibility.

### Acceptance Criteria
- [ ] GET /health includes postgresql, minio, redis, temporal status
- [ ] Structured JSON logs with request_id
- [ ] Failed dependency returns 503

### Dependencies
- #FEAT-INFRA (must be closed first)
- #US-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `user-story`, `backend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-03-01` — Implement /health with dependency probes
- [ ] `T-03-02` — Add structured logging middleware
- [ ] `T-03-03` — Add request ID propagation

---

## Issue 6: [US-05] MinIO asset upload service

**Type:** User Story  
**Milestone:** S1  
**Implementation Order:** 6  
**Story Points:** 3  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  

### Title
[US-05] MinIO asset upload service

### Description
As a backend developer, I want reusable content-addressable asset storage.

### Business Value
Versioned assets in MinIO.

### Acceptance Criteria
- [ ] store_asset computes SHA-256 and stores at hash key
- [ ] Metadata row content_hash matches ETag
- [ ] Duplicate bytes deduplicated

### Dependencies
- #FEAT-INFRA (must be closed first)
- #US-02 (must be closed first)
- #US-04 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `user-story`, `backend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-05-01` — Implement MinIO client wrapper
- [ ] `T-05-02` — Implement content-hash key generator
- [ ] `T-05-03` — Implement AssetVersion create on upload
- [ ] `T-05-04` — Integration test upload round-trip

---

## Issue 7: [US-06] Ollama and ComfyUI smoke test

**Type:** User Story  
**Milestone:** S1  
**Implementation Order:** 7  
**Story Points:** 3  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  

### Title
[US-06] Ollama and ComfyUI smoke test

### Description
As an AI engineer, I want verified local model endpoints.

### Business Value
Validates Ollama + ComfyUI image path early.

### Acceptance Criteria
- [ ] Ollama generate responds in <30s
- [ ] ComfyUI workflow writes PNG to MinIO
- [ ] Sequential GPU use without OOM

### Dependencies
- #FEAT-INFRA (must be closed first)
- #US-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `user-story`, `ai`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-06-01` — Create Ollama connectivity test script
- [ ] `T-06-02` — Pin and test ComfyUI SDXL workflow JSON
- [ ] `T-06-03` — Document GPU sequencing rule in worker README

---

## Issue 8: [US-01] Create default project

**Type:** User Story  
**Milestone:** S1  
**Implementation Order:** 8  
**Story Points:** 2  
**Parent:** #FEAT-01  
**Epic:** #EPIC-03  

### Title
[US-01] Create default project

### Description
As a creator, I want a default project on startup so I can begin without setup.

### Business Value
Immediate project context — no setup.

### Acceptance Criteria
- [ ] Given fresh deployment, one project AIMPOS Spark Demo exists
- [ ] GET /projects returns project with status ACTIVE
- [ ] Pipeline runs list is empty

### Dependencies
- #FEAT-01 (must be closed first)
- #US-04 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s1`, `feature:F-01`, `epic:EPIC-03`, `priority:p0`, `user-story`, `backend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-01-01` — Create projects table migration
- [ ] `T-01-02` — Implement seed script for default project
- [ ] `T-01-03` — Add GET /projects endpoint
- [ ] `T-01-04` — Unit test project repository

---

## Issue 9: [EPIC-02] Pipeline Orchestration

**Type:** Epic  
**Milestone:** S2  
**Implementation Order:** 9  
**Epic:** #EPIC-02  

### Title
[EPIC-02] Pipeline Orchestration

### Description
Temporal 4-stage workflow: Idea → Story → Script → Storyboard. Start, status, approve/reject, regenerate, audit.

### Business Value
4-stage workflow with human approval gates. Proves Temporal + human-in-the-loop without video complexity.

### Acceptance Criteria
- [ ] User starts pipeline and sees 4-stage status
- [ ] Workflow pauses at each review gate
- [ ] Approve on storyboard sets COMPLETED
- [ ] All transitions in audit_events

### Dependencies
- #EPIC-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `epic`, `sprint:s2`, `epic:EPIC-02`, `priority:p0`, `aimpos-spark`, `temporal`, `workflow`

### Estimated Complexity
XL

### Definition of Done
- [ ] All child P0 features and stories closed
- [ ] Epic AC verified on Olares
- [ ] No P0 defects

---

## Issue 10: [FEAT-03] Start Production Pipeline

**Type:** Feature  
**Milestone:** S2  
**Implementation Order:** 10  
**Parent:** #EPIC-02  
**Epic:** #EPIC-02  

### Title
[FEAT-03] Start Production Pipeline

### Description
Start Temporal workflow after idea capture. F-03.

### Business Value
Start Temporal workflow after idea capture. F-03.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-02 (must be closed first)
- #FEAT-INFRA (must be closed first)
- #FEAT-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `feature`, `F-03`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 11: [FEAT-16] Pipeline Status Dashboard

**Type:** Feature  
**Milestone:** S2  
**Implementation Order:** 11  
**Parent:** #EPIC-02  
**Epic:** #EPIC-02  

### Title
[FEAT-16] Pipeline Status Dashboard

### Description
Dashboard showing stage, progress, CTAs. F-16.

### Business Value
Dashboard showing stage, progress, CTAs. F-16.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-02 (must be closed first)
- #FEAT-INFRA (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s2`, `feature:F-16`, `epic:EPIC-02`, `priority:p0`, `feature`, `F-16`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 12: [US-26] App navigation shell

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 12  
**Story Points:** 2  
**Parent:** #FEAT-16  
**Epic:** #EPIC-06  

### Title
[US-26] App navigation shell

### Description
As a creator, I want nav between Dashboard, Review, Assets, Audit, Export.

### Business Value
Nav: Dashboard, Review, Assets, Audit.

### Acceptance Criteria
- [ ] Nav bar: Dashboard, Review, Assets, Audit (Export deferred)
- [ ] Empty states when pipeline not started
- [ ] Usable at >=768px

### Dependencies
- #FEAT-16 (must be closed first)
- #US-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-16`, `epic:EPIC-06`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-26-01` — Build app shell with React Router
- [ ] `T-26-02` — Implement nav bar and route guards
- [ ] `T-26-03` — Add empty states per screen

---

## Issue 13: [US-07] Start pipeline workflow

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 13  
**Story Points:** 5  
**Parent:** #FEAT-03  
**Epic:** #EPIC-02  

### Title
[US-07] Start pipeline workflow

### Description
As a creator, I want to start the 4-stage production pipeline after entering my idea.

### Business Value
4-stage governed pipeline automation.

### Acceptance Criteria
- [ ] POST /pipeline/start creates SparkPipelineWorkflow (4 stages)
- [ ] Status shows STORY_GENERATING or STORY_REVIEW
- [ ] Workflow ends at COMPLETED after storyboard approval (no video stage)
- [ ] PipelineStarted audit event recorded

### Dependencies
- #FEAT-03 (must be closed first)
- #US-04 (must be closed first)
- #US-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `user-story`, `workflow`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-07-01` — Deploy Temporal server with PostgreSQL persistence
- [ ] `T-07-02` — Implement SparkPipelineWorkflow skeleton
- [ ] `T-07-03` — Implement POST /pipeline/start API
- [ ] `T-07-04` — Implement GET /pipeline/status API
- [ ] `T-07-05` — Register Temporal worker pod
- [ ] `T-07-06` — Write audit event on pipeline start

---

## Issue 14: [US-08] Approve or reject stage output

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 14  
**Story Points:** 5  
**Parent:** #FEAT-03  
**Epic:** #EPIC-02  

### Title
[US-08] Approve or reject stage output

### Description
As a creator, I want to approve or reject AI output at each stage.

### Business Value
4 human gates enforced (SC-03 adapted).

### Acceptance Criteria
- [ ] POST /pipeline/approve with GRANT creates immutable approvals row
- [ ] Approve advances workflow
- [ ] Reject with note keeps stage
- [ ] ApprovalGranted audit event logged

### Dependencies
- #FEAT-03 (must be closed first)
- #US-07 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `user-story`, `workflow`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-08-01` — Implement approval API endpoints
- [ ] `T-08-02` — Wire Temporal approve/reject signals
- [ ] `T-08-03` — Create immutable approvals table writes
- [ ] `T-08-04` — Handle reject without workflow advance
- [ ] `T-08-05` — Integration test approve advances stage

---

## Issue 15: [US-09] Regenerate after rejection

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 15  
**Story Points:** 3  
**Parent:** #FEAT-03  
**Epic:** #EPIC-02  

### Title
[US-09] Regenerate after rejection

### Description
As a creator, I want to regenerate AI output after rejecting it.

### Business Value
Regenerate without restart.

### Acceptance Criteria
- [ ] POST /pipeline/regenerate triggers agent for current stage
- [ ] New asset_version with incremented version
- [ ] Max 3 regenerations per stage (429 after)
- [ ] Rejection note passed to agent

### Dependencies
- #FEAT-03 (must be closed first)
- #US-07 (must be closed first)
- #US-08 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `user-story`, `workflow`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-09-01` — Implement regenerate endpoint
- [ ] `T-09-02` — Pass rejection note to activity input
- [ ] `T-09-03` — Enforce max 3 regenerations per stage
- [ ] `T-09-04` — Increment version on regenerate

---

## Issue 16: [US-24] Pipeline survives worker restart

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 16  
**Story Points:** 3  
**Parent:** #FEAT-03  
**Epic:** #EPIC-06  

### Title
[US-24] Pipeline survives worker restart

### Description
As a platform engineer, I want workflow resume after restart.

### Business Value
ComfyUI jobs survive worker restart.

### Acceptance Criteria
- [ ] Worker restart resumes within 2 min
- [ ] Approve signal works after API restart
- [ ] No duplicate asset versions

### Dependencies
- #FEAT-03 (must be closed first)
- #US-07 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-06`, `priority:p0`, `user-story`, `workflow`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-24-01` — Configure Temporal worker graceful shutdown
- [ ] `T-24-02` — Test worker restart during review wait
- [ ] `T-24-03` — Test worker restart during activity execution
- [ ] `T-24-04` — Document recovery behavior

---

## Issue 17: [US-25] API token authentication

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 17  
**Story Points:** 2  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-06  

### Title
[US-25] API token authentication

### Description
As a platform engineer, I want Bearer token on mutating endpoints.

### Business Value
LAN token auth on mutating APIs.

### Acceptance Criteria
- [ ] No token on POST returns 401
- [ ] Valid Bearer succeeds
- [ ] Web client sends token from env

### Dependencies
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-INFRA`, `epic:EPIC-06`, `priority:p0`, `user-story`, `security`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-25-01` — Implement Bearer token middleware
- [ ] `T-25-02` — Configure token via environment variable
- [ ] `T-25-03` — Wire token into React API client

---

## Issue 18: [US-10] View pipeline status dashboard

**Type:** User Story  
**Milestone:** S2  
**Implementation Order:** 18  
**Story Points:** 3  
**Parent:** #FEAT-16  
**Epic:** #EPIC-02  

### Title
[US-10] View pipeline status dashboard

### Description
As a creator, I want a dashboard showing stage and progress.

### Business Value
4-step progress UI.

### Acceptance Criteria
- [ ] Dashboard shows 4-stage progress (Idea, Story, Script, Storyboard)
- [ ] REVIEW shows Go to Review CTA
- [ ] GENERATING polls every 5s

### Dependencies
- #FEAT-16 (must be closed first)
- #US-26 (must be closed first)
- #US-07 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s2`, `feature:F-16`, `epic:EPIC-02`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-10-01` — Implement dashboard API aggregation endpoint
- [ ] `T-10-02` — Build Dashboard screen (React)
- [ ] `T-10-03` — Add 5-stage progress stepper component
- [ ] `T-10-04` — Implement status polling hook

---

## Issue 19: [EPIC-03] Idea, Story & Script Stages

**Type:** Epic  
**Milestone:** S3  
**Implementation Order:** 19  
**Epic:** #EPIC-03  

### Title
[EPIC-03] Idea, Story & Script Stages

### Description
Idea capture through approved script using Story Architect and Screenwriter agents.

### Business Value
Text pipeline via local Ollama — Story Architect and Screenwriter agents.

### Acceptance Criteria
- [ ] Creator completes Idea to approved Story to approved Script in one run
- [ ] Assets versioned in MinIO
- [ ] Agent invocations logged with model ID

### Dependencies
- #EPIC-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `epic`, `sprint:s3`, `epic:EPIC-03`, `priority:p0`, `aimpos-spark`, `agents`, `story`, `script`

### Estimated Complexity
XL

### Definition of Done
- [ ] All child P0 features and stories closed
- [ ] Epic AC verified on Olares
- [ ] No P0 defects

---

## Issue 20: [FEAT-01] Project Bootstrap

**Type:** Feature  
**Milestone:** S1  
**Implementation Order:** 20  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-01] Project Bootstrap

### Description
Default project on startup. F-01.

### Business Value
Default project on startup. F-01.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s1`, `feature:F-01`, `epic:EPIC-03`, `priority:p0`, `feature`, `F-01`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 21: [FEAT-02] Capture Idea

**Type:** Feature  
**Milestone:** S3  
**Implementation Order:** 21  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-02] Capture Idea

### Description
Title, paragraph, optional style note. F-02.

### Business Value
Title, paragraph, optional style note. F-02.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-01 (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s3`, `feature:F-02`, `epic:EPIC-03`, `priority:p0`, `feature`, `F-02`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 22: [FEAT-04] AI Story Generation

**Type:** Feature  
**Milestone:** S3  
**Implementation Order:** 22  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-04] AI Story Generation

### Description
Story Architect agent generates treatment. F-04.

### Business Value
Story Architect agent generates treatment. F-04.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-02 (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s3`, `feature:F-04`, `epic:EPIC-03`, `priority:p0`, `feature`, `F-04`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 23: [FEAT-05] Story Review & Approval

**Type:** Feature  
**Milestone:** S3  
**Implementation Order:** 23  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-05] Story Review & Approval

### Description
Read, edit, approve/reject story. F-05.

### Business Value
Read, edit, approve/reject story. F-05.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-04 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s3`, `feature:F-05`, `epic:EPIC-03`, `priority:p0`, `feature`, `F-05`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 24: [FEAT-06] AI Script Generation

**Type:** Feature  
**Milestone:** S3  
**Implementation Order:** 24  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-06] AI Script Generation

### Description
Screenwriter agent generates one-scene Fountain script. F-06.

### Business Value
Screenwriter agent generates one-scene Fountain script. F-06.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-05 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s3`, `feature:F-06`, `epic:EPIC-03`, `priority:p0`, `feature`, `F-06`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 25: [FEAT-07] Script Review & Approval

**Type:** Feature  
**Milestone:** S3  
**Implementation Order:** 25  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-07] Script Review & Approval

### Description
Preview script, approve/reject. F-07.

### Business Value
Preview script, approve/reject. F-07.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-06 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s3`, `feature:F-07`, `epic:EPIC-03`, `priority:p0`, `feature`, `F-07`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 26: [FEAT-13] Audit Log Viewer

**Type:** Feature  
**Milestone:** S3  
**Implementation Order:** 26  
**Parent:** #EPIC-06  
**Epic:** #EPIC-06  

### Title
[FEAT-13] Audit Log Viewer

### Description
Chronological pipeline event log. F-13.

### Business Value
Chronological pipeline event log. F-13.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-06 (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s3`, `feature:F-13`, `epic:EPIC-06`, `priority:p0`, `feature`, `F-13`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 27: [US-11] Enter production idea

**Type:** User Story  
**Milestone:** S3  
**Implementation Order:** 27  
**Story Points:** 2  
**Parent:** #FEAT-02  
**Epic:** #EPIC-03  

### Title
[US-11] Enter production idea

### Description
As a creator, I want to enter title, paragraph, and style note.

### Business Value
MVP entry — creator's idea.

### Acceptance Criteria
- [ ] Submit idea stores idea
- [ ] txt v1 in MinIO
- [ ] Style note in metadata
- [ ] Appears under stage IDEA
- [ ] Validation on required fields and 50-2000 char paragraph

### Dependencies
- #FEAT-02 (must be closed first)
- #US-05 (must be closed first)
- #US-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s3`, `feature:F-02`, `epic:EPIC-03`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-11-01` — Implement POST /ideas endpoint
- [ ] `T-11-02` — Build idea capture form on Dashboard
- [ ] `T-11-03` — Validate input length and required fields
- [ ] `T-11-04` — Store idea as asset_version stage=IDEA

---

## Issue 28: [US-12] Generate story from idea

**Type:** User Story  
**Milestone:** S3  
**Implementation Order:** 28  
**Story Points:** 5  
**Parent:** #FEAT-04  
**Epic:** #EPIC-03  

### Title
[US-12] Generate story from idea

### Description
As a creator, I want Story Architect to generate a treatment.

### Business Value
Ollama Story Architect output.

### Acceptance Criteria
- [ ] LangGraph Story Architect invoked
- [ ] story
- [ ] md on ai-draft branch
- [ ] Audit logs model_id and agent
- [ ] Local-only Ollama
- [ ] Workflow to STORY_REVIEW

### Dependencies
- #FEAT-04 (must be closed first)
- #US-05 (must be closed first)
- #US-06 (must be closed first)
- #US-07 (must be closed first)
- #US-11 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s3`, `feature:F-04`, `epic:EPIC-03`, `priority:p0`, `user-story`, `ai`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-12-01` — Implement LangGraph Story Architect graph
- [ ] `T-12-02` — Implement run_story_agent Temporal activity
- [ ] `T-12-03` — Create story prompt template with idea injection
- [ ] `T-12-04` — Store story output as asset version
- [ ] `T-12-05` — Log agent invocation to audit_events
- [ ] `T-12-06` — Integration test story generation (mock Ollama)

---

## Issue 29: [US-13] Review and edit story

**Type:** User Story  
**Milestone:** S3  
**Implementation Order:** 29  
**Story Points:** 3  
**Parent:** #FEAT-05  
**Epic:** #EPIC-03  

### Title
[US-13] Review and edit story

### Description
As a creator, I want to read, edit, and approve the story.

### Business Value
Edit and approve treatment.

### Acceptance Criteria
- [ ] Review screen shows editable treatment
- [ ] Save creates human-edit version
- [ ] Approve advances pipeline
- [ ] Reject enables regenerate

### Dependencies
- #FEAT-05 (must be closed first)
- #US-26 (must be closed first)
- #US-08 (must be closed first)
- #US-12 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s3`, `feature:F-05`, `epic:EPIC-03`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-13-01` — Build Review screen — story mode
- [ ] `T-13-02` — Implement PUT /assets/{id} text update
- [ ] `T-13-03` — Wire Approve/Reject buttons to pipeline API
- [ ] `T-13-04` — Display rejection note input on reject

---

## Issue 30: [US-14] Generate one-scene script

**Type:** User Story  
**Milestone:** S3  
**Implementation Order:** 30  
**Story Points:** 5  
**Parent:** #FEAT-06  
**Epic:** #EPIC-03  

### Title
[US-14] Generate one-scene script

### Description
As a creator, I want Screenwriter to generate a Fountain script.

### Business Value
Ollama Screenwriter output.

### Acceptance Criteria
- [ ] Exactly 1 scene Fountain script
- [ ] script
- [ ] fountain is_ai_generated=true
- [ ] Lineage edge story to script
- [ ] Workflow to SCRIPT_REVIEW

### Dependencies
- #FEAT-06 (must be closed first)
- #US-05 (must be closed first)
- #US-07 (must be closed first)
- #US-13 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s3`, `feature:F-06`, `epic:EPIC-03`, `priority:p0`, `user-story`, `ai`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-14-01` — Implement LangGraph Screenwriter graph
- [ ] `T-14-02` — Implement run_script_agent Temporal activity
- [ ] `T-14-03` — Add Fountain format validation
- [ ] `T-14-04` — Record lineage edge story to script
- [ ] `T-14-05` — Store script asset version

---

## Issue 31: [US-15] Review and approve script

**Type:** User Story  
**Milestone:** S3  
**Implementation Order:** 31  
**Story Points:** 3  
**Parent:** #FEAT-07  
**Epic:** #EPIC-03  

### Title
[US-15] Review and approve script

### Description
As a creator, I want to preview and approve the script.

### Business Value
Approve script before ComfyUI.

### Acceptance Criteria
- [ ] Fountain rendered with formatting
- [ ] Approve advances to STORYBOARD_GENERATING
- [ ] Reject/regenerate works
- [ ] Approved version marked in DB

### Dependencies
- #FEAT-07 (must be closed first)
- #US-26 (must be closed first)
- #US-08 (must be closed first)
- #US-14 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s3`, `feature:F-07`, `epic:EPIC-03`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-15-01` — Build Review screen — script mode with Fountain preview
- [ ] `T-15-02` — Add basic Fountain-to-HTML formatter
- [ ] `T-15-03` — Wire approve/reject for script stage
- [ ] `T-15-04` — Mark approved script version in DB

---

## Issue 32: [US-23] View audit trail

**Type:** User Story  
**Milestone:** S3  
**Implementation Order:** 32  
**Story Points:** 3  
**Parent:** #FEAT-13  
**Epic:** #EPIC-06  

### Title
[US-23] View audit trail

### Description
As a creator, I want chronological pipeline event log.

### Business Value
Verify 100% local AI calls logged.

### Acceptance Criteria
- [ ] Events: PipelineStarted, AgentTaskCompleted, ApprovalGranted, Rejected, Completed
- [ ] Agent events show model_id
- [ ] Append-only
- [ ] Included in export

### Dependencies
- #FEAT-13 (must be closed first)
- #US-04 (must be closed first)
- #US-26 (must be closed first)
- #US-07 (must be closed first)
- #US-12 (must be closed first)
- #US-14 (must be closed first)
- #US-16 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s3`, `feature:F-13`, `epic:EPIC-06`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-23-01` — Implement GET /audit?pipeline_run_id= API
- [ ] `T-23-02` — Build Audit screen table
- [ ] `T-23-03` — Standardize audit event schema across worker
- [ ] `T-23-04` — Include audit summary in export manifest

---

## Issue 33: [EPIC-04] Storyboard Stage

**Type:** Epic  
**Milestone:** S4  
**Implementation Order:** 33  
**Epic:** #EPIC-04  

### Title
[EPIC-04] Storyboard Stage

### Description
ComfyUI storyboard from approved script. Gallery review. **Pipeline completes when frames are approved.**

### Business Value
**Terminal delivery epic for Visual MVP.** Approved storyboard frames = MVP complete.

### Acceptance Criteria
- [ ] 4–6 frames generated locally via ComfyUI
- [ ] Gallery approve/reject/regenerate
- [ ] GPU sequenced without OOM
- [ ] Approved frames = Visual MVP complete

### Dependencies
- #EPIC-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `epic`, `sprint:s4`, `epic:EPIC-04`, `priority:p0`, `aimpos-spark`, `storyboard`, `comfyui`

### Estimated Complexity
XL

### Definition of Done
- [ ] All child P0 features and stories closed
- [ ] Epic AC verified on Olares
- [ ] No P0 defects

---

## Issue 34: [FEAT-08] AI Storyboard Generation

**Type:** Feature  
**Milestone:** S4  
**Implementation Order:** 34  
**Parent:** #EPIC-04  
**Epic:** #EPIC-04  

### Title
[FEAT-08] AI Storyboard Generation

### Description
Cinematography agent + ComfyUI frames. F-08.

### Business Value
Local ComfyUI storyboard frames — visual MVP climax.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-04 (must be closed first)
- #FEAT-07 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s4`, `feature:F-08`, `epic:EPIC-04`, `priority:p0`, `feature`, `F-08`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 35: [FEAT-09] Storyboard Gallery Review

**Type:** Feature  
**Milestone:** S4  
**Implementation Order:** 35  
**Parent:** #EPIC-04  
**Epic:** #EPIC-04  

### Title
[FEAT-09] Storyboard Gallery Review

### Description
Grid gallery, approve/reject frames. F-09.

### Business Value
Human curation of frame set; pipeline completes on approval.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-04 (must be closed first)
- #FEAT-08 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s4`, `feature:F-09`, `epic:EPIC-04`, `priority:p0`, `feature`, `F-09`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 36: [FEAT-12] Asset Version History

**Type:** Feature  
**Milestone:** S4  
**Implementation Order:** 36  
**Parent:** #EPIC-06  
**Epic:** #EPIC-06  

### Title
[FEAT-12] Asset Version History

### Description
Browse versions per stage. F-12.

### Business Value
Browse versions per stage. F-12.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-06 (must be closed first)
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s4`, `feature:F-12`, `epic:EPIC-06`, `priority:p0`, `feature`, `F-12`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 37: [FEAT-14] Lineage Summary

**Type:** Feature  
**Milestone:** S4  
**Implementation Order:** 37  
**Parent:** #EPIC-05  
**Epic:** #EPIC-04  

### Title
[FEAT-14] Lineage Summary

### Description
Lineage chain: idea → story → script → frames (video deferred). F-14.

### Business Value
Lineage chain Idea→Story→Script→Frames (no video node).

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-05 (must be closed first)
- #FEAT-09 (must be closed first)
- #EPIC-04 (must be closed first)

### Priority
P1

### Labels
`aimpos-spark`, `visual-mvp`, `feature`, `sprint:s4`, `feature:F-14`, `epic:EPIC-04`, `priority:p1`, `feature`, `F-14`

### Estimated Complexity
Large

### Definition of Done
- [ ] All child stories closed
- [ ] Traced to F-xx in release notes
- [ ] PO acceptance

---

## Issue 38: [US-16] Generate storyboard frames

**Type:** User Story  
**Milestone:** S4  
**Implementation Order:** 38  
**Story Points:** 8  
**Parent:** #FEAT-08  
**Epic:** #EPIC-04  

### Title
[US-16] Generate storyboard frames

### Description
As a creator, I want 4-6 storyboard images from my script.

### Business Value
ComfyUI generates 4–6 frames locally.

### Acceptance Criteria
- [ ] 4-6 PNG frames via ComfyUI
- [ ] Ollama unloaded before GPU
- [ ] Lineage script to frames
- [ ] STORYBOARD_REVIEW on success
- [ ] Retry 2x then FAILED

### Dependencies
- #FEAT-08 (must be closed first)
- #US-05 (must be closed first)
- #US-06 (must be closed first)
- #US-07 (must be closed first)
- #US-15 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s4`, `feature:F-08`, `epic:EPIC-04`, `priority:p0`, `user-story`, `ai`

### Estimated Complexity
High (8 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-16-01` — Implement Cinematography agent (planning via Ollama)
- [ ] `T-16-02` — Implement ComfyUI tool — SDXL/Flux workflow
- [ ] `T-16-03` — Implement run_storyboard_agent Temporal activity
- [ ] `T-16-04` — GPU sequencing: unload Ollama before ComfyUI
- [ ] `T-16-05` — Store multiple frame assets per run
- [ ] `T-16-06` — Record lineage edges script to frames
- [ ] `T-16-07` — ComfyUI error handling and retry

---

## Issue 39: [US-17] Review storyboard gallery

**Type:** User Story  
**Milestone:** S4  
**Implementation Order:** 39  
**Story Points:** 3  
**Parent:** #FEAT-09  
**Epic:** #EPIC-04  

### Title
[US-17] Review storyboard gallery

### Description
As a creator, I want to view frames in a grid and approve or reject.

### Business Value
Approve frames → pipeline COMPLETED.

### Acceptance Criteria
- [ ] Grid of 4–6 images
- [ ] Lightbox preview
- [ ] Approve-all sets pipeline COMPLETED
- [ ] Reject triggers regenerate
- [ ] AI badge on frames

### Dependencies
- #FEAT-09 (must be closed first)
- #US-26 (must be closed first)
- #US-08 (must be closed first)
- #US-16 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s4`, `feature:F-09`, `epic:EPIC-04`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-17-01` — Build Review screen — storyboard gallery mode
- [ ] `T-17-02` — Implement image preview lightbox
- [ ] `T-17-03` — Wire approve-all / reject for storyboard stage
- [ ] `T-17-04` — Display AI badge and model on frames

---

## Issue 40: [US-20] View asset lineage chain

**Type:** User Story  
**Milestone:** S4  
**Implementation Order:** 40  
**Story Points:** 3  
**Parent:** #FEAT-14  
**Epic:** #EPIC-04  

### Title
[US-20] View asset lineage chain

### Description
As a creator, I want to see the chain from idea to storyboard frames.

### Business Value
Traceability Idea→Frames without Neo4j.

### Acceptance Criteria
- [ ] Ordered chain: idea → story → script → frames
- [ ] Click node shows metadata
- [ ] Data from lineage_edges in PostgreSQL
- [ ] No video node

### Dependencies
- #FEAT-14 (must be closed first)
- #US-14 (must be closed first)
- #US-16 (must be closed first)

### Priority
P1

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s4`, `feature:F-14`, `epic:EPIC-04`, `priority:p1`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-20-01` — Implement GET /lineage/{pipeline_run_id} API
- [ ] `T-20-02` — Build Lineage summary component on Export screen
- [ ] `T-20-03` — Render chain visualization (simple list/tree)

---

## Issue 41: [US-22] Browse asset versions

**Type:** User Story  
**Milestone:** S4  
**Implementation Order:** 41  
**Story Points:** 3  
**Parent:** #FEAT-12  
**Epic:** #EPIC-06  

### Title
[US-22] Browse asset versions

### Description
As a creator, I want to see all versions per stage.

### Business Value
Browse drafts and approvals.

### Acceptance Criteria
- [ ] Versions grouped by stage
- [ ] Newest first
- [ ] Preview or download per version
- [ ] Shows is_ai_generated, branch, content_hash

### Dependencies
- #FEAT-12 (must be closed first)
- #US-05 (must be closed first)
- #US-26 (must be closed first)
- #US-12 (must be closed first)
- #US-16 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s4`, `feature:F-12`, `epic:EPIC-06`, `priority:p0`, `user-story`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-22-01` — Implement GET /assets?project_id=&stage= API
- [ ] `T-22-02` — Build Assets screen with stage tabs
- [ ] `T-22-03` — Implement version list and preview components
- [ ] `T-22-04` — Add download link per version

---

## Issue 42: [EPIC-06] Governance, Assets & Console

**Type:** Epic  
**Milestone:** S1-S5  
**Implementation Order:** 42  
**Epic:** #EPIC-06  

### Title
[EPIC-06] Governance, Assets & Console

### Description
Asset history, audit log, auth token, navigation shell, durability.

### Business Value
Governance, audit, asset history, and creator UX across the 4-stage pipeline.

### Acceptance Criteria
- [ ] All assets versioned and browsable
- [ ] Full audit trail visible
- [ ] Pipeline survives worker restart
- [ ] API token auth on mutating endpoints

### Dependencies
- #EPIC-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `epic`, `epic:EPIC-06`, `priority:p0`, `aimpos-spark`, `governance`, `ui`

### Estimated Complexity
XL

### Definition of Done
- [ ] All child P0 features and stories closed
- [ ] Epic AC verified on Olares
- [ ] No P0 defects

---

## Issue 43: [US-V01] Visual MVP demo acceptance validation

**Type:** User Story  
**Milestone:** S4  
**Implementation Order:** 43  
**Story Points:** 2  
**Parent:** #FEAT-09  
**Epic:** #EPIC-04  

### Title
[US-V01] Visual MVP demo acceptance validation

### Description
As a product owner, I want the Visual MVP demo script executable end-to-end on Olares.

### Business Value
Proves Visual MVP: Idea→approved storyboard E2E on Olares.

### Acceptance Criteria
- [ ] 1
- [ ] Enter idea on fresh project
- [ ] 2
- [ ] Start pipeline
- [ ] 3
- [ ] Approve story with one edit
- [ ] 4
- [ ] Reject script once, regenerate, approve
- [ ] 5
- [ ] Approve all storyboard frames
- [ ] 6
- [ ] Pipeline status COMPLETED
- [ ] 7
- [ ] Audit log shows 4 approvals and 3+ local model invocations
- [ ] 8
- [ ] Lineage shows idea to frames
- [ ] 9
- [ ] Restart worker — state unchanged
- [ ] Pass: all steps without manual DB intervention
- [ ] 100% local inference (SC-02)

### Dependencies
- #FEAT-09 (must be closed first)
- #US-17 (must be closed first)
- #US-20 (must be closed first)
- #US-23 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `visual-mvp`, `user-story`, `sprint:s4`, `feature:F-09`, `epic:EPIC-04`, `priority:p0`, `user-story`, `qa`, `visual-mvp`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] Tasks complete
- [ ] AC verified
- [ ] Merged to main
- [ ] Dependencies regression-free

### Implementation Tasks
- [ ] `T-V01-01` — Execute Visual MVP demo script on Olares
- [ ] `T-V01-02` — Verify SC-02 SC-03 SC-04 SC-05 SC-06 SC-07 SC-08 for 4-stage scope
- [ ] `T-V01-03` — Document deferred items (video, export) in release notes
- [ ] `T-V01-04` — Stakeholder sign-off on Visual MVP

---
