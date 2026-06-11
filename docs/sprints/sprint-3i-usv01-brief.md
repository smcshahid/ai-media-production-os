# Sprint 3I — US-V01 Visual MVP Demo Acceptance (governance brief)

**Status:** **SUBMITTED** — awaiting governance review. **No verification scripts, no code, no Olares runs, no implementation plan authorized** until this brief is **ACCEPTED**.  
**Story type:** **Verification / attestation** — not a feature story.  
**Story:** US-V01 "Visual MVP demo acceptance validation" · FEAT-09 · EPIC-04 · P0 · 2 SP · Sprint S4/S5.  
**Prerequisites (all closed):** US-08 ✅ · US-09 ✅ · US-12 ✅ · US-13 ✅ · US-14 ✅ · US-15 ✅ · US-16 ✅ · US-17 ✅.  
**Blocks:** **M5 — Visual MVP signed** (`docs/governance/definition-of-done.md` §M5). Unblocks Spark Full planning only after US-V01 closure.

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 43 `[US-V01]` (9 AC bullets, tasks T-V01-01..04).  
**Success criteria authority:** `MVP Scope Freeze.md` §8 (SC-V01, SC-02, SC-V03, SC-V04, SC-V05, SC-V06, SC-V07, SC-V08).  
**Decision records under test:** **`D-37` through `D-47`** (integrated attestation on Olares).

**Baseline:** `v0.3.6-us17` (`4604e5f` tag · `69c40b3` @ main)

---

## 0. Story classification — verification only

US-V01 is the **Visual MVP sign-off gate**. It **does not** authorize:

| Forbidden in US-V01 | Rationale |
|---|---|
| New API routes or response shapes | Platform frozen post US-17 |
| New worker agents or Temporal activities | All four stages implemented |
| New web screens or UX flows | Review surfaces closed (US-13/15/17) |
| Schema migrations | Scope Freeze |
| Lineage UI (US-20) or asset history UI (US-22/23) | Deferred — SQL attestation only |
| Video stage (US-18) or export (US-19) | Deferred |
| Gallery framework abstractions | Explicitly rejected in US-17 governance |
| Refactors, perf work, or "while we're here" fixes | Defect hotfix protocol only |

**Authorized work after brief ACCEPT:** Olares verify scripts, evidence collection, verification report, acceptance package, closure tag — **zero product code** unless a **blocking defect** is discovered during the run (hotfix on the underlying story, re-run US-V01).

---

## 1. Objective

Execute **one authoritative end-to-end Visual MVP acceptance run on Olares** using a **fresh project**, validating the complete four-stage pipeline and attesting decision records **D-37 through D-47**:

```
Idea → STORY (human edit + approve) → SCRIPT (reject + regen + approve) → STORYBOARD (batch approve) → COMPLETED
```

| Dimension | Intent |
|---|---|
| **User value** | Product-owner confidence that Visual MVP delivers Idea → approved storyboard on real hardware |
| **System value** | Repeatable demo script + evidence pack closing **M5** |
| **MVP boundary** | Terminates at **`COMPLETED`** after approved storyboard batch; no video |

---

## 1A. Governance resolution — issue dependency conflicts

Visual MVP Issue 43 lists **#US-20** (lineage viewer) and **#US-23** (asset history) as dependencies. Both are **Deferred** per Scope Freeze §5:

| Issue | Scope Freeze | US-V01 treatment |
|---|---|---|
| US-20 Lineage graph UI | **Deferred** | AC-8 satisfied by **SQL** on `lineage_edges` (IDEA→STORY→SCRIPT→STORYBOARD chain) |
| US-23 Asset history UI | **Deferred** | SC-V04 satisfied by **SQL** on `asset_versions` version monotonicity |

**US-V01 does not authorize** shipping US-20 or US-23. SQL + audit evidence is sufficient for sign-off.

---

## 1B. Governance resolution — approval count (Issue 43 AC-7)

Issue 43 requires **"4 approvals"** in the audit log. The normative demo produces **four `approvals` rows** on the run:

| # | Stage | Decision | Demo step |
|---|---|---|---|
| 1 | STORY | APPROVED | S-06 (after human edit) |
| 2 | SCRIPT | REJECTED | S-08 |
| 3 | SCRIPT | APPROVED | S-11 (after regen) |
| 4 | STORYBOARD | APPROVED | S-14 (batch approve, D-46) |

Three human **gates** passed (STORY, SCRIPT, STORYBOARD) plus one SCRIPT rejection — satisfies **SC-V03** (3/3 gates with recorded decisions).

---

## 2. Source review

### 2.1 Approved acceptance criteria (Visual MVP Issue 43 — authoritative)

