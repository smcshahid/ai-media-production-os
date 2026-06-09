# AIMPOS-Spark — GitHub Issues

**Status:** ARCHIVED — Superseded by [GitHub Issues - Visual MVP.md](./GitHub%20Issues%20-%20Visual%20MVP.md). Do not use for execution.

**Product:** AIMPOS-Spark MVP  
**Format:** GitHub Issue Markdown (copy body into issue or use `gh issue create`)  
**Total Issues:** 50 (6 Epics · 17 Features · 27 User Stories)  
**Source:** [MVP Backlog.md](./MVP%20Backlog.md) · [MVP Dependency Map.md](./MVP%20Dependency%20Map.md)

---

## How to Import

```bash
# Example: create a user story issue
gh issue create --title "[US-02] Deploy MVP stack on Olares" \
  --label "aimpos-spark,user-story,sprint:s1,priority:p0,devops" \
  --milestone "Sprint 1" \
  --body-file issues/US-02.md
```

**Recommended GitHub setup:**
- Milestones: `Sprint 1` … `Sprint 5`
- Labels: `epic`, `feature`, `user-story`, `priority:p0`, `priority:p1`, `sprint:s1`–`sprint:s5`
- Parent links: use GitHub Projects v2 sub-issue relationships or `Depends on #N` in descriptions

---

## Issue Index

| # | ID | Title | Priority | Sprint | Complexity |
|---|-----|-------|----------|--------|------------|
| 1 | EPIC-01 | Platform Foundation | P0 | S1 | XL (multi-sprint) |
| 2 | EPIC-02 | Pipeline Orchestration | P0 | S2 | XL (multi-sprint) |
| 3 | EPIC-03 | Idea, Story & Script Stages | P0 | S3 | XL (multi-sprint) |
| 4 | EPIC-04 | Storyboard Stage | P0 | S4 | XL (multi-sprint) |
| 5 | EPIC-05 | Video & Pipeline Completion | P0 | S5 | XL (multi-sprint) |
| 6 | EPIC-06 | Governance, Assets & Console | P0 | S1-S5 | XL (multi-sprint) |
| 7 | FEAT-01 | Project Bootstrap | P0 | S1 | Large (multi-story) |
| 8 | FEAT-INFRA | Infrastructure Enabler | P0 | S1 | Large (multi-story) |
| 9 | FEAT-03 | Start Production Pipeline | P0 | S2 | Large (multi-story) |
| 10 | FEAT-16 | Pipeline Status Dashboard | P0 | S2 | Large (multi-story) |
| 11 | FEAT-02 | Capture Idea | P0 | S3 | Large (multi-story) |
| 12 | FEAT-04 | AI Story Generation | P0 | S3 | Large (multi-story) |
| 13 | FEAT-05 | Story Review & Approval | P0 | S3 | Large (multi-story) |
| 14 | FEAT-06 | AI Script Generation | P0 | S3 | Large (multi-story) |
| 15 | FEAT-07 | Script Review & Approval | P0 | S3 | Large (multi-story) |
| 16 | FEAT-08 | AI Storyboard Generation | P0 | S4 | Large (multi-story) |
| 17 | FEAT-09 | Storyboard Gallery Review | P0 | S4 | Large (multi-story) |
| 18 | FEAT-10 | AI Short Video Generation | P0 | S5 | Large (multi-story) |
| 19 | FEAT-11 | Video Preview & Approval | P0 | S5 | Large (multi-story) |
| 20 | FEAT-14 | Lineage Summary | P1 | S5 | Large (multi-story) |
| 21 | FEAT-15 | Export Final Bundle | P1 | S5 | Large (multi-story) |
| 22 | FEAT-12 | Asset Version History | P0 | S4 | Large (multi-story) |
| 23 | FEAT-13 | Audit Log Viewer | P0 | S3 | Large (multi-story) |
| 24 | US-02 | Deploy MVP stack on Olares | P0 | S1 | Medium (5 SP) |
| 25 | US-04 | Database schema foundation | P0 | S1 | Low (3 SP) |
| 26 | US-03 | API health and logging | P0 | S1 | Low (2 SP) |
| 27 | US-05 | MinIO asset upload service | P0 | S1 | Low (3 SP) |
| 28 | US-06 | Ollama and ComfyUI smoke test | P0 | S1 | Low (3 SP) |
| 29 | US-01 | Create default project | P0 | S1 | Low (2 SP) |
| 30 | US-26 | App navigation shell | P0 | S2 | Low (2 SP) |
| 31 | US-07 | Start pipeline workflow | P0 | S2 | Medium (5 SP) |
| 32 | US-08 | Approve or reject stage output | P0 | S2 | Medium (5 SP) |
| 33 | US-09 | Regenerate after rejection | P0 | S2 | Low (3 SP) |
| 34 | US-24 | Pipeline survives worker restart | P0 | S2 | Low (3 SP) |
| 35 | US-25 | API token authentication | P0 | S2 | Low (2 SP) |
| 36 | US-10 | View pipeline status dashboard | P0 | S2 | Low (3 SP) |
| 37 | US-11 | Enter production idea | P0 | S3 | Low (2 SP) |
| 38 | US-12 | Generate story from idea | P0 | S3 | Medium (5 SP) |
| 39 | US-13 | Review and edit story | P0 | S3 | Low (3 SP) |
| 40 | US-14 | Generate one-scene script | P0 | S3 | Medium (5 SP) |
| 41 | US-15 | Review and approve script | P0 | S3 | Low (3 SP) |
| 42 | US-23 | View audit trail | P0 | S3 | Low (3 SP) |
| 43 | US-16 | Generate storyboard frames | P0 | S4 | High (8 SP) |
| 44 | US-17 | Review storyboard gallery | P0 | S4 | Low (3 SP) |
| 45 | US-22 | Browse asset versions | P0 | S4 | Low (3 SP) |
| 46 | US-18 | Generate short video clip | P0 | S5 | High (8 SP) |
| 47 | US-19 | Preview and approve video | P0 | S5 | Low (3 SP) |
| 48 | US-20 | View asset lineage chain | P1 | S5 | Low (3 SP) |
| 49 | US-21 | Download production bundle | P1 | S5 | Low (3 SP) |
| 50 | US-27 | MVP demo acceptance validation | P0 | S5 | Low (2 SP) |

