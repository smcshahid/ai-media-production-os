# Spark Full — Governance Brief

**Document type:** Program governance brief (new planning cycle)  
**Status:** **ACCEPT** — governance review 2026-06-11. Spark Full planning cycle authorized.  
**Date:** 2026-06-11  
**Codename:** `AIMPOS-Spark-Full`  
**Prerequisite:** Visual MVP **COMPLETE** — tag `v0.4.0-usv01` · M5 signed  
**Authority chain:** [MVP Definition.md](../../MVP%20Definition.md) · [MVP Scope Freeze.md](../../MVP%20Scope%20Freeze.md) (Deferred items) · [GitHub Issues - Full MVP (Superseded).md](../../GitHub%20Issues%20-%20Full%20MVP%20(Superseded).md)

**Visual MVP closure records are frozen.** This brief opens a **new governance cycle**. It does not modify US-V01 evidence, acceptance packages, or M5 attestation.

---

## Table of contents

1. [Product Vision](#1-product-vision)
2. [Scope Boundaries](#2-scope-boundaries)
3. [Success Criteria](#3-success-criteria)
4. [MVP Lessons Learned](#4-mvp-lessons-learned)
5. [Proposed Story Sequence](#5-proposed-story-sequence)
6. [Hardware Assumptions](#6-hardware-assumptions)
7. [AI Model Strategy](#7-ai-model-strategy)
8. [Deployment Strategy](#8-deployment-strategy)
9. [Risks](#9-risks)
10. [Recommended US-18 Scope](#10-recommended-us-18-scope)

---

## 1. Product Vision

### 1.1 North star

AIMPOS-Spark Full completes the original MVP Definition promise:

> A creator can take a **one-paragraph idea**, produce an **approved story, script, storyboard, and short video** for **one scene**, with **local AI assistance**, **human approval at every stage**, **versioned assets**, and a **traceable audit trail** — without cloud GPU or multi-tenant complexity.

Visual MVP proved the **first four stages** on Olares. Spark Full adds the **fifth stage (Short Video)**, moves pipeline completion to **video approval**, and delivers **portable export** and **lineage visibility** — still on a single project, single scene, single creator, 100% local inference.

### 1.2 Extended pipeline

```mermaid
flowchart LR
    S0["S0: Idea"] --> S1["S1: Story<br/>Gate 1"]
    S1 --> S2["S2: Script<br/>Gate 2"]
    S2 --> S3["S3: Storyboard<br/>Gate 3"]
    S3 --> S4["S4: Short Video<br/>Gate 4"]
    S4 --> DONE["COMPLETED"]

    style DONE fill:#2d5016,color:#fff
```

| Dimension | Visual MVP (shipped) | Spark Full (target) |
|---|---|---|
| Terminal gate | STORYBOARD approve | **VIDEO approve** |
| Human gates | 3 | **4** |
| Motion output | None | **15–30 s MP4 ≤480p** |
| Export | None | **ZIP + manifest** |
| Lineage UI | SQL only | **Simple chain view** |
| Inference | Local only | Local only (unchanged) |

### 1.3 User outcome

After Spark Full, a non-engineer creator can run one session (~2–4 hours including GPU time): enter idea → review/edit story → review script → review storyboard gallery → **preview short video → approve** → **download production bundle** → **inspect idea-to-video lineage**.

---

## 2. Scope Boundaries

### 2.1 In scope (Spark Full)

| ID | Feature / story | Priority | Notes |
|---|---|---|---|
| **F-10** | AI short video generation | **P0** | US-18 |
| **F-11** | Video preview & approval | **P0** | US-19; **COMPLETED** moves here |
| **F-14** | Lineage summary UI | **P1** | US-20; simple list/tree |
| **F-15** | Export final bundle | **P1** | US-21; ZIP + JSON manifest |
| **EPIC-05** | Video & completion | **P0** | Closes when US-19 accepted |
| **US-V02** *(proposed)* | Spark Full E2E acceptance | **P0** | Verification gate (mirror US-V01 pattern) |

**Pipeline contract change (requires SCR):**

- Add `VIDEO` to `PipelineStage` enum and `SparkPipelineWorkflow`
- **STORYBOARD approve advances to VIDEO stage** — does **not** set `COMPLETED`
- **VIDEO approve** sets `COMPLETED` + `PipelineCompleted` audit event

### 2.2 Explicitly deferred (post–Spark Full)

| Item | Classification | Rationale |
|---|---|---|
| Multi-project / create-delete UI | **Future** | Scope Freeze 1.1 |
| Multi-scene scripts / breakdown | **Deferred** | BC 3.1 |
| Keycloak / RBAC (US-25 full) | **Deferred** | Lab token sufficient |
| WebSocket live updates | **Deferred** | Poll adequate |
| Asset history UI polish (US-22/23) | **Deferred** | P1; API/SQL exists partially |
| Neo4j / graph DB lineage | **Future** | PostgreSQL edges sufficient |
| Cloud inference / burst GPU | **Out of scope** | Sovereignty principle |
| NLE integration, distribution | **Future** | Program charter |

### 2.3 Frozen — do not regress

Visual MVP behavior through STORYBOARD remains **immutable** unless a blocking defect is filed against the underlying story:

- D-37..D-47 decision records (story/script/storyboard contracts)
- 4-frame storyboard batches (D-45)
- Batch-level approve/reject/regen (D-46, D-47)
- Append-only versioning (D-38)
- GPU sequencing rule (D-08)
- Local model pin (D-02 / D-36: `qwen3:14b`)

### 2.4 Governance boundary

| Authorized after brief ACCEPT | Forbidden without SCR |
|---|---|
| US-18..US-21 implementation | Changing Visual MVP terminal semantics retroactively |
| New `VIDEO` stage + 5th gate | Multi-scene or multi-project |
| ComfyUI video + FFmpeg fallback workflows | Cloud API calls |
| Review screen video player mode | Gallery framework abstractions |
| `GET /lineage` API + UI | Neo4j migration |
| Export ZIP endpoint | Modifying US-V01 closure records |

---

## 3. Success Criteria

Spark Full passes when **all** criteria below pass on Olares with a fresh project (proposed sign-off: **US-V02**).

### 3.1 Primary (from MVP Definition §9 — previously Deferred)

| ID | Criterion | Target | Evidence |
|---|---|---|---|
| **SC-01** | Complete pipeline E2E | Idea → **approved video** | Terminal `COMPLETED` after VIDEO approve |
| **SC-02** | Local inference | 100% — zero cloud API | Audit `model_id` / no egress |
| **SC-11** | Export integrity | ZIP contains approved assets + manifest hashes | US-21 acceptance |
| **SC-F01** | Fourth human gate | VIDEO approve/reject/regen recorded | `approvals` row |
| **SC-F02** | Video artifact | MP4 15–30 s, ≤480p, stored in MinIO | Asset row + content-read |
| **SC-F03** | Lineage chain | idea → story → script → frames → **video** | US-20 UI + SQL |
| **SC-F04** | Visual MVP regression | US-V01 path still passes through STORYBOARD | Re-run subset or SQL attestation |
| **SC-F05** | Worker durability | COMPLETED stable after worker restart | SC-V06 pattern on video terminal |

### 3.2 Inherited from Visual MVP (must not regress)

SC-V02 (local inference), SC-V04 (versioning), SC-V05 (audit completeness), SC-V06 (durability), SC-V07 (< 5 min to first story) — re-attested in US-V02.

### 3.3 Explicit non-goals

| Criterion | Status |
|---|---|
| Hollywood video quality | **Not required** — workflow proof |
| Real-time WebSocket status | **Deferred** |
| Sub-5-minute video generation | **Not required** — 10–25 min acceptable per MVP Definition journey |

---

## 4. MVP Lessons Learned

Lessons from Visual MVP delivery and US-V01 Olares attestation (`efdc8200-…`, tag `v0.4.0-usv01`):

### 4.1 What worked

| Lesson | Evidence | Spark Full application |
|---|---|---|
| **Governance briefs before code** | US-09..US-17, US-V01 pattern | Brief per story; D-records before implementation |
| **Decision records (D-37..D-47)** | Stable contracts across stories | Extend with D-48+ for VIDEO stage before US-18 |
| **Olares verify scripts + evidence packs** | `deploy/k8s/usv01-verify/`, acceptance package | `deploy/k8s/us18-verify/` … `usv02-verify/` |
| **Batch-level storyboard semantics** | D-46/D-47; US-V01 A-01 | Video is **single artifact** — simpler than frames |
| **Append-only regen** | SCRIPT + STORYBOARD regen paths | Mirror for VIDEO reject/regen |
| **GPU sequencer** | D-08; storyboard batches on Olares | **Mandatory** before video ComfyUI |
| **Fresh project E2E** | US-V01 PF-05 | Required for US-V02 |
| **Inline SQL attestation** | V-01..V-47 in verify log | Extend for VIDEO rows + frame→video lineage |

### 4.2 What to improve

| Lesson | Observation | Mitigation |
|---|---|---|
| **ComfyUI launcher reliability** | US-V01 PF-03 probe failed; frames still generated | Harden launcher + pre-flight in verify scripts; document manual fallback |
| **Async approve → COMPLETED delay** | VERIFY-V01-001 (~5 s) | Poll loop in verify scripts; do not assume synchronous terminal |
| **PowerShell / SSH friction** | Windows dev → Olares collect issues | Bash scripts on Olares; scp logs post-run |
| **No POST /projects API** | verify uses psql bootstrap | Accept for verify infra OR add minimal API in separate story |
| **Long ComfyUI wall-clock** | 2× storyboard batches in US-V01 | Budget 30+ min for video stage in acceptance run |
| **Annotated tag vs HEAD sync** | Multiple closure doc commits post-tag | Tag release artifact commit; sync docs after push (US-17/US-V01 pattern) |

### 4.3 Architectural debt (acceptable)

| Item | Status |
|---|---|
| Bearer token auth (not Keycloak) | Accept for Spark Full lab |
| Poll-based UI (no WebSocket) | Accept |
| Single pre-seeded project | Accept |
| `create_project.sh` psql bootstrap in verify | Accept for attestation only |

---

## 5. Proposed Story Sequence

Recommended implementation order after governance **ACCEPT**. Dependencies reflect Full MVP backlog; Visual MVP prerequisites are **closed**.

### 5.1 Phase A — Video pipeline (P0)

| Order | Story | SP | Depends on | Delivers |
|---|---|---|---|---|
| **A-1** | **US-18** Generate short video clip | 8 | US-17 ✅ | `run_video_agent`, MP4 asset, frame→video lineage |
| **A-2** | **US-19** Preview and approve video | 3 | US-18, US-08 ✅, US-26 ✅ | Video player review mode; **COMPLETED** at VIDEO approve |
| **A-3** | **US-V02** *(propose)* Spark Full E2E acceptance | 2 | US-19 | Olares attestation; M6 sign-off |

**Workflow change gate:** US-18 brief must include SCR for `PipelineStage.VIDEO` and moving `COMPLETED` from post-STORYBOARD to post-VIDEO.

### 5.2 Phase B — Trust & portability (P1)

| Order | Story | SP | Depends on | Delivers |
|---|---|---|---|---|
| **B-1** | **US-20** View asset lineage chain | 3 | US-18, US-19 | `GET /lineage/{run_id}` + UI |
| **B-2** | **US-21** Download production bundle | 3 | US-19 | ZIP export + manifest + audit |

Phase B may run **in parallel** with US-V02 prep once US-19 reaches code-complete; US-V02 should attestation-include lineage + export if Phase B is in scope for M6.

### 5.3 Phase C — Optional polish (defer if behind)

| Story | SP | Notes |
|---|---|---|
| US-22 Asset version browser | — | Partially in web; defer UI polish |
| US-23 Audit trail enhancements | — | Table exists; defer |
| US-24 Extended durability tests | — | SC-V06 covered at COMPLETED; extend for mid-VIDEO if needed |

### 5.4 Milestone map

| Milestone | Closure condition |
|---|---|
| **M6a — Video stage** | US-18 + US-19 Olares PASS |
| **M6 — Spark Full signed** | US-V02 ACCEPT (incl. export + lineage if Phase B shipped) |

---

## 6. Hardware Assumptions

### 6.1 Primary target — Olares lab node

| Assumption | Value | Source |
|---|---|---|
| Host | `olares@10.0.0.34` | M1-DV, US-V01 |
| Orchestration | k3s, namespace `aimpos-mwayolares` | Deploy docs |
| GPU | **Single GPU** — Ollama and ComfyUI **never concurrent** | **D-08** |
| Shared AI services | Cluster Ollama + ComfyUI (not duplicated in AIMPOS pods) | M1-DV README |
| VRAM band | ~8–16 GB effective for quantized models | MVP Definition §6.6 |
| Storage | MinIO hot tier; content-addressable keys | Visual MVP |
| Network | LAN / zero egress for inference | M1-DV T-02-06 |

### 6.2 Video-specific hardware expectations

| Workload | VRAM estimate | Duration estimate |
|---|---|---|
| Story + Script (Ollama `qwen3:14b`) | ~8–10 GB | < 2 min combined |
| Storyboard 4× SDXL frames | ~8 GB | 5–15 min per batch |
| Short video (i2v or encode) | **~12–16 GB** | **10–25 min** |
| FFmpeg slideshow fallback | **CPU only** | **< 2 min** |

**Assumption:** Olares can run ComfyUI image workloads today (proven US-16/17/V01). Video i2v must be **validated in week 1** of US-18; if VRAM insufficient, **slideshow fallback is the shipping path** for Spark Full v1.

### 6.3 Dev environment

| Environment | Role |
|---|---|
| Windows dev + Docker Compose | Unit tests, API/worker CI |
| Olares k8s | Authoritative GPU acceptance |
| No cloud GPU burst | Out of scope |

---

## 7. AI Model Strategy

### 7.1 Locked from Visual MVP

| Task | Model | Runtime | Decision |
|---|---|---|---|
| Story Architect | **`qwen3:14b`** | Ollama | D-02 / D-36 |
| Screenwriter | **`qwen3:14b`** | Ollama | D-02 / D-36 |
| Cinematography planner | **`qwen3:14b`** | Ollama | US-16 |
| Fallback chain | `llama3.1:8b` → `mistral:7b` | Ollama | D-02 |

### 7.2 New for Spark Full (proposed — confirm in US-18 brief)

| Task | Primary | Fallback | Rationale |
|---|---|---|---|
| Storyboard frames | SDXL (`sdxl_storyboard.json`) | — | D-03; proven on Olares |
| **Short video — primary** | **FFmpeg slideshow** from approved frames | — | **Low risk**; satisfies AC; CPU-only |
| **Short video — stretch** | ComfyUI **AnimateDiff** or **SVD** graph | Slideshow on any failure | MVP Definition §6.6; pin workflow JSON like D-03 |

### 7.3 GPU sequencing (mandatory)

```
Ollama (plan/script) → unload → ComfyUI frames → idle → ComfyUI video OR FFmpeg → idle
```

Enforce via existing `gpu/sequencer.py`. US-18 activity **must** call sequencer before any ComfyUI video job.

### 7.4 Prompt / input contract (proposed D-48 preview)

VIDEO regeneration inputs (mirror D-42/D-47):

1. **Approved storyboard batch** — latest `MAX(version)` STORYBOARD frames per D-46  
2. **Latest VIDEO rejection rationale** — no reuse of superseded MP4 bytes in prompt  
3. **Approved script** — optional context for slideshow captions/timing only  

### 7.5 Quality bar

Spark Full proves **workflow and provenance**, not broadcast quality. Cap: **480p, 15–30 s, H.264 MP4**. Creator expectation set in UI copy.

---

## 8. Deployment Strategy

### 8.1 Baseline

| Field | Value |
|---|---|
| Starting tag | **`v0.4.0-usv01`** |
| Images | Continue `aimpos-api:*` / `aimpos-worker:*` per-story tags |
| Schema | Alembic migrations only when US-18 brief authorizes (e.g. `VIDEO` stage enum, asset metadata) |
| Web | Static build deployed with API |

### 8.2 Per-story delivery pattern (proven)

1. Governance brief ACCEPT  
2. Implementation plan + decision records  
3. Local unit tests (API / worker / web)  
4. Build container images  
5. `deploy/k8s/usNN-verify/` Olares scripts  
6. Evidence → `evidence/us-NN-verification/`  
7. Implementation report + closure tag  

### 8.3 US-18 deploy specifics

| Step | Action |
|---|---|
| Worker | New `run_video_agent` activity; extend `spark_pipeline.py` |
| ComfyUI | Pin `configs/comfyui/workflows/` video graph **or** ship FFmpeg-only v1 |
| MinIO | `video/mp4` content type; metadata: `duration_sec`, `width`, `height`, `codec` |
| Verify | `deploy/k8s/us18-verify/verify_us18.sh` — pipeline through VIDEO gate |
| ComfyUI prep | Reuse `prep_comfyui.sh` pattern from US-V01 |

### 8.4 Rollback

Each story tag is independently revertable. If US-18 fails Olares, **do not** merge workflow COMPLETED move until video stage passes — keep STORYBOARD terminal on a maintenance branch only if hotfix required (prefer forward fix).

---

## 9. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R-01** | ComfyUI i2v exceeds VRAM or quality unusable | **High** | **High** | **Ship FFmpeg slideshow as primary**; i2v as stretch goal |
| **R-02** | Video stage extends E2E run > 60 min | **Medium** | **Medium** | Slideshow default; US-V02 time-box; async polling |
| **R-03** | Moving COMPLETED breaks US-V01 regression | **Medium** | **High** | SCR + unit tests; US-V02 re-attests STORYBOARD path; feature flag optional |
| **R-04** | Temporal workflow non-determinism on new stage | **Medium** | **High** | Follow US-09 fix pattern; fresh runs for verify |
| **R-05** | ComfyUI launcher unreachable (PF-03 class) | **Medium** | **Medium** | FFmpeg path independent of ComfyUI; harden prep script |
| **R-06** | Scope creep into multi-scene / export formats | **High** | **Medium** | This brief + SCR gate; ZIP manifest only |
| **R-07** | Single-GPU sequencing bugs under video load | **Medium** | **High** | D-08 enforcement; GPU smoke in US-18 verify |
| **R-08** | Large MP4 MinIO / browser preview issues | **Low** | **Medium** | Cap 480p/30s; HTML5 `<video>` with content-read URL |

### 9.1 Kill / pivot criteria

| Signal | Action |
|---|---|
| No MP4 stored after 2 Olares attempts | Ship **slideshow-only** US-18; defer i2v to Spark Full v1.1 |
| US-19 cannot reach COMPLETED reliably | Block M6; file workflow defect |
| Export ZIP fails hash audit | Block US-21 closure; manual manifest acceptable for demo only |

---

## 10. Recommended US-18 Scope

US-18 is **8 SP / P0** in the Full MVP backlog. Recommend **scoped delivery** in two internal phases within one governance story, with explicit **phase-1 acceptance** for Spark Full v1.

### 10.1 Recommended phase 1 — Slideshow video (authorize first)

**Goal:** Wire the VIDEO stage end-to-end with deterministic, CPU-based output.

| Task | Deliverable |
|---|---|
| T-18-S1 | SCR + `PipelineStage.VIDEO`; workflow continues after STORYBOARD approve |
| T-18-S2 | `run_video_agent` activity — FFmpeg slideshow from **approved storyboard batch** (4 PNGs) |
| T-18-S3 | MP4 output: **15–30 s**, **≤480p**, H.264; store as `stage=VIDEO`, `branch=ai-draft` |
| T-18-S4 | Lineage: each frame → video (or batch parent → video) in `lineage_edges` |
| T-18-S5 | Metadata: `duration_sec`, `width`, `height`, `source=slideshow` |
| T-18-S6 | Audit: `AGENT_TASK_COMPLETED` or `VIDEO_GENERATED` event with method |
| T-18-S7 | Olares verify: STORYBOARD approve → VIDEO gate → MP4 content-read HTTP 200 |

**Acceptance (phase 1):**

- [ ] `scene_video.mp4` (or content-addressed equivalent) in MinIO  
- [ ] Pipeline status `AWAITING_APPROVAL` at `VIDEO` — **not** `COMPLETED` at STORYBOARD  
- [ ] Lineage frames → video in PostgreSQL  
- [ ] Regenerate after reject produces new MP4 version (append-only)  

### 10.2 Recommended phase 2 — ComfyUI i2v (stretch, same story or US-18b)

**Goal:** Upgrade generation method when Olares proves VRAM headroom.

| Task | Deliverable |
|---|---|
| T-18-C1 | Pin ComfyUI workflow JSON (AnimateDiff or SVD) under `configs/comfyui/workflows/` |
| T-18-C2 | GPU sequencer integration; unload before video job |
| T-18-C3 | On ComfyUI failure → **automatic slideshow fallback** (Issue 46 AC) |
| T-18-C4 | Metadata `source=comfyui_i2v`; model/workflow in audit |

**Do not block US-19 or M6 on phase 2.** Phase 2 failure reverts to slideshow, not pipeline failure.

### 10.3 Explicitly out of US-18 scope

| Item | Route |
|---|---|
| Video review UI / COMPLETED | **US-19** |
| Export ZIP | **US-21** |
| Lineage graph UI | **US-20** |
| Audio track / music | **Future** |
| 720p+ / >30 s | **SCR required** |
| Per-frame video approve | **Rejected** — single video artifact |

### 10.4 Proposed decision records (draft for US-18 brief)

| ID | Topic |
|---|---|
| **D-48** | VIDEO asset contract (`stage=VIDEO`, MP4 semantics, metadata) |
| **D-49** | Approved storyboard resolution as video input (extends D-46) |
| **D-50** | VIDEO regen input contract (extends D-47 pattern) |
| **D-51** | COMPLETED terminal moves to VIDEO approve (US-19 boundary) |

### 10.5 Effort estimate

| Phase | Estimate | Confidence |
|---|---|---|
| Phase 1 slideshow + workflow | 5–6 SP | **High** |
| Phase 2 ComfyUI i2v | +3–5 SP | **Medium** (hardware-dependent) |
| Olares verify package | 1 SP | **High** (pattern established) |

---

## 11. Governance next steps

| Step | Owner | Action |
|---|---|---|
| 1 | PO + Architect | Review this brief → **ACCEPT** / **ACCEPT WITH AMENDMENT** / **REJECT** |
| 2 | Architect | Open SCR for VIDEO stage + COMPLETED move |
| 3 | Engineering | Draft `docs/sprints/sprint-4a-us18-brief.md` using §10 |
| 4 | PO | Confirm M6 = US-V02 scope (video only vs video + export + lineage) |
| 5 | — | **No implementation** until US-18 brief ACCEPT |

---

## Document control

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-06-11 | Initial Spark Full governance brief post M5 |

**Related (frozen):**

- `docs/sprints/visual-mvp-completion-summary.md`  
- `evidence/us-v01-verification/olares-2026-06-11/US-V01-ACCEPTANCE-PACKAGE.md`  
- `docs/sprints/sprint-3i-usv01-closure-report.md`

*End of document.*