| # | Criterion | Demo step |
|---|---|---|
| AC-1 | Enter idea on **fresh project** | S-01, S-02 |
| AC-2 | Start pipeline | S-03 |
| AC-3 | Approve story **with one edit** | S-05, S-06 |
| AC-4 | Reject script once, regenerate, approve | S-08 – S-11 |
| AC-5 | Approve **all** storyboard frames (batch) | S-14 |
| AC-6 | Pipeline status **COMPLETED** | S-14 |
| AC-7 | Audit: **4 approvals** + **3+ local model invocations** | S-16 |
| AC-8 | Lineage shows idea → frames | S-16 SQL |
| AC-9 | Restart worker — state unchanged | S-15 |
| — | Pass without manual DB intervention | All steps |
| — | 100% local inference (**SC-02**) | Worker audit `model_id` |

### 2.2 Approved tasks (Visual MVP Issue 43)

| Task | US-V01 deliverable |
|---|---|
| T-V01-01 | `deploy/k8s/usv01-verify/verify_usv01.sh` — Olares E2E |
| T-V01-02 | Acceptance package § SC-V01..SC-V08 attestation |
| T-V01-03 | Acceptance package § Deferred items (video, export) |
| T-V01-04 | Stakeholder sign-off recorded in closure report |

### 2.3 Scope Freeze success criteria mapping

| ID | Criterion | US-V01 evidence |
|---|---|---|
| **SC-V01** | Idea → approved storyboard | E2E ending `COMPLETED` + STORYBOARD `APPROVED` |
| **SC-02** | 100% local inference | `audit_events.model_id` populated; no cloud URLs in worker logs |
| **SC-V03** | 3/3 human gates | 3× `APPROVED` + 1× `REJECTED` on SCRIPT (see §1B) |
| **SC-V04** | ≥4 versioned assets per run | SQL: IDEA + STORY (≥2 w/ edit) + SCRIPT (≥2 w/ regen) + 4 STORYBOARD frames |
| **SC-V05** | 100% AI calls logged | `AGENT_TASK_COMPLETED` / `ASSET_STORED` with `model_id` per stage |
| **SC-V06** | Workflow durability | Worker rollout restart; `pipeline/status` unchanged post-restart |
| **SC-V07** | Time to first story < 5 min | Audit timestamp delta: `STAGE_STARTED` STORY → STORY gate |
| **SC-V08** | Creator comprehension | Documented API demo path (solo founder executable) |

---

## 3. Decision record attestation matrix (D-37 – D-47)

US-V01 **re-validates** the integrated decision stack on Olares. Individual decisions were closed per-story; US-V01 proves they **compose correctly** in one fresh run.

| ID | Title | Exercised in demo? | Demo step | Olares evidence |
|---|---|---|---|---|
| **D-37** | Approved story resolution (no branch promotion) | **Yes** | S-05, S-06 | Latest STORY row is `human-edit` after edit; `approvals` STORY/APPROVED; **no new STORY row on approve** |
| **D-38** | Regeneration append-only ai-draft | **Yes** | S-09 | SCRIPT `version` increments; prior SCRIPT row `content_hash` unchanged |
| **D-39** | Script asset semantics (`script.fountain`) | **Yes** | S-07, S-11 | `asset_versions` SCRIPT row; `text/plain`; lineage STORY→SCRIPT |
| **D-40** | Fountain validation gate | **Yes** (implicit) | S-07, S-11 | Successful SCRIPT store implies validator pass |
| **D-41** | Approved script resolution (no branch promotion) | **Yes** | S-11, S-12 | `approvals` SCRIPT/APPROVED; **no new SCRIPT row on approve**; storyboard reads approved script |
| **D-42** | Script regen input contract | **Yes** | S-08, S-09 | Regen after SCRIPT REJECTED; new ai-draft from approved story + rejection note only |
| **D-43** | Storyboard frame asset contract | **Yes** | S-12 | 4 STORYBOARD rows sharing batch `version`; distinct `metadata_json.frame_index` |
| **D-44** | Storyboard batch completeness | **Yes** (implicit) | S-12 | Exactly 4 frames at gate; no orphan partial batch |
| **D-45** | Storyboard frame count = 4 | **Yes** | S-12 | `COUNT(*)=4` at `MAX(version)` for STORYBOARD |
| **D-46** | Approved storyboard batch (no branch promotion) | **Yes** | S-14 | Single STORYBOARD/APPROVED; **no new STORYBOARD rows on approve**; `COMPLETED` |
| **D-47** | Storyboard regen input contract | **Regression** | — | **Not in normative demo path** (single STORYBOARD approve). Attested by **US-17 closure** (`806b671a` run). Optional extension V-47 if governance requires re-exercise |

**Normative rule:** US-V01 **must not fail** because D-47 is not re-run — US-17 is a hard prerequisite with Olares PASS. If governance requires D-47 re-exercise in the same run, add optional steps S-12a (STORYBOARD REJECT) + S-12b (STORYBOARD regen) before S-14 — **not authorized unless brief amended**.

