# Sprint 3I — US-V01 Visual MVP Demo Acceptance (governance brief)

**Status:** **SUBMITTED** — awaiting governance review. **No verification scripts, no code, no Olares runs authorized** until this brief is accepted.  
**Story:** US-V01 "Visual MVP demo acceptance validation" · FEAT-09 · EPIC-04 · P0 · 2 SP · Sprint S4/S5.  
**Prerequisites (all closed):** US-12 ✅ · US-13 ✅ · US-14 ✅ · US-15 ✅ · US-16 ✅ · US-17 ✅ · US-08 ✅ · US-09 ✅.  
**Blocks:** **M5 — Visual MVP signed** (Definition of Done §M5). Unblocks Spark Full planning only after closure.

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 43 `[US-V01]` (9 AC bullets, tasks T-V01-01..04).  
**Success criteria authority:** `MVP Scope Freeze.md` §8 (SC-V01, SC-02, SC-V03, SC-V04, SC-05, SC-06, SC-07, SC-08).

**Baseline:** `v0.3.6-us17` (@ US-17 closure)

---

## 1. Objective

Execute a **single end-to-end Visual MVP acceptance run on Olares** using a **fresh project** (no reuse of verification project `ba0c4636-…`), validating the complete pipeline:

```
Idea → STORY (edit + approve) → SCRIPT (reject + regen + approve) → STORYBOARD (approve batch) → COMPLETED
```

US-V01 is **verification and attestation only** — not a feature story. No new API routes, worker agents, web screens, or schema migrations unless a blocking defect is discovered (defects follow hotfix protocol, not US-V01 scope expansion).

| Dimension | Intent |
|---|---|
| **User value** | Product owner confidence that Visual MVP works as sold |
| **System value** | Repeatable demo script + evidence pack for M5 gate |
| **MVP boundary** | Terminates at **approved storyboard** / `COMPLETED`; video and export remain deferred |

---

## 1A. Governance resolution — issue dependency conflicts

Visual MVP Issue 43 lists dependencies on **#US-20** (lineage viewer) and **#US-23** (asset history). Both are **Deferred** per Scope Freeze §5 and must **not** block US-V01:

| Issue | Scope Freeze | US-V01 treatment |
|---|---|---|
| US-20 Lineage graph UI | **Deferred** | Lineage **verified via SQL** on `lineage_edges` (same as US-16/US-17 Olares scripts) |
| US-23 Asset history UI | **Deferred** | Versioning **verified via SQL** on `asset_versions` (SC-V04) |

**US-V01 does not authorize** shipping US-20 or US-23 to satisfy AC-8. SQL + audit evidence is sufficient for sign-off.

---

## 2. Source review

### 2.1 Approved acceptance criteria (Visual MVP Issue 43 — authoritative)

| # | Criterion |
|---|---|
| 1 | Enter idea on **fresh project** |
| 2 | Start pipeline |
| 3 | Approve story **with one edit** (human-edit branch) |
| 4 | Reject script **once**, regenerate, approve |
| 5 | Approve **all** storyboard frames (batch approve — D-46) |
| 6 | Pipeline status **COMPLETED** |
| 7 | Audit log: **4 approvals** and **3+ local model invocations** |
| 8 | Lineage shows idea → frames |
| 9 | Restart worker — state unchanged |
| — | Pass: all steps **without manual DB intervention** |
| — | **100% local inference** (SC-02) |

### 2.2 Approved tasks (Visual MVP Issue 43)

| Task | Description |
|---|---|
| T-V01-01 | Execute Visual MVP demo script on Olares |
| T-V01-02 | Verify SC-02, SC-03, SC-04, SC-05, SC-06, SC-07, SC-08 for 4-stage scope |
| T-V01-03 | Document deferred items (video, export) in release notes |
| T-V01-04 | Stakeholder sign-off on Visual MVP |

### 2.3 Scope Freeze success criteria mapping

| ID | Criterion | US-V01 evidence |
|---|---|---|
| **SC-V01** | Idea → approved storyboard | Full E2E run ending `COMPLETED` + STORYBOARD `APPROVED` |
| **SC-02** | 100% local inference | Audit events with `model_id`; zero cloud endpoints in worker logs |
| **SC-V03** | 3/3 human gates | 3× `APPROVED` (STORY after edit, SCRIPT after regen, STORYBOARD batch) + 1× `REJECTED` (SCRIPT) |
| **SC-V04** | ≥4 versioned assets per run | SQL: IDEA, STORY (≥2 if edit), SCRIPT (≥2 if regen), STORYBOARD (4 frames) |
| **SC-05** | 100% AI calls logged | `audit_events` with `AGENT_TASK_COMPLETED` / `ASSET_STORED` + `model_id` |
| **SC-06** | Workflow durability | Worker pod restart mid-run or after gate; status recoverable via poll |
| **SC-V07** | Time to first story | < 5 min idea → STORY gate (timestamp delta in audit log) |
| **SC-08** | Creator comprehension | Manual UI walkthrough OR scripted API path documented for solo founder |

---

## 3. Demo script (normative sequence)

All steps on Olares namespace `aimpos-mwayolares`. **Fresh project UUID** created via `POST /projects` (or dashboard) — **do not** reuse `ba0c4636-817c-423b-9771-20100e080b76`.