---

## Issue 1: [EPIC-01] Platform Foundation

**Type:** Epic  
**Milestone:** S1  
**Epic:** #EPIC-01  

### Title
[EPIC-01] Platform Foundation

### Description
Runnable Olares stack: PostgreSQL, MinIO, Redis, Ollama, ComfyUI, API skeleton, health checks.

### Business Value
Enables sovereign local-AI production on Olares. Without a runnable stack, no MVP capability can be demonstrated. De-risks GPU and ComfyUI early (week 2 kill criterion).

### Acceptance Criteria
- [ ] Docker Compose starts all services with one command
- [ ] /health returns OK
- [ ] ComfyUI test image succeeds
- [ ] Ollama responds locally with zero egress

### Dependencies
_None — can start immediately._

### Priority
P0

### Labels
`aimpos-spark`, `epic`, `sprint:s1`, `epic:EPIC-01`, `priority:p0`, `foundation`, `olares`

### Estimated Complexity
XL (multi-sprint)

### Definition of Done
- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes

---

## Issue 2: [EPIC-02] Pipeline Orchestration

**Type:** Epic  
**Milestone:** S2  
**Epic:** #EPIC-02  

### Title
[EPIC-02] Pipeline Orchestration

### Description
Temporal workflow skeleton with start, status, approve/reject signals, audit events.

### Business Value
Proves workflow-driven production with human-in-the-loop gates — the core AIMPOS architectural principle. Unblocks all five pipeline stages and SC-03, SC-06.

### Acceptance Criteria
- [ ] User starts pipeline and sees status transitions
- [ ] Workflow pauses at review gates
- [ ] Approve advances; reject keeps stage
- [ ] All transitions in audit_events

### Dependencies
- #EPIC-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `epic`, `sprint:s2`, `epic:EPIC-02`, `priority:p0`, `temporal`, `workflow`

### Estimated Complexity
XL (multi-sprint)

### Definition of Done
- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes

---

## Issue 3: [EPIC-03] Idea, Story & Script Stages

**Type:** Epic  
**Milestone:** S3  
**Epic:** #EPIC-03  

### Title
[EPIC-03] Idea, Story & Script Stages

### Description
Idea capture through approved script using Story Architect and Screenwriter agents.

### Business Value
Delivers the text half of the creative pipeline (Idea → Story → Script). Validates LangGraph agents, Ollama inference, and first three approval gates.

### Acceptance Criteria
- [ ] Creator completes Idea to approved Story to approved Script in one run
- [ ] Assets versioned in MinIO
- [ ] Agent invocations logged with model ID

### Dependencies
- #EPIC-01 (must be closed first)
- #EPIC-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `epic`, `sprint:s3`, `epic:EPIC-03`, `priority:p0`, `agents`, `story`, `script`

### Estimated Complexity
XL (multi-sprint)

### Definition of Done
- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes

---

## Issue 4: [EPIC-04] Storyboard Stage

**Type:** Epic  
**Milestone:** S4  
**Epic:** #EPIC-04  

### Title
[EPIC-04] Storyboard Stage

### Description
ComfyUI storyboard frames from approved script, gallery review, approval.

### Business Value
Proves local visual AI via ComfyUI. Transforms approved script into reviewable storyboard frames — prerequisite for video.

### Acceptance Criteria
- [ ] 4-6 frames generated locally
- [ ] Gallery review with approve/reject/regenerate
- [ ] GPU jobs sequenced without OOM

### Dependencies
- #EPIC-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `epic`, `sprint:s4`, `epic:EPIC-04`, `priority:p0`, `storyboard`, `comfyui`

### Estimated Complexity
XL (multi-sprint)

### Definition of Done
- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes

---

## Issue 5: [EPIC-05] Video & Pipeline Completion

**Type:** Epic  
**Milestone:** S5  
**Epic:** #EPIC-05  

### Title
[EPIC-05] Video & Pipeline Completion

### Description
Short video generation, approval, export bundle, lineage summary.

### Business Value
Completes the MVP promise: Idea to approved short video with export. Satisfies SC-01 (end-to-end run) and stakeholder demo.

### Acceptance Criteria
- [ ] 15-30s video generated locally
- [ ] Full pipeline end-to-end per demo script
- [ ] Export ZIP with manifest

### Dependencies
- #EPIC-04 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `epic`, `sprint:s5`, `epic:EPIC-05`, `priority:p0`, `video`, `export`

### Estimated Complexity
XL (multi-sprint)

### Definition of Done
- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes

---

## Issue 6: [EPIC-06] Governance, Assets & Console

**Type:** Epic  
**Milestone:** Cross-sprint  
**Epic:** #EPIC-06  

### Title
[EPIC-06] Governance, Assets & Console

### Description
Asset history, audit log, auth token, navigation shell, durability.

### Business Value
Provides trust, traceability, and usability across the pipeline. Supports SC-04 (versioning), SC-05 (audit), SC-08 (comprehension).

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
`aimpos-spark`, `epic`, `epic:EPIC-06`, `priority:p0`, `governance`, `ui`

