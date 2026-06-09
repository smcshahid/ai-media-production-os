# AIMPOS-Spark Visual — Definition of Done

**Document Type:** Engineering Governance  
**Version:** 1.0  
**Status:** FROZEN — Effective June 9, 2026  
**Date:** June 9, 2026  
**Product:** AIMPOS-Spark Visual

---

## Purpose

Project-level Definition of Done (DoD) for closing GitHub issues. Issue **acceptance criteria** in [GitHub Issues - Visual MVP.md](../../GitHub%20Issues%20-%20Visual%20MVP.md) define *what* to build; this document defines *when an issue is truly complete*.

**Related documents:**

- [development-workflow.md](./development-workflow.md)
- [branching-strategy.md](./branching-strategy.md)
- [coding-standards.md](./coding-standards.md)
- [MVP Scope Freeze.md](../../MVP%20Scope%20Freeze.md)

---

## Universal DoD (Every Issue)

An issue is **done** only when all of the following are true:

- [ ] All implementation tasks for the issue are complete
- [ ] Issue **acceptance criteria** verified locally on Docker Compose or Olares
- [ ] PR merged to `main` per [branching-strategy.md](./branching-strategy.md)
- [ ] Work is within [MVP Scope Freeze.md](../../MVP%20Scope%20Freeze.md) — no out-of-freeze features
- [ ] [coding-standards.md](./coding-standards.md) architectural rules respected (when code is involved)
- [ ] No secrets committed; new env vars documented in `.env.example`
- [ ] Downstream smoke still passes (compose up; prior gates unaffected)

Copy this checklist into every PR description and mark items complete.

---

## DoD by Change Type

Apply the sections below **in addition to** Universal DoD when the issue touches that area.

### Infrastructure (`deploy/`, Docker Compose, Makefile)

- [ ] `docker compose up` starts all services for the current sprint scope
- [ ] Health checks pass for affected services
- [ ] `.env.example` updated if new environment variables were added
- [ ] README or runbook updated when issue requires it (e.g. US-02, US-06)

### Database (Alembic migrations, SQLAlchemy models)

- [ ] Migration applies cleanly on empty database
- [ ] Migration downgrade succeeds (rollback works)
- [ ] Models match issue AC (table names, required columns)
- [ ] Repository interfaces colocated per [Repository Structure.md](../../Repository%20Structure.md)

### API (FastAPI routes, domain services)

- [ ] New/changed route appears in OpenAPI schema
- [ ] `api/domain/` modules contain **no** FastAPI or SQLAlchemy imports
- [ ] Colocated tests added or updated in `api/tests/`
- [ ] API does **not** call Ollama, ComfyUI, or Temporal activities directly

### Worker (Temporal workflows, activities, agents)

- [ ] Worker exposes **no** HTTP server
- [ ] Workflow/activity registered and picked up by worker process
- [ ] Activities are idempotent where issue AC requires it
- [ ] Agent code lives under `worker/agents/` only
- [ ] Colocated tests added or updated in `worker/tests/`

### AI / GPU (Ollama, ComfyUI, LangGraph)

- [ ] Model or workflow JSON pinned under `configs/`
- [ ] Relevant smoke script in `scripts/smoke/` passes on target hardware
- [ ] GPU sequencing respected — no concurrent Ollama + ComfyUI when issue involves both
- [ ] Audit fields logged: `model_id`, inputs reference, timestamp (per SC-05)

### Web (React SPA)

- [ ] UI matches issue AC (screen, states, actions)
- [ ] Frontend calls **API only** — never Temporal, Ollama, or ComfyUI
- [ ] Colocated tests added or updated in `web/src/tests/` where applicable
- [ ] Desktop layout ≥ 768px (mobile out of scope)

---

## Epic and Feature DoD

Epics and features close when:

- [ ] All child P0 user stories are closed
- [ ] Epic acceptance criteria verified on Olares (or Docker Compose during early sprints)
- [ ] No open P0 defects against the epic scope

---

## Milestone / Sprint DoD

Per [Sprint Reclassification.md](../../Sprint%20Reclassification.md) and [Architecture Freeze Review.md](../../Architecture%20Freeze%20Review.md).

| Milestone | Sprint | Gate |
|-----------|--------|------|
| **M0 — Platform Skeleton** | Sprint 0 | 24 class-A issues closed; browser walkthrough: Login → Project → Upload → idle Dashboard |
| **M1 — Infrastructure validated** | Sprint 1 | US-02, US-06, EPIC-01, FEAT-INFRA closed; GPU smoke pass on Olares |
| **M2 — Workflow skeleton** | Sprint 2 | US-07, US-08, US-10 closed; stub pipeline → `COMPLETED` |
| **M3 — Story pipeline** | Sprint 3 | US-11 through US-13 closed; Idea → approved story E2E |
| **M4 — Script pipeline** | Sprint 4 | US-14, US-15 closed; approved script E2E |
| **M5 — Visual MVP signed** | Sprint 5 | US-16, US-17, US-V01 closed; Idea → approved storyboard frames |

---

## Visual MVP Sign-Off (US-V01)

The increment is complete when:

- [ ] All 43 Visual MVP issues closed (or pre-approved cuts applied per Scope Freeze §11.2)
- [ ] End-to-end demo: Idea → Story → Script → Storyboard → `COMPLETED`
- [ ] Success criteria SC-01 through SC-08 in [MVP Scope Freeze.md](../../MVP%20Scope%20Freeze.md) §8 verified
- [ ] 100% local inference — zero cloud API calls during demo run

---

## Explicitly Not Required for DoD (Visual MVP)

These are deferred or future — do **not** block issue closure:

| Excluded | Reference |
|----------|-----------|
| Neo4j / knowledge graph UI | Scope Freeze §5 |
| Keycloak / full RBAC | Scope Freeze §5 — US-25 token is sufficient |
| WebSocket live updates | HTTP polling acceptable |
| Export bundle / video stage | Deferred to Spark Full |
| Test coverage percentage targets | Add when CI matures |
| Multi-reviewer PR approval | Solo self-review acceptable |

---

## Pre-Approved Cuts (Scope Freeze §11.2)

If behind schedule, these may be removed **without SCR** — mark issue as cancelled, not done:

| Cut | Issues |
|-----|--------|
| Lineage UI | F-14, US-20 |
| API token auth | US-25 |
| Regenerate limit UI polish | US-09 (keep API; simplify UX) |

Do not cut US-02, US-06, US-07, US-08, US-12, US-14, US-16, US-17, or US-V01 without SCR.

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-09 | Initial Definition of Done for Visual MVP |
| 1.1 | 2026-06-09 | M0 Platform Skeleton; milestones aligned to Sprint 0–5 |

*End of document*
