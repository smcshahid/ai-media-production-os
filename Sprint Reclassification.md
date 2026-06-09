# AIMPOS-Spark Visual — Sprint Reclassification

**Document Type:** Execution Planning — Issue Milestone Map  
**Version:** 1.0  
**Status:** Approved — Effective June 9, 2026  
**Date:** June 9, 2026  
**Codename:** `AIMPOS-Spark-Visual`  
**Parent Documents:**

- [Architecture Freeze Review.md](./Architecture%20Freeze%20Review.md)
- [Sprint 0 — Platform Skeleton.md](./Sprint%200%20%E2%80%94%20Platform%20Skeleton.md)
- [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md)
- [GitHub Issues - Visual MVP.md](./GitHub%20Issues%20-%20Visual%20MVP.md)

---

## Classification key

| Code | Sprint | Purpose |
|------|--------|---------|
| **A** | Sprint 0 — Platform Skeleton | Login, project, upload, idle dashboard — no workflow, no AI |
| **B** | Sprint 1 — Infrastructure Validation | Full 9-service stack, Olares deploy, GPU smoke |
| **C** | Sprint 2 — Workflow Foundation | Temporal skeleton, approve/reject, live dashboard |
| **D** | Sprint 3 — Idea → Story | Idea capture, Story Architect, story review |
| **E** | Sprint 4 — Story → Script | Screenwriter, script review, audit viewer |
| **F** | Sprint 5 — Script → Storyboard | ComfyUI frames, gallery, US-V01 sign-off |
| **G** | Future Release | Deferred / pre-approved cuts |

**Method:** Conservative — prefer moving work **later** unless it directly blocks Sprint 0 Platform Skeleton.

---

## Epics and features

| Issue ID | Current Sprint | Recommended Sprint | Reason |
|----------|----------------|-------------------|--------|
| EPIC-01 | Sprint 1 | **B** | Closes when full stack + GPU validated on Olares |
| FEAT-INFRA | Sprint 1 | **B** | Docker, GPU smoke, Olares deploy — not user features |
| FEAT-01 | Sprint 1 | **A** | Default project seed — Create Project criterion |
| FEAT-03 | Sprint 2 | **C** | Start pipeline — requires validated infra (B) |
| FEAT-16 | Sprint 2 | **C** | Live polling needs US-07; idle UI via US-26 in A |
| FEAT-02 | Sprint 3 | **D** | Idea capture |
| FEAT-04 | Sprint 3 | **D** | AI Story Generation |
| FEAT-05 | Sprint 3 | **D** | Story review — Gate 1 |
| FEAT-06 | Sprint 3 | **E** | Script generation after approved story |
| FEAT-07 | Sprint 3 | **E** | Script review — Gate 2 |
| FEAT-13 | Sprint 3 | **E** | Audit viewer — after script-stage events |
| FEAT-08 | Sprint 4 | **F** | ComfyUI storyboard |
| FEAT-09 | Sprint 4 | **F** | Gallery review — terminal gate |
| FEAT-12 | Sprint 4 | **F** | Full version history UI |
| FEAT-14 | Sprint 4 | **G** | P1 lineage — pre-approved cut (Scope Freeze §11.2) |
| EPIC-02 | Sprint 2 | **C** | Pipeline Orchestration |
| EPIC-03 | Sprint 3 | **E** | Closes when script stage complete (spans D+E) |
| EPIC-04 | Sprint 4 | **F** | Storyboard stage |
| EPIC-06 | Sprint 1–5 | **A** | Governance umbrella opens Sprint 0 |

---

## User stories

| Issue ID | Current Sprint | Recommended Sprint | Reason |
|----------|----------------|-------------------|--------|
| US-02 | Sprint 1 | **B** | Full 9-container Olares deploy; not skeleton scope |
| US-04 | Sprint 1 | **A** | Database schema — blocks project and assets |
| US-03 | Sprint 1 | **A** | API health/logging |
| US-05 | Sprint 1 | **A** | MinIO upload — Upload Asset criterion |
| US-06 | Sprint 1 | **B** | GPU kill check — isolate from skeleton |
| US-01 | Sprint 1 | **A** | Default project — Create Project criterion |
| US-26 | Sprint 2 | **A** | Nav shell + idle routes for Platform Skeleton |
| US-25 | Sprint 2 | **A** | Bearer token — Login criterion (auth before FEAT-INFRA close) |
| US-10 | Sprint 2 | **C** | Full AC requires US-07; idle dashboard via US-26 |
| US-07 | Sprint 2 | **C** | Temporal workflow — after infra gate |
| US-08 | Sprint 2 | **C** | Approve/reject signals |
| US-09 | Sprint 2 | **D** | Regenerate needs real agents |
| US-24 | Sprint 2 | **F** | Durability for ComfyUI long jobs |
| US-11 | Sprint 3 | **D** | Enter idea |
| US-12 | Sprint 3 | **D** | Generate story |
| US-13 | Sprint 3 | **D** | Review story |
| US-14 | Sprint 3 | **E** | Generate script |
| US-15 | Sprint 3 | **E** | Approve script |
| US-23 | Sprint 3 | **E** | Audit trail |
| US-16 | Sprint 4 | **F** | Storyboard frames |
| US-17 | Sprint 4 | **F** | Gallery review → COMPLETED |
| US-20 | Sprint 4 | **G** | P1 lineage — pre-approved cut |
| US-22 | Sprint 4 | **F** | Asset version browser |
| US-V01 | Sprint 4 | **F** | Visual MVP sign-off |

