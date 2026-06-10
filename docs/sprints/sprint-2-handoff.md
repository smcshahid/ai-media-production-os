# Sprint 2 — Workflow Foundation: Agent Handoff

**Governance:** SCR-2026-001 / **D-31**. Prerequisites: **S1-SW** complete; **M1-DV** not required to start (required before Sprint 3).

**Audience:** the engineering agent picking up Sprint 2.

Read [`sprint-1-handoff.md`](./sprint-1-handoff.md), **D-31** in [`DECISIONS.md`](../../DECISIONS.md), and [`docs/governance/development-workflow.md`](../governance/development-workflow.md) hard gates.

---

## 0. TL;DR

> **Sprint 2 = Temporal workflow skeleton:** start pipeline, approve/reject, audit, live dashboard — **stub activities only**. M2 exit: stub pipeline → `COMPLETED` via 4 approvals. **No real AI.**

---

## 1. Sprint 2 boundary (mandatory — SCR §3.2 / D-31)

### Prohibited

| Prohibited | Detail |
|------------|--------|
| **LangGraph implementation** | No graphs under `worker/app/agents/` |
| **Ollama inference calls** | No HTTP/SDK calls to Ollama from worker or API |
| **ComfyUI inference calls** | No workflow execution against ComfyUI |
| **Regenerate agent execution** | No US-09-style agent re-runs (Sprint 3) |
| **Production AI activities** | No `run_story_agent`, `run_script_agent`, `run_storyboard_agent`, or equivalent real inference |

### Permitted

| Permitted | Detail |
|-----------|--------|
| **Workflow orchestration** | `SparkPipelineWorkflow`, signals, `wait_condition` |
| **Temporal integration** | Server, worker registration, API start/signal client |
| **Approval/rejection flows** | `POST /pipeline/approve`, immutable `approvals` |
| **Audit tracking** | `audit_events` for start, approvals, transitions |
| **Status reporting** | `GET /pipeline/status`, dashboard polling (US-10) |
| **Stub activities** | Placeholder activities: set stage status, optional fixed-byte `store_asset`, stub DTOs — **no external AI** |

PRs introducing prohibited items are **out of Sprint 2 scope**.

---

## 2. Scope (authoritative — Sprint Reclassification class C)

| Issue | Deliverable |
|-------|-------------|
| EPIC-02 | Pipeline orchestration epic |
| FEAT-03 | Start production pipeline |
| FEAT-16 | Pipeline status dashboard |
| US-07 | `SparkPipelineWorkflow`, `POST /pipeline/start`, worker registration |
| US-08 | Approve/reject signals |
| US-10 | Live dashboard + polling |

**Explicit exclusions (do not execute in Sprint 2):** US-09 (regenerate), US-24 (worker durability — Sprint 5 per reclassification).

---

## 3. Exit gate (M2)

- US-07, US-08, US-10 closed
- Stub pipeline reaches **`COMPLETED`** via 4 human approvals
- All stage transitions in `audit_events`

---

## 4. Sprint 3 entry

Requires **M2** (this sprint) **and** **M1-DV** (US-06 live on Olares, or documented failure protocol on US-06).

---

## 5. References

- `docs/governance/definition-of-done.md` — M2 row
- `docs/governance/development-workflow.md` — hard gates
- `Sprint 0 — Platform Skeleton.md` §12 — historical §7 supersession
- `MVP Backlog.md` EPIC-02 — workflow skeleton goal