---

## 4. Demo script (normative sequence)

**Environment:** Olares namespace `aimpos-mwayolares`.  
**Project:** **Fresh UUID** via `POST /projects` — **do not** reuse verification project `ba0c4636-817c-423b-9771-20100e080b76`.  
**Images:** `aimpos-api:us17`, `aimpos-worker:us17` (or later if hotfixed).

| Step | Action | Expected state | Decisions touched |
|---|---|---|---|
| S-00 | ComfyUI launcher `POST :3000/api/start` | ComfyUI queue ready | — |
| S-01 | Create project | Empty project, no active run | — |
| S-02 | `POST /ideas` | IDEA asset stored | — |
| S-03 | `POST /pipeline/start` | `RUNNING` / `STORY` | — |
| S-04 | Poll until STORY gate | `AWAITING_APPROVAL` / `STORY` | — |
| S-05 | `PUT /assets/{story_id}` — one human edit | STORY `human-edit` branch, `version+1` | D-37 input |
| S-06 | `POST /pipeline/approve` STORY `APPROVED` | Advances to SCRIPT generation | **D-37** |
| S-07 | Poll until SCRIPT gate | `AWAITING_APPROVAL` / `SCRIPT` | D-39/D-40 |
| S-08 | `POST /pipeline/approve` SCRIPT `REJECT` + note | Rejection recorded | D-42 setup |
| S-09 | `POST /pipeline/regenerate` SCRIPT | New SCRIPT batch | **D-38**, **D-42** |
| S-10 | Poll until SCRIPT gate | `AWAITING_APPROVAL` / `SCRIPT` | — |
| S-11 | `POST /pipeline/approve` SCRIPT `APPROVED` | STORYBOARD generation | **D-41** |
| S-12 | Poll until STORYBOARD gate | 4 PNG frames at shared batch version | **D-43**, **D-44**, **D-45** |
| S-13 | `GET /assets/{frame_id}/content` (sample) | HTTP 200 `image/png` | D-37 content-read extension |
| S-14 | `POST /pipeline/approve` STORYBOARD `APPROVED` | **`COMPLETED`** | **D-46** |
| S-15 | `kubectl rollout restart deploy/aimpos-worker`; poll | Status unchanged | **SC-V06** |
| S-16 | SQL attestation queries | See §5 | All AC + SC |

**Forbidden:** Manual SQL `UPDATE`/`INSERT` on `pipeline_runs`, `approvals`, or `asset_versions` to unblock the demo.

---

## 5. Olares SQL attestation queries (evidence templates)

All queries scoped to `$PROJECT` and `$RUN_ID` from the fresh run.

### V-01 — Pipeline terminal state (SC-V01, AC-6)

```sql
SELECT status, current_stage FROM pipeline_runs WHERE id = '$RUN_ID';
-- Expected: COMPLETED, current_stage NULL
```

### V-02 — Four approval records (AC-7, SC-V03)

```sql
SELECT stage, decision, LEFT(rationale, 60)
FROM approvals WHERE pipeline_run_id = '$RUN_ID' ORDER BY created_at;
-- Expected: STORY/APPROVED, SCRIPT/REJECTED, SCRIPT/APPROVED, STORYBOARD/APPROVED
```

### V-03 — No asset write on approve (D-37, D-41, D-46)

```sql
-- STORYBOARD row count before and after S-14 must match (compare audit timestamps or pre/post count)
SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';
```

### V-04 — SCRIPT regen immutability (D-38, D-42)

```sql
SELECT version, branch, content_hash FROM asset_versions
WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version;
-- Expected: ≥2 ai-draft rows; distinct content_hash per version
```

### V-05 — Storyboard batch (D-43, D-45)

```sql
WITH latest AS (SELECT MAX(version) v FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD')
SELECT version, metadata_json->>'frame_index' fi FROM asset_versions av, latest
WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=latest.v ORDER BY fi::int;
-- Expected: 4 rows, frame_index 1..4
```

### V-06 — Lineage chain (AC-8)

```sql
-- IDEA → STORY → SCRIPT → STORYBOARD (4 edges minimum script→frames)
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions av ON le.child_id = av.id
WHERE av.project_id = '$PROJECT';
-- Expected: ≥6 (story→script + script→4 frames)
```

### V-07 — Local model invocations (AC-7, SC-02, SC-V05)

```sql
SELECT event_type, payload->>'agent' agent, model_id
FROM audit_events WHERE pipeline_run_id = '$RUN_ID'
AND event_type IN ('AGENT_TASK_COMPLETED', 'ASSET_STORED')
ORDER BY created_at;
-- Expected: ≥3 AGENT_TASK_COMPLETED with non-null model_id (story, script×2, storyboard)
```