### Estimated Complexity
XL (multi-sprint)

### Definition of Done
- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes

---

## Issue 7: [FEAT-01] Project Bootstrap

**Type:** Feature  
**Milestone:** S1  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-01] Project Bootstrap

### Description
Default project on startup. F-01.

### Business Value
Removes setup friction for solo creator; one-click start to production.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s1`, `feature:F-01`, `epic:EPIC-03`, `priority:p0`, `F-01`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 8: [FEAT-INFRA] Infrastructure Enabler

**Type:** Feature  
**Milestone:** S1  
**Parent:** #EPIC-01  
**Epic:** #EPIC-01  

### Title
[FEAT-INFRA] Infrastructure Enabler

### Description
Docker Compose, health, schema, MinIO, Ollama/ComfyUI smoke tests.

### Business Value
Foundation for all persistence, assets, and AI runtimes. Investment here prevents 1–2 weeks rework later.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `infrastructure`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 9: [FEAT-03] Start Production Pipeline

**Type:** Feature  
**Milestone:** S2  
**Parent:** #EPIC-02  
**Epic:** #EPIC-02  

### Title
[FEAT-03] Start Production Pipeline

### Description
Start Temporal workflow after idea capture. F-03.

### Business Value
Single action starts governed production; replaces ad-hoc scripts with Temporal control.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-02 (must be closed first)
- #FEAT-INFRA (must be closed first)
- #FEAT-01 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `F-03`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 10: [FEAT-16] Pipeline Status Dashboard

**Type:** Feature  
**Milestone:** S2  
**Parent:** #EPIC-02  
**Epic:** #EPIC-02  

### Title
[FEAT-16] Pipeline Status Dashboard

### Description
Dashboard showing stage, progress, CTAs. F-16.

### Business Value
Creator always knows pipeline state and next action (SC-08).

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-02 (must be closed first)
- #FEAT-INFRA (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s2`, `feature:F-16`, `epic:EPIC-02`, `priority:p0`, `F-16`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 11: [FEAT-02] Capture Idea

**Type:** Feature  
**Milestone:** S3  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-02] Capture Idea

### Description
Title, paragraph, optional style note. F-02.

### Business Value
Captures creative intent as first versioned asset; root of lineage chain.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-01 (must be closed first)
- #FEAT-03 (must be closed first)
- #FEAT-16 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s3`, `feature:F-02`, `epic:EPIC-03`, `priority:p0`, `F-02`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 12: [FEAT-04] AI Story Generation

**Type:** Feature  
**Milestone:** S3  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-04] AI Story Generation

### Description
Story Architect agent generates treatment. F-04.

### Business Value
First AI value moment — treatment from idea in <5 min (SC-07).

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-02 (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s3`, `feature:F-04`, `epic:EPIC-03`, `priority:p0`, `F-04`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 13: [FEAT-05] Story Review & Approval

**Type:** Feature  
**Milestone:** S3  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-05] Story Review & Approval

### Description
Read, edit, approve/reject story. F-05.

### Business Value
Human creative control over AI story output; enforces approval gate.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-04 (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s3`, `feature:F-05`, `epic:EPIC-03`, `priority:p0`, `F-05`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 14: [FEAT-06] AI Script Generation

**Type:** Feature  
**Milestone:** S3  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-06] AI Script Generation

### Description
Screenwriter agent generates one-scene Fountain script. F-06.

### Business Value
Produces shootable screenplay for one scene; bridges narrative to visual production.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-05 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s3`, `feature:F-06`, `epic:EPIC-03`, `priority:p0`, `F-06`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 15: [FEAT-07] Script Review & Approval

**Type:** Feature  
**Milestone:** S3  
**Parent:** #EPIC-03  
**Epic:** #EPIC-03  

### Title
[FEAT-07] Script Review & Approval

### Description
Preview script, approve/reject. F-07.

### Business Value
Final text gate before GPU-intensive visual work begins.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-03 (must be closed first)
- #FEAT-06 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s3`, `feature:F-07`, `epic:EPIC-03`, `priority:p0`, `F-07`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 16: [FEAT-08] AI Storyboard Generation

**Type:** Feature  
**Milestone:** S4  
**Parent:** #EPIC-04  
**Epic:** #EPIC-04  

### Title
[FEAT-08] AI Storyboard Generation

### Description
Cinematography agent + ComfyUI frames. F-08.

### Business Value
Visualizes scene before video; highest ComfyUI image risk isolated here.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-04 (must be closed first)
- #FEAT-07 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s4`, `feature:F-08`, `epic:EPIC-04`, `priority:p0`, `F-08`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 17: [FEAT-09] Storyboard Gallery Review

**Type:** Feature  
**Milestone:** S4  
**Parent:** #EPIC-04  
**Epic:** #EPIC-04  

### Title
[FEAT-09] Storyboard Gallery Review

### Description
Grid gallery, approve/reject frames. F-09.

### Business Value
Creator controls which frames proceed; prevents bad visuals propagating to video.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-04 (must be closed first)
- #FEAT-08 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s4`, `feature:F-09`, `epic:EPIC-04`, `priority:p0`, `F-09`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 18: [FEAT-10] AI Short Video Generation

**Type:** Feature  
**Milestone:** S5  
**Parent:** #EPIC-05  
**Epic:** #EPIC-05  

### Title
[FEAT-10] AI Short Video Generation

### Description
ComfyUI image-to-video from frames. F-10.

### Business Value
MVP climax — motion video from local AI. Proves full media pipeline.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-05 (must be closed first)
- #FEAT-09 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s5`, `feature:F-10`, `epic:EPIC-05`, `priority:p0`, `F-10`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 19: [FEAT-11] Video Preview & Approval