| Step | Action | Expected state |
|---|---|---|
| S-01 | Create project | Empty project, no active run |
| S-02 | `POST /ideas` | IDEA asset stored |
| S-03 | `POST /pipeline/start` | `RUNNING` / `STORY` |
| S-04 | Wait for STORY gate | `AWAITING_APPROVAL` / `STORY` |
| S-05 | `PUT /assets/{story_id}` — one human edit | STORY `human-edit` branch, version+1 |
| S-06 | `POST /pipeline/approve` STORY `APPROVED` | Advances to SCRIPT generation |
| S-07 | Wait for SCRIPT gate | `AWAITING_APPROVAL` / `SCRIPT` |
| S-08 | `POST /pipeline/approve` SCRIPT `REJECT` + note | Rejection recorded |
| S-09 | `POST /pipeline/regenerate` SCRIPT | New SCRIPT batch; `RUNNING` / `SCRIPT` |
| S-10 | Wait for SCRIPT gate | `AWAITING_APPROVAL` / `SCRIPT` |
| S-11 | `POST /pipeline/approve` SCRIPT `APPROVED` | STORYBOARD generation |
| S-12 | Wait for STORYBOARD gate | `AWAITING_APPROVAL` / `STORYBOARD`; 4 PNG frames (`D-45`) |
| S-13 | Optional: `GET /assets/{id}/content` sample PNG | HTTP 200 `image/png` |
| S-14 | `POST /pipeline/approve` STORYBOARD `APPROVED` | **`COMPLETED`** / `current_stage=null` |
| S-15 | Worker restart test | `kubectl rollout restart deploy/aimpos-worker`; poll status unchanged |
| S-16 | SQL attestation | Approvals count, lineage, audit model invocations |

**Forbidden:** Manual SQL updates to `pipeline_runs`, `approvals`, or `asset_versions` to unblock the demo.

---

## 4. Environment prerequisites (Olares)

| Prerequisite | Source |
|---|---|
| API + worker images ≥ `v0.3.6-us17` | US-17 closure |
| Alembic **0003** applied | US-16 migration (multi-frame STORYBOARD batches) |
| ComfyUI running | Launcher `POST http://127.0.0.1:3000/api/start` before STORYBOARD stages |
| Worker `COMFYUI_HOST` | `http://comfyui.comfyuisharev2server-shared:8190` |
| Temporal + Postgres + MinIO | M1-DV stack healthy |

---

## 5. Explicitly out of scope (US-V01)

| Item | Rationale |
|---|---|
| Video stage (US-18) | Deferred — Scope Freeze |
| Export bundle (US-19) | Deferred |
| Lineage graph UI (US-20) | Deferred — SQL only |
| Asset history UI (US-22) | Deferred |
| Web SPA deploy on Olares | Optional; API-first demo satisfies AC |
| New features / refactors | Verification story only |
| Multi-project support | Single fresh project sufficient |

---

## 6. Deliverables (on acceptance of this brief)

| Deliverable | Path (proposed) |
|---|---|
| Olares demo script | `deploy/k8s/usv01-verify/verify_usv01.sh` |
| Evidence package | `evidence/us-v01-verification/olares-<date>/US-V01-ACCEPTANCE-PACKAGE.md` |
| Implementation report | `docs/sprints/sprint-3i-usv01-implementation-report.md` (verification report) |
| Release notes — deferred items | Section in acceptance package (T-V01-03) |
| Closure report + tag | `v0.3.7-usv01` (proposed; confirm at plan review) |

**No code authorized in brief phase.** Implementation plan follows brief acceptance.

---

## 7. Acceptance gates (closure)

| Gate | Requirement |
|---|---|
| **ACCEPT** | All Issue 43 ACs evidenced on fresh Olares project; SC-02..SC-08 attested; no manual DB intervention |
| **CONDITIONAL ACCEPT** | Not sufficient for M5 — Visual MVP requires full pass |
| **REJECT** | Re-run after defect fix on underlying story (not US-V01 feature work) |

---

## 8. Risk register

| ID | Risk | Mit | Impact |
|---|---|---|---|
| R1 | ComfyUI not started | Launcher preflight in verify script | STORYBOARD hang |
| R2 | Stale active run on fresh project | Assert no run before S-03 | 409 on start |
| R3 | GPU wall-clock exceeds SC-V07 on slow day | Record timestamps; retry once | Medium |
| R4 | Issue 43 deps US-20/US-23 | SQL substitution (§1A) | Governance confusion |
| R5 | Reused verification project | Mandate fresh UUID | Invalid sign-off |

---

## 9. Project status (on US-V01 brief submission)

| Item | Status |
|---|---|
| **US-17** | **CLOSED** (`v0.3.6-us17`) |
| **US-V01** | **BRIEF SUBMITTED** — awaiting governance review |
| **Frontier** | **US-V01** |
| **M5 Visual MVP signed** | Blocked on US-V01 closure |

---

## 10. Document control

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-06-11 | Agent | Initial governance brief post US-17 closure |

**Next step:** Governance review → ACCEPT → implementation plan → authorized Olares verification run.