---

## Tasks

| Issue ID | Current Sprint | Recommended Sprint | Reason |
|----------|----------------|-------------------|--------|
| T-02-01 | Sprint 1 | **B** | All 9 services — beyond S0 core compose |
| T-02-02 | Sprint 1 | **A** | PostgreSQL init |
| T-02-03 | Sprint 1 | **A** | MinIO bucket init |
| T-02-04 | Sprint 1 | **B** | Ollama model pin |
| T-02-05 | Sprint 1 | **B** | Olares deployment docs |
| T-02-06 | Sprint 1 | **B** | Zero-egress verification |
| T-04-01 | Sprint 1 | **A** | SQLAlchemy models |
| T-04-02 | Sprint 1 | **A** | Alembic migration |
| T-04-03 | Sprint 1 | **A** | Repository interfaces |
| T-03-01 | Sprint 1 | **A** | `/health` endpoint |
| T-03-02 | Sprint 1 | **A** | Structured logging |
| T-03-03 | Sprint 1 | **A** | Request ID propagation |
| T-05-01 | Sprint 1 | **A** | MinIO client wrapper |
| T-05-02 | Sprint 1 | **A** | Content-hash keys |
| T-05-03 | Sprint 1 | **A** | AssetVersion on upload |
| T-05-04 | Sprint 1 | **A** | Upload round-trip test |
| T-06-01 | Sprint 1 | **B** | Ollama smoke script |
| T-06-02 | Sprint 1 | **B** | ComfyUI smoke script |
| T-06-03 | Sprint 1 | **B** | GPU sequencing docs |
| T-01-01 | Sprint 1 | **A** | Projects table |
| T-01-02 | Sprint 1 | **A** | Default project seed |
| T-01-03 | Sprint 1 | **A** | GET /projects |
| T-01-04 | Sprint 1 | **A** | Project repository tests |
| T-26-01 | Sprint 2 | **A** | React Router app shell |
| T-26-02 | Sprint 2 | **A** | Nav bar and route guards |

---

## Summary by sprint

| Sprint | Count | Issue IDs |
|--------|------:|-----------|
| **A — Platform Skeleton** | 26 | US-01, US-03, US-04, US-05, US-25, US-26, FEAT-01, EPIC-06, T-01-01–04, T-02-02–03, T-03-01–03, T-04-01–03, T-05-01–04, T-26-01–02 |
| **B — Infrastructure Validation** | 11 | EPIC-01, FEAT-INFRA, US-02, US-06, T-02-01, T-02-04–06, T-06-01–03 |
| **C — Workflow Foundation** | 6 | EPIC-02, FEAT-03, FEAT-16, US-07, US-08, US-10 |
| **D — Idea → Story** | 7 | FEAT-02, FEAT-04, FEAT-05, US-09, US-11, US-12, US-13 |
| **E — Story → Script** | 7 | EPIC-03, FEAT-06, FEAT-07, FEAT-13, US-14, US-15, US-23 |
| **F — Script → Storyboard** | 9 | EPIC-04, FEAT-08, FEAT-09, FEAT-12, US-16, US-17, US-22, US-24, US-V01 |
| **G — Future Release** | 2 | FEAT-14, US-20 |
| | **68** | |

---

## GitHub milestone mapping

| Milestone | Issues |
|-----------|--------|
| Sprint 0 | 26 (class A) |
| Sprint 1 | 11 (class B) |
| Sprint 2 | 6 (class C) |
| Sprint 3 | 7 (class D) |
| Sprint 4 | 7 (class E) |
| Sprint 5 | 9 (class F) |
| Future Release | 2 (class G) |

---

## Sprint 0 exit gate — issues that must close

| Criterion | Closing issues |
|-----------|----------------|
| Login | US-25 |
| Create Project | US-01, FEAT-01, T-01-01–04 |
| Upload Asset | US-05, T-05-01–04 |
| View Dashboard (idle) | US-26, T-26-01–02 |
| Backend foundation | US-03, US-04, T-02-02–03, T-03-01–03, T-04-01–03 |

**Not required for Sprint 0 sign-off:** US-02, US-06, US-10, FEAT-16, EPIC-01, FEAT-INFRA (Sprint 1+).

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-09 | Initial conservative reclassification of 68 GitHub issues |

*End of document*