**Type:** Feature  
**Milestone:** S5  
**Parent:** #EPIC-05  
**Epic:** #EPIC-05  

### Title
[FEAT-11] Video Preview & Approval

### Description
In-browser video preview and final approval. F-11.

### Business Value
Human sign-off completes production; triggers export and SC-01.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-05 (must be closed first)
- #FEAT-10 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s5`, `feature:F-11`, `epic:EPIC-05`, `priority:p0`, `F-11`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 20: [FEAT-14] Lineage Summary

**Type:** Feature  
**Milestone:** S5  
**Parent:** #EPIC-05  
**Epic:** #EPIC-05  

### Title
[FEAT-14] Lineage Summary

### Description
Idea to video chain visualization. F-14.

### Business Value
Shows derivation chain idea→video without Neo4j; builds trust in AI outputs.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-05 (must be closed first)
- #FEAT-11 (must be closed first)

### Priority
P1

### Labels
`aimpos-spark`, `feature`, `sprint:s5`, `feature:F-14`, `epic:EPIC-05`, `priority:p1`, `F-14`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 21: [FEAT-15] Export Final Bundle

**Type:** Feature  
**Milestone:** S5  
**Parent:** #EPIC-05  
**Epic:** #EPIC-05  

### Title
[FEAT-15] Export Final Bundle

### Description
ZIP download with manifest.json. F-15.

### Business Value
Archivable deliverable with integrity hashes (SC-11); demo step 10.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-05 (must be closed first)
- #FEAT-11 (must be closed first)

### Priority
P1

### Labels
`aimpos-spark`, `feature`, `sprint:s5`, `feature:F-15`, `epic:EPIC-05`, `priority:p1`, `F-15`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 22: [FEAT-12] Asset Version History

**Type:** Feature  
**Milestone:** S4  
**Parent:** #EPIC-06  
**Epic:** #EPIC-06  

### Title
[FEAT-12] Asset Version History

### Description
Browse versions per stage. F-12.

### Business Value
Transparency into AI drafts vs human edits; supports regenerate workflow.

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-06 (must be closed first)
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s4`, `feature:F-12`, `epic:EPIC-06`, `priority:p0`, `F-12`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 23: [FEAT-13] Audit Log Viewer

**Type:** Feature  
**Milestone:** S3  
**Parent:** #EPIC-06  
**Epic:** #EPIC-06  

### Title
[FEAT-13] Audit Log Viewer

### Description
Chronological pipeline event log. F-13.

### Business Value
Verifiable audit trail for model usage and approvals (SC-05).

### Acceptance Criteria
_See child user stories._

### Dependencies
- #EPIC-06 (must be closed first)
- #FEAT-03 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `feature`, `sprint:s3`, `feature:F-13`, `epic:EPIC-06`, `priority:p0`, `F-13`

### Estimated Complexity
Large (multi-story)

### Definition of Done
- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance

---

## Issue 24: [US-02] Deploy MVP stack on Olares

**Type:** User Story  
**Milestone:** S1  
**Story Points:** 5  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  
**Implementation Order:** 1  

### Title
[US-02] Deploy MVP stack on Olares

### Description
As a platform engineer, I want Docker Compose for all MVP services.

### Business Value
Team can develop and demo on Olares with one command.

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
`aimpos-spark`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `devops`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-02-01` — Write docker-compose.yml for all 9 services
- [ ] `T-02-02` — Configure PostgreSQL volume and init scripts
- [ ] `T-02-03` — Configure MinIO bucket aimpos-hot-assets on startup
- [ ] `T-02-04` — Pin Ollama model llama3.1:13b in compose init
- [ ] `T-02-05` — Document Olares deployment in README
- [ ] `T-02-06` — Verify zero egress during compose startup

---

## Issue 25: [US-04] Database schema foundation

**Type:** User Story  
**Milestone:** S1  
**Story Points:** 3  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  
**Implementation Order:** 2  

### Title
[US-04] Database schema foundation

### Description
As a backend developer, I want core tables migrated.

### Business Value
Single source of truth for pipeline, assets, audit — architectural requirement.

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
`aimpos-spark`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `backend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-04-01` — Define SQLAlchemy models for core tables
- [ ] `T-04-02` — Create initial Alembic migration
- [ ] `T-04-03` — Add repository layer interfaces

---

## Issue 26: [US-03] API health and logging

**Type:** User Story  
**Milestone:** S1  
**Story Points:** 2  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  
**Implementation Order:** 3  

### Title
[US-03] API health and logging

### Description
As a platform engineer, I want health checks and structured logs.

### Business Value
Fast diagnosis of integration failures; ops readiness.

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
`aimpos-spark`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `backend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-03-01` — Implement /health with dependency probes
- [ ] `T-03-02` — Add structured logging middleware
- [ ] `T-03-03` — Add request ID propagation

---

## Issue 27: [US-05] MinIO asset upload service

**Type:** User Story  
**Milestone:** S1  
**Story Points:** 3  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  
**Implementation Order:** 4  

### Title
[US-05] MinIO asset upload service

### Description
As a backend developer, I want reusable content-addressable asset storage.

### Business Value
Content-addressable assets enable versioning, export hashes, deduplication.

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
`aimpos-spark`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `backend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-05-01` — Implement MinIO client wrapper
- [ ] `T-05-02` — Implement content-hash key generator
- [ ] `T-05-03` — Implement AssetVersion create on upload
- [ ] `T-05-04` — Integration test upload round-trip

---

## Issue 28: [US-06] Ollama and ComfyUI smoke test

**Type:** User Story  
**Milestone:** S1  
**Story Points:** 3  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-01  
**Implementation Order:** 5  

### Title
[US-06] Ollama and ComfyUI smoke test