### V-08 — Time to first story (SC-V07)

```sql
SELECT event_type, created_at FROM audit_events
WHERE pipeline_run_id = '$RUN_ID' AND payload->>'stage' = 'STORY'
ORDER BY created_at LIMIT 5;
-- Delta from STAGE_STARTED to first AWAITING_APPROVAL/STORY gate < 5 minutes
```

---

## 6. Environment prerequisites (Olares)

| Prerequisite | Verification |
|---|---|
| API + worker ≥ `v0.3.6-us17` | `kubectl get deploy -o jsonpath='{.spec.template.spec.containers[0].image}'` |
| Alembic **0003** applied | Partial unique indexes for STORYBOARD multi-frame |
| ComfyUI running | Launcher start + `/queue` HTTP 200 |
| Worker `COMFYUI_HOST` | `http://comfyui.comfyuisharev2server-shared:8190` |
| Temporal healthy | Worker logs show activity registration |
| Postgres + MinIO healthy | API `/health` green |

---

## 7. Explicitly out of scope

| Item | Classification |
|---|---|
| Video (US-18), Export (US-19) | Deferred |
| Lineage UI (US-20), Asset history (US-22/23) | Deferred |
| Web SPA on Olares | Optional — API demo is sufficient |
| STORYBOARD regen in normative path | D-47 regression via US-17 |
| New platform capabilities | **Forbidden** (§0) |
| Multi-project demo | Single fresh project sufficient |

---

## 8. Deliverables (authorized after brief ACCEPT)

| Deliverable | Path |
|---|---|
| Olares verify script | `deploy/k8s/usv01-verify/verify_usv01.sh` |
| SQL attestation helper | `deploy/k8s/usv01-verify/collect_usv01.sh` |
| Olares evidence | `evidence/us-v01-verification/olares-<date>/` |
| Acceptance package | `…/US-V01-ACCEPTANCE-PACKAGE.md` |
| Verification report | `docs/sprints/sprint-3i-usv01-verification-report.md` |
| Closure report + tag | `v0.4.0-usv01` (proposed — confirm at plan review) |

**Implementation plan** (`sprint-3i-usv01-verification-plan.md`) follows brief ACCEPT — not authorized now.

---

## 9. Olares verification strategy

| Phase | Activity |
|---|---|
| **Pre-flight** | Deploy/tag check; ComfyUI start; create fresh project |
| **Execute** | Run normative demo S-00..S-16 |
| **Collect** | Logs, SQL query output, worker/API log excerpts |
| **Attest** | Map each AC + SC + D-37..D-47 row to evidence |
| **Package** | Acceptance package with PASS/FAIL per check |
| **Closure** | Governance ACCEPT → tag → M5 signed |

**Estimated wall-clock:** 15–25 min (includes one SCRIPT regen + ComfyUI 4-frame batch).

**Regression gate before Olares:** API 81 / worker 36 / web 23 unit tests green on `v0.3.6-us17` baseline (no new tests required unless defect found).

---

## 10. Acceptance gates (governance closure)

| Verdict | Condition |
|---|---|
| **ACCEPT** | All Issue 43 ACs pass on fresh Olares project; SC-V01..SC-V08 attested; D-37..D-46 validated in run; D-47 regression cited from US-17; no manual DB intervention |
| **CONDITIONAL ACCEPT** | **Not sufficient** for M5 |
| **REJECT** | Any AC/SC failure → defect on underlying story; fix + re-run US-V01 |

---

## 11. Risk register

| ID | Risk | Mitigation |
|---|---|---|
| R1 | ComfyUI not started | S-00 preflight in verify script |
| R2 | Reused verification project | Mandate fresh UUID; script asserts empty run |
| R3 | Stale active run (409) | Pre-check `pipeline/status` before S-03 |
| R4 | SC-V07 miss on slow GPU day | Record timestamps; document actual delta |
| R5 | Scope creep ("add UI for sign-off") | §0 forbidden list |
| R6 | D-47 not re-run | US-17 prerequisite + optional V-47 extension |
| R7 | Issue 43 deps US-20/US-23 | SQL substitution (§1A) |

---

## 12. Project status

| Item | Status |
|---|---|
| **US-17** | **CLOSED** (`v0.3.6-us17`) |
| **US-V01** | **BRIEF SUBMITTED** — awaiting governance review |
| **Frontier** | **US-V01** |
| **M5 Visual MVP signed** | Blocked on US-V01 closure |

---

## 13. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial brief post US-17 closure |
| 1.1 | 2026-06-11 | Governance submission: D-37..D-47 matrix, SQL attestation, verification-only classification |

**Next step:** Governance review of this brief → **ACCEPT** → verification plan → authorized Olares run. **No code.**