### Description
As an AI engineer, I want verified local model endpoints.

### Business Value
Validates GPU path before agent sprints; avoids late MVP kill.

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
`aimpos-spark`, `user-story`, `sprint:s1`, `feature:F-INFRA`, `epic:EPIC-01`, `priority:p0`, `ai`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-06-01` — Create Ollama connectivity test script
- [ ] `T-06-02` — Pin and test ComfyUI SDXL workflow JSON
- [ ] `T-06-03` — Document GPU sequencing rule in worker README

---

## Issue 29: [US-01] Create default project

**Type:** User Story  
**Milestone:** S1  
**Story Points:** 2  
**Parent:** #FEAT-01  
**Epic:** #EPIC-03  
**Implementation Order:** 6  

### Title
[US-01] Create default project

### Description
As a creator, I want a default project on startup so I can begin without setup.

### Business Value
Creator opens app and immediately has a project — zero onboarding.

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
`aimpos-spark`, `user-story`, `sprint:s1`, `feature:F-01`, `epic:EPIC-03`, `priority:p0`, `backend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-01-01` — Create projects table migration
- [ ] `T-01-02` — Implement seed script for default project
- [ ] `T-01-03` — Add GET /projects endpoint
- [ ] `T-01-04` — Unit test project repository

---

## Issue 30: [US-26] App navigation shell

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 2  
**Parent:** #FEAT-16  
**Epic:** #EPIC-06  
**Implementation Order:** 7  

### Title
[US-26] App navigation shell

### Description
As a creator, I want nav between Dashboard, Review, Assets, Audit, Export.

### Business Value
Unified UX across five screens; SC-08 comprehension.

### Acceptance Criteria
- [ ] Nav bar on all screens
- [ ] Empty states when pipeline not started
- [ ] CTA reflects current stage
- [ ] Usable at >=768px

### Dependencies
- #FEAT-16 (must be closed first)
- #US-02 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-16`, `epic:EPIC-06`, `priority:p0`, `frontend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-26-01` — Build app shell with React Router
- [ ] `T-26-02` — Implement nav bar and route guards
- [ ] `T-26-03` — Add empty states per screen

---

## Issue 31: [US-07] Start pipeline workflow

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 5  
**Parent:** #FEAT-03  
**Epic:** #EPIC-02  
**Implementation Order:** 8  

### Title
[US-07] Start pipeline workflow

### Description
As a creator, I want to start production after entering my idea.

### Business Value
Pipeline automation begins; core workflow value delivered.

### Acceptance Criteria
- [ ] POST /pipeline/start creates SparkPipelineWorkflow
- [ ] GET /pipeline/status shows STORY_GENERATING or STORY_REVIEW
- [ ] Duplicate start returns 409
- [ ] PipelineStarted audit event recorded

### Dependencies
- #FEAT-03 (must be closed first)
- #US-01 (must be closed first)
- #US-04 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `workflow`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-07-01` — Deploy Temporal server with PostgreSQL persistence
- [ ] `T-07-02` — Implement SparkPipelineWorkflow skeleton
- [ ] `T-07-03` — Implement POST /pipeline/start API
- [ ] `T-07-04` — Implement GET /pipeline/status API
- [ ] `T-07-05` — Register Temporal worker pod
- [ ] `T-07-06` — Write audit event on pipeline start

---

## Issue 32: [US-08] Approve or reject stage output

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 5  
**Parent:** #FEAT-03  
**Epic:** #EPIC-02  
**Implementation Order:** 9  

### Title
[US-08] Approve or reject stage output

### Description
As a creator, I want to approve or reject AI output at each stage.

### Business Value
Human-in-the-loop enforced — agents cannot bypass creator (SC-03).

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
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `workflow`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-08-01` — Implement approval API endpoints
- [ ] `T-08-02` — Wire Temporal approve/reject signals
- [ ] `T-08-03` — Create immutable approvals table writes
- [ ] `T-08-04` — Handle reject without workflow advance
- [ ] `T-08-05` — Integration test approve advances stage

---

## Issue 33: [US-09] Regenerate after rejection

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 3  
**Parent:** #FEAT-03  
**Epic:** #EPIC-02  
**Implementation Order:** 10  

### Title
[US-09] Regenerate after rejection

### Description
As a creator, I want to regenerate AI output after rejecting it.

### Business Value
Improves AI output quality without pipeline restart (SC-10).

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
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-02`, `priority:p0`, `workflow`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-09-01` — Implement regenerate endpoint
- [ ] `T-09-02` — Pass rejection note to activity input
- [ ] `T-09-03` — Enforce max 3 regenerations per stage
- [ ] `T-09-04` — Increment version on regenerate

---

## Issue 34: [US-24] Pipeline survives worker restart

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 3  
**Parent:** #FEAT-03  
**Epic:** #EPIC-06  
**Implementation Order:** 11  

### Title
[US-24] Pipeline survives worker restart

### Description
As a platform engineer, I want workflow resume after restart.

### Business Value
Long GPU jobs survive restarts — creator confidence (SC-06).

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
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-03`, `epic:EPIC-06`, `priority:p0`, `workflow`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-24-01` — Configure Temporal worker graceful shutdown
- [ ] `T-24-02` — Test worker restart during review wait
- [ ] `T-24-03` — Test worker restart during activity execution
- [ ] `T-24-04` — Document recovery behavior

---

## Issue 35: [US-25] API token authentication

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 2  
**Parent:** #FEAT-INFRA  
**Epic:** #EPIC-06  
**Implementation Order:** 12  

### Title
[US-25] API token authentication

### Description
As a platform engineer, I want Bearer token on mutating endpoints.

### Business Value
Basic LAN security for lab deployment.

### Acceptance Criteria
- [ ] No token on POST returns 401
- [ ] Valid Bearer succeeds
- [ ] Web client sends token from env

### Dependencies
- #FEAT-INFRA (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-INFRA`, `epic:EPIC-06`, `priority:p0`, `security`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-25-01` — Implement Bearer token middleware
- [ ] `T-25-02` — Configure token via environment variable
- [ ] `T-25-03` — Wire token into React API client

---

## Issue 36: [US-10] View pipeline status dashboard

**Type:** User Story  
**Milestone:** S2  
**Story Points:** 3  
**Parent:** #FEAT-16  
**Epic:** #EPIC-02  
**Implementation Order:** 13  

### Title
[US-10] View pipeline status dashboard

### Description
As a creator, I want a dashboard showing stage and progress.

### Business Value
Reduces creator confusion; shows progress and required actions.

### Acceptance Criteria
- [ ] Dashboard shows stage, status, 5-step progress
- [ ] REVIEW shows Go to Review CTA
- [ ] GENERATING polls every 5s
- [ ] FAILED shows error and Retry

### Dependencies
- #FEAT-16 (must be closed first)
- #US-07 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s2`, `feature:F-16`, `epic:EPIC-02`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-10-01` — Implement dashboard API aggregation endpoint
- [ ] `T-10-02` — Build Dashboard screen (React)
- [ ] `T-10-03` — Add 5-stage progress stepper component
- [ ] `T-10-04` — Implement status polling hook

---

## Issue 37: [US-11] Enter production idea

**Type:** User Story  
**Milestone:** S3  
**Story Points:** 2  
**Parent:** #FEAT-02  
**Epic:** #EPIC-03  
**Implementation Order:** 14  

### Title
[US-11] Enter production idea

### Description
As a creator, I want to enter title, paragraph, and style note.

### Business Value
Production starts from creator's own idea — MVP entry point.

### Acceptance Criteria
- [ ] Submit idea stores idea
- [ ] txt v1 in MinIO
- [ ] Style note in metadata
- [ ] Appears under stage IDEA
- [ ] Validation on required fields and 50-2000 char paragraph

### Dependencies
- #FEAT-02 (must be closed first)
- #US-01 (must be closed first)
- #US-05 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s3`, `feature:F-02`, `epic:EPIC-03`, `priority:p0`, `frontend`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-11-01` — Implement POST /ideas endpoint
- [ ] `T-11-02` — Build idea capture form on Dashboard
- [ ] `T-11-03` — Validate input length and required fields
- [ ] `T-11-04` — Store idea as asset_version stage=IDEA

---

## Issue 38: [US-12] Generate story from idea

**Type:** User Story  
**Milestone:** S3  
**Story Points:** 5  
**Parent:** #FEAT-04  
**Epic:** #EPIC-03  
**Implementation Order:** 15  

### Title
[US-12] Generate story from idea

### Description
As a creator, I want Story Architect to generate a treatment.

### Business Value
First AI-generated creative asset; proves local LLM story capability.

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
`aimpos-spark`, `user-story`, `sprint:s3`, `feature:F-04`, `epic:EPIC-03`, `priority:p0`, `ai`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-12-01` — Implement LangGraph Story Architect graph
- [ ] `T-12-02` — Implement run_story_agent Temporal activity
- [ ] `T-12-03` — Create story prompt template with idea injection
- [ ] `T-12-04` — Store story output as asset version
- [ ] `T-12-05` — Log agent invocation to audit_events
- [ ] `T-12-06` — Integration test story generation (mock Ollama)

---

## Issue 39: [US-13] Review and edit story

**Type:** User Story  
**Milestone:** S3  
**Story Points:** 3  
**Parent:** #FEAT-05  
**Epic:** #EPIC-03  
**Implementation Order:** 16  

### Title
[US-13] Review and edit story

### Description
As a creator, I want to read, edit, and approve the story.

### Business Value
Creator refines treatment before scripting — quality gate.

### Acceptance Criteria
- [ ] Review screen shows editable treatment
- [ ] Save creates human-edit version
- [ ] Approve advances pipeline
- [ ] Reject enables regenerate

### Dependencies
- #FEAT-05 (must be closed first)
- #US-08 (must be closed first)
- #US-12 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s3`, `feature:F-05`, `epic:EPIC-03`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-13-01` — Build Review screen — story mode
- [ ] `T-13-02` — Implement PUT /assets/{id} text update
- [ ] `T-13-03` — Wire Approve/Reject buttons to pipeline API
- [ ] `T-13-04` — Display rejection note input on reject

---

## Issue 40: [US-14] Generate one-scene script

**Type:** User Story  
**Milestone:** S3  
**Story Points:** 5  
**Parent:** #FEAT-06  
**Epic:** #EPIC-03  
**Implementation Order:** 17  

### Title
[US-14] Generate one-scene script

### Description
As a creator, I want Screenwriter to generate a Fountain script.

### Business Value
Automates screenplay draft; saves hours of manual writing.

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
`aimpos-spark`, `user-story`, `sprint:s3`, `feature:F-06`, `epic:EPIC-03`, `priority:p0`, `ai`

### Estimated Complexity
Medium (5 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-14-01` — Implement LangGraph Screenwriter graph
- [ ] `T-14-02` — Implement run_script_agent Temporal activity
- [ ] `T-14-03` — Add Fountain format validation
- [ ] `T-14-04` — Record lineage edge story to script
- [ ] `T-14-05` — Store script asset version

---

## Issue 41: [US-15] Review and approve script

**Type:** User Story  
**Milestone:** S3  
**Story Points:** 3  
**Parent:** #FEAT-07  
**Epic:** #EPIC-03  
**Implementation Order:** 18  

### Title
[US-15] Review and approve script

### Description
As a creator, I want to preview and approve the script.

### Business Value
Locks script before expensive GPU storyboard work.

### Acceptance Criteria
- [ ] Fountain rendered with formatting
- [ ] Approve advances to STORYBOARD_GENERATING
- [ ] Reject/regenerate works
- [ ] Approved version marked in DB

### Dependencies
- #FEAT-07 (must be closed first)
- #US-08 (must be closed first)
- #US-14 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s3`, `feature:F-07`, `epic:EPIC-03`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-15-01` — Build Review screen — script mode with Fountain preview
- [ ] `T-15-02` — Add basic Fountain-to-HTML formatter
- [ ] `T-15-03` — Wire approve/reject for script stage
- [ ] `T-15-04` — Mark approved script version in DB

---

## Issue 42: [US-23] View audit trail

**Type:** User Story  
**Milestone:** S3  
**Story Points:** 3  
**Parent:** #FEAT-13  
**Epic:** #EPIC-06  
**Implementation Order:** 19  

### Title
[US-23] View audit trail

### Description
As a creator, I want chronological pipeline event log.

### Business Value
Full transparency of what AI did and when (SC-05).

### Acceptance Criteria
- [ ] Events: PipelineStarted, AgentTaskCompleted, ApprovalGranted, Rejected, Completed
- [ ] Agent events show model_id
- [ ] Append-only
- [ ] Included in export

### Dependencies
- #FEAT-13 (must be closed first)
- #US-04 (must be closed first)
- #US-07 (must be closed first)
- #US-12 (must be closed first)
- #US-14 (must be closed first)
- #US-16 (must be closed first)
- #US-18 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s3`, `feature:F-13`, `epic:EPIC-06`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-23-01` — Implement GET /audit?pipeline_run_id= API
- [ ] `T-23-02` — Build Audit screen table
- [ ] `T-23-03` — Standardize audit event schema across worker
- [ ] `T-23-04` — Include audit summary in export manifest

---

## Issue 43: [US-16] Generate storyboard frames

**Type:** User Story  
**Milestone:** S4  
**Story Points:** 8  
**Parent:** #FEAT-08  
**Epic:** #EPIC-04  
**Implementation Order:** 20  

### Title
[US-16] Generate storyboard frames

### Description
As a creator, I want 4-6 storyboard images from my script.

### Business Value
Generates visual plan locally; core differentiator vs cloud tools.

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
`aimpos-spark`, `user-story`, `sprint:s4`, `feature:F-08`, `epic:EPIC-04`, `priority:p0`, `ai`

### Estimated Complexity
High (8 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-16-01` — Implement Cinematography agent (planning via Ollama)
- [ ] `T-16-02` — Implement ComfyUI tool — SDXL/Flux workflow
- [ ] `T-16-03` — Implement run_storyboard_agent Temporal activity
- [ ] `T-16-04` — GPU sequencing: unload Ollama before ComfyUI
- [ ] `T-16-05` — Store multiple frame assets per run
- [ ] `T-16-06` — Record lineage edges script to frames
- [ ] `T-16-07` — ComfyUI error handling and retry

---

## Issue 44: [US-17] Review storyboard gallery

**Type:** User Story  
**Milestone:** S4  
**Story Points:** 3  
**Parent:** #FEAT-09  
**Epic:** #EPIC-04  
**Implementation Order:** 21  

### Title
[US-17] Review storyboard gallery

### Description
As a creator, I want to view frames in a grid and approve or reject.

### Business Value
Creator curates visuals; maintains creative control.

### Acceptance Criteria
- [ ] Responsive grid of 4-6 images
- [ ] Lightbox preview
- [ ] Approve-all advances to video
- [ ] Reject triggers regenerate
- [ ] AI badge on frames

### Dependencies
- #FEAT-09 (must be closed first)
- #US-08 (must be closed first)
- #US-16 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s4`, `feature:F-09`, `epic:EPIC-04`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-17-01` — Build Review screen — storyboard gallery mode
- [ ] `T-17-02` — Implement image preview lightbox
- [ ] `T-17-03` — Wire approve-all / reject for storyboard stage
- [ ] `T-17-04` — Display AI badge and model on frames

---

## Issue 45: [US-22] Browse asset versions

**Type:** User Story  
**Milestone:** S4  
**Story Points:** 3  
**Parent:** #FEAT-12  
**Epic:** #EPIC-06  
**Implementation Order:** 22  

### Title
[US-22] Browse asset versions

### Description
As a creator, I want to see all versions per stage.

### Business Value
Compare AI drafts, edits, and approvals across stages.

### Acceptance Criteria
- [ ] Versions grouped by stage
- [ ] Newest first
- [ ] Preview or download per version
- [ ] Shows is_ai_generated, branch, content_hash

### Dependencies
- #FEAT-12 (must be closed first)
- #US-05 (must be closed first)
- #US-12 (must be closed first)
- #US-16 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s4`, `feature:F-12`, `epic:EPIC-06`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-22-01` — Implement GET /assets?project_id=&stage= API
- [ ] `T-22-02` — Build Assets screen with stage tabs
- [ ] `T-22-03` — Implement version list and preview components
- [ ] `T-22-04` — Add download link per version

---

## Issue 46: [US-18] Generate short video clip

**Type:** User Story  
**Milestone:** S5  
**Story Points:** 8  
**Parent:** #FEAT-10  
**Epic:** #EPIC-05  
**Implementation Order:** 23  

### Title
[US-18] Generate short video clip

### Description
As a creator, I want a short video from approved frames.

### Business Value
Delivers final media artifact — MVP primary outcome.

### Acceptance Criteria
- [ ] scene_video
- [ ] mp4 15-30s <=480p
- [ ] Lineage frames to video
- [ ] VIDEO_REVIEW on success
- [ ] Slideshow fallback on failure

### Dependencies
- #FEAT-10 (must be closed first)
- #US-05 (must be closed first)
- #US-06 (must be closed first)
- #US-07 (must be closed first)
- #US-17 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s5`, `feature:F-10`, `epic:EPIC-05`, `priority:p0`, `ai`

### Estimated Complexity
High (8 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-18-01` — Implement ComfyUI image-to-video workflow
- [ ] `T-18-02` — Implement run_video_agent Temporal activity
- [ ] `T-18-03` — Implement slideshow fallback generator (FFmpeg)
- [ ] `T-18-04` — Store video asset with duration/resolution metadata
- [ ] `T-18-05` — Record lineage frames to video
- [ ] `T-18-06` — End-to-end GPU test on Olares hardware

---

## Issue 47: [US-19] Preview and approve video

**Type:** User Story  
**Milestone:** S5  
**Story Points:** 3  
**Parent:** #FEAT-11  
**Epic:** #EPIC-05  
**Implementation Order:** 24  

### Title
[US-19] Preview and approve video

### Description
As a creator, I want to preview video and complete the pipeline.

### Business Value
Formal completion and audit closure of production run.

### Acceptance Criteria
- [ ] HTML5 player renders video
- [ ] Approve sets COMPLETED
- [ ] Reject enables regenerate
- [ ] PipelineCompleted audit event

### Dependencies
- #FEAT-11 (must be closed first)
- #US-08 (must be closed first)
- #US-18 (must be closed first)
- #US-26 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s5`, `feature:F-11`, `epic:EPIC-05`, `priority:p0`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-19-01` — Build Review screen — video player mode
- [ ] `T-19-02` — Wire approve/reject for video stage
- [ ] `T-19-03` — Set pipeline status COMPLETED on final approval
- [ ] `T-19-04` — Write PipelineCompleted audit event

---

## Issue 48: [US-20] View asset lineage chain

**Type:** User Story  
**Milestone:** S5  
**Story Points:** 3  
**Parent:** #FEAT-14  
**Epic:** #EPIC-05  
**Implementation Order:** 25  

### Title
[US-20] View asset lineage chain

### Description
As a creator, I want to see idea to video lineage.

### Business Value
Explains how each asset was derived; regulatory/trust readiness.

### Acceptance Criteria
- [ ] Ordered chain: idea to story to script to frames to video
- [ ] Click node shows metadata
- [ ] Data from lineage_edges PostgreSQL

### Dependencies
- #FEAT-14 (must be closed first)
- #US-14 (must be closed first)
- #US-16 (must be closed first)
- #US-18 (must be closed first)
- #US-19 (must be closed first)

### Priority
P1

### Labels
`aimpos-spark`, `user-story`, `sprint:s5`, `feature:F-14`, `epic:EPIC-05`, `priority:p1`, `frontend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-20-01` — Implement GET /lineage/{pipeline_run_id} API
- [ ] `T-20-02` — Build Lineage summary component on Export screen
- [ ] `T-20-03` — Render chain visualization (simple list/tree)

---

## Issue 49: [US-21] Download production bundle

**Type:** User Story  
**Milestone:** S5  
**Story Points:** 3  
**Parent:** #FEAT-15  
**Epic:** #EPIC-05  
**Implementation Order:** 26  

### Title
[US-21] Download production bundle

### Description
As a creator, I want ZIP of approved assets with manifest.

### Business Value
Portable production package for archive and sharing.

### Acceptance Criteria
- [ ] ZIP contains all approved assets and manifest
- [ ] json with hashes, approvals, model IDs
- [ ] BundleExported audit event

### Dependencies
- #FEAT-15 (must be closed first)
- #US-05 (must be closed first)
- #US-19 (must be closed first)

### Priority
P1

### Labels
`aimpos-spark`, `user-story`, `sprint:s5`, `feature:F-15`, `epic:EPIC-05`, `priority:p1`, `backend`

### Estimated Complexity
Low (3 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-21-01` — Implement finalize_export Temporal activity
- [ ] `T-21-02` — Implement GET /export/{pipeline_run_id} ZIP builder
- [ ] `T-21-03` — Generate manifest.json with hashes and metadata
- [ ] `T-21-04` — Build Export screen with download button

---

## Issue 50: [US-27] MVP demo acceptance validation

**Type:** User Story  
**Milestone:** S5  
**Story Points:** 2  
**Parent:** #FEAT-15  
**Epic:** #EPIC-05  
**Implementation Order:** 27  

### Title
[US-27] MVP demo acceptance validation

### Description
As a product owner, I want demo script executable end-to-end.

### Business Value
Objective MVP readiness proof for stakeholders.

### Acceptance Criteria
- [ ] All 10 demo steps pass
- [ ] SC-01 to SC-08 verified
- [ ] Limitations documented
- [ ] Stakeholder sign-off

### Dependencies
- #FEAT-15 (must be closed first)
- #EPIC-05 (must be closed first)
- #US-21 (must be closed first)

### Priority
P0

### Labels
`aimpos-spark`, `user-story`, `sprint:s5`, `feature:F-15`, `epic:EPIC-05`, `priority:p0`, `qa`

### Estimated Complexity
Low (2 SP)

### Definition of Done
- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed

### Implementation Tasks
- [ ] `T-27-01` — Execute demo acceptance script
- [ ] `T-27-02` — Document success metrics results
- [ ] `T-27-03` — Write MVP release notes
- [ ] `T-27-04` — Stakeholder demo and sign-off

---
