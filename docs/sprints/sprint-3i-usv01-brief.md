# Sprint 3I — US-V01 Visual MVP Demo Acceptance (governance brief)

**Status:** **CLOSED** — governance ACCEPT 2026-06-11 · tag `v0.4.0-usv01` · M5 complete. Amendment **A-01** (D-47 extension) incorporated.  
**Verification plan:** `docs/sprints/sprint-3i-usv01-verification-plan.md` (**AUTHORIZED** — Olares execution only; no product code).  
**Story type:** **Verification / attestation** — not a feature story.  
**Story:** US-V01 "Visual MVP demo acceptance validation" · FEAT-09 · EPIC-04 · P0 · 2 SP · Sprint S4/S5.  
**Prerequisites (all closed):** US-08 ✅ · US-09 ✅ · US-12 ✅ · US-13 ✅ · US-14 ✅ · US-15 ✅ · US-16 ✅ · US-17 ✅.  
**Blocks:** **M5 — Visual MVP signed** (`docs/governance/definition-of-done.md` §M5). Unblocks Spark Full planning only after US-V01 closure.

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 43 `[US-V01]` (9 AC bullets, tasks T-V01-01..04).  
**Success criteria authority:** `MVP Scope Freeze.md` §8 (SC-V01, SC-02, SC-V03, SC-V04, SC-V05, SC-V06, SC-V07, SC-V08).  
**Decision records under test:** **`D-37` through `D-47`** (integrated attestation on Olares).

**Baseline:** `v0.3.6-us17` (`4604e5f` tag)

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

**Authorized work:** Olares verify scripts, evidence collection, verification report, acceptance package, closure tag — **zero product code** unless a **blocking defect** is discovered (hotfix on underlying story, re-run US-V01).

---

## 1. Objective

Execute **one authoritative end-to-end Visual MVP acceptance run on Olares** using a **fresh project**, validating the complete four-stage pipeline and attesting decision records **D-37 through D-47**:

```
Idea → STORY (human edit + approve) → SCRIPT (reject + regen + approve)
     → STORYBOARD (batch v1 → [A-01 reject + regen → batch v2] → batch approve) → COMPLETED
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
| US-20 Lineage graph UI | **Deferred** | AC-8 satisfied by **SQL** on `lineage_edges` |
| US-23 Asset history UI | **Deferred** | SC-V04 satisfied by **SQL** on `asset_versions` |

**US-V01 does not authorize** shipping US-20 or US-23.

---

## 1B. Governance resolution — approval count (Issue 43 AC-7)

Issue 43 requires **"4 approvals"** in the audit log. The **normative Issue 43 attestation** (unchanged by A-01) covers these four human gate outcomes:

| # | Stage | Decision | Demo step |
|---|---|---|---|
| 1 | STORY | APPROVED | S-06 (after human edit) |
| 2 | SCRIPT | REJECTED | S-08 |
| 3 | SCRIPT | APPROVED | S-11 (after regen) |
| 4 | STORYBOARD | APPROVED | S-14 (final batch, D-46) |

**Amendment A-01** adds a **fifth** `approvals` row (`STORYBOARD` / `REJECTED` at S-12a) as **D-47 extension evidence only**. It does **not** modify Issue 43 acceptance criteria, the normative demo path definition, or MVP scope — it is an additional evidence-collection step in the Olares run before the final batch approve.

---

## 1C. Governance amendment A-01 — D-47 extension verification

**Amendment ID:** **A-01**  
**Status:** **ACCEPTED** — mandatory in Olares acceptance run; evidence collection only.

| Step | Action | Purpose |
|---|---|---|
| **S-12a** | `POST /pipeline/approve` STORYBOARD `REJECT` + note | Record batch-level rejection (D-46 symmetry) |
| **S-12b** | `POST /pipeline/regenerate` STORYBOARD | Execute D-47 regeneration path |

**Verify (Olares SQL + logs):**

| Check | Expected |
|---|---|
| Storyboard batch version increments | `MAX(version)` increases by 1 (v1 → v2) |
| Prior batch remains intact | 4 rows at v1 unchanged (`content_hash` stable) |
| New batch complete | 4 rows at v2 with `frame_index` 1..4 |
| D-47 path executes | Worker `storyboard_agent_completed` after regen; regen audit `REGENERATION_REQUESTED` stage=STORYBOARD |
| Final approve | S-14 approves **v2** batch → `COMPLETED` |

**Does not modify:** Issue 43 AC text · normative demo path semantics · MVP scope freeze.

---

## 2. Source review

### 2.1 Approved acceptance criteria (Visual MVP Issue 43 — authoritative)

| # | Criterion | Demo step |
|---|---|---|
| AC-1 | Enter idea on **fresh project** | S-01, S-02 |
| AC-2 | Start pipeline | S-03 |
| AC-3 | Approve story **with one edit** | S-05, S-06 |
| AC-4 | Reject script once, regenerate, approve | S-08 – S-11 |
| AC-5 | Approve **all** storyboard frames (batch) | S-14 (final batch post A-01) |
| AC-6 | Pipeline status **COMPLETED** | S-14 |
| AC-7 | Audit: **4 approvals** + **3+ local model invocations** | S-16 (see §1B; ≥4 invocations with A-01) |
| AC-8 | Lineage shows idea → frames | S-16 SQL |
| AC-9 | Restart worker — state unchanged | S-15 |
| — | Pass without manual DB intervention | All steps |
| — | 100% local inference (**SC-02**) | Worker audit `model_id` |

### 2.2 Approved tasks (Visual MVP Issue 43)

| Task | US-V01 deliverable |
|---|---|
| T-V01-01 | `deploy/k8s/usv01-verify/verify_usv01.sh` |
| T-V01-02 | Acceptance package § SC-V01..SC-V08 |
| T-V01-03 | Acceptance package § Deferred items |
| T-V01-04 | Stakeholder sign-off in closure report |

### 2.3 Scope Freeze success criteria mapping

| ID | Criterion | US-V01 evidence |
|---|---|---|
| **SC-V01** | Idea → approved storyboard | E2E `COMPLETED` + STORYBOARD `APPROVED` |
| **SC-02** | 100% local inference | `audit_events.model_id`; no cloud URLs in logs |
| **SC-V03** | 3/3 human gates | 3× `APPROVED` + SCRIPT `REJECTED` (§1B) |
| **SC-V04** | ≥4 versioned assets per run | SQL asset chain incl. 8 STORYBOARD rows (2 batches) |
| **SC-V05** | 100% AI calls logged | Audit trail per agent invocation |
| **SC-V06** | Workflow durability | Worker restart procedure (§4 / verification plan §6) |
| **SC-V07** | Time to first story < 5 min | Audit timestamp delta |
| **SC-V08** | Creator comprehension | Documented API demo path |

---

## 3. Decision record attestation matrix (D-37 – D-47)

| ID | Title | Exercised? | Demo step | Olares evidence |
|---|---|---|---|---|
| **D-37** | Approved story (no branch promotion) | **Yes** | S-05, S-06 | `human-edit` STORY; no new row on approve |
| **D-38** | Regeneration append-only | **Yes** | S-09, S-12b | SCRIPT + STORYBOARD version chains |
| **D-39** | Script asset (`script.fountain`) | **Yes** | S-07, S-11 | SCRIPT rows + lineage |
| **D-40** | Fountain validation gate | **Yes** (implicit) | S-07, S-11 | Successful store |
| **D-41** | Approved script (no branch promotion) | **Yes** | S-11, S-12 | No SCRIPT row on approve |
| **D-42** | Script regen input contract | **Yes** | S-08, S-09 | Regen after SCRIPT reject |
| **D-43** | Storyboard frame contract | **Yes** | S-12, S-12b | Shared batch `version` + `frame_index` |
| **D-44** | Batch completeness | **Yes** | S-12, S-12b | 4 frames per batch; no orphans |
| **D-45** | Frame count = 4 | **Yes** | S-12, S-12b | `COUNT(*)=4` per batch version |
| **D-46** | Approved storyboard batch | **Yes** | S-14 | Single APPROVED; no new rows on approve |
| **D-47** | Storyboard regen input contract | **Yes (A-01)** | **S-12a, S-12b** | v1 preserved; v2 fresh batch; worker regen log |

---

## 4. Demo script (normative + A-01 extension)

**Environment:** Olares `aimpos-mwayolares`. **Fresh project UUID** — not `ba0c4636-…`. **Images:** ≥ `v0.3.6-us17`.

| Step | Action | Expected state | Decisions |
|---|---|---|---|
| S-00 | ComfyUI launcher start | Queue ready | — |
| S-01 | Create project | No active run | — |
| S-02 | `POST /ideas` | IDEA stored | — |
| S-03 | `POST /pipeline/start` | `RUNNING` / `STORY` | — |
| S-04 | Poll STORY gate | `AWAITING_APPROVAL` / `STORY` | — |
| S-05 | `PUT /assets/{story_id}` human edit | STORY `human-edit` v+1 | D-37 |
| S-06 | Approve STORY | SCRIPT generation | **D-37** |
| S-07 | Poll SCRIPT gate | `AWAITING_APPROVAL` / `SCRIPT` | D-39/D-40 |
| S-08 | Reject SCRIPT + note | Rejection recorded | D-42 setup |
| S-09 | Regenerate SCRIPT | New SCRIPT batch | **D-38**, **D-42** |
| S-10 | Poll SCRIPT gate | `AWAITING_APPROVAL` / `SCRIPT` | — |
| S-11 | Approve SCRIPT | STORYBOARD generation | **D-41** |
| S-12 | Poll STORYBOARD gate | 4 frames batch **v1** | **D-43..D-45** |
| **S-12a** | **Reject STORYBOARD + note** | Rejection recorded | **A-01 / D-47 setup** |
| **S-12b** | **Regenerate STORYBOARD** | New batch **v2** | **A-01 / D-38, D-47** |
| S-12c | Poll STORYBOARD gate | 4 frames batch **v2** | D-43..D-45 |
| S-13 | `GET /assets/{id}/content` sample | HTTP 200 PNG | content-read |
| S-14 | Approve STORYBOARD | **`COMPLETED`** | **D-46** |
| S-15 | Worker restart + poll | Status unchanged | **SC-V06** |
| S-16 | SQL attestation | §5 + V-47 | All AC + SC + D-37..D-47 |

**Forbidden:** Manual SQL to unblock the demo.

---

## 5. Olares SQL attestation queries (evidence templates)

See **verification plan §4** for full query catalog. Summary checks:

| ID | Check |
|---|---|
| V-01 | Terminal `COMPLETED` |
| V-02 | Core four gate decisions (§1B) |
| V-03 | No asset write on approve (D-37, D-41, D-46) |
| V-04 | SCRIPT regen immutability (D-38, D-42) |
| V-05 | Storyboard batch structure (D-43, D-45) |
| V-06 | Lineage chain (AC-8) |
| V-07 | Local model invocations (AC-7, SC-02, SC-V05) |
| V-08 | Time to first story (SC-V07) |
| **V-47** | **D-47 extension (A-01): v1 intact, v2 created, regen audit** |

### V-47 — D-47 extension (Amendment A-01)

```sql
-- Prior batch intact (4 rows at v1)
SELECT version, COUNT(*), array_agg(content_hash ORDER BY (metadata_json->>'frame_index')::int)
FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=1
GROUP BY version;

-- New batch (4 rows at v2)
SELECT version, COUNT(*), array_agg(content_hash ORDER BY (metadata_json->>'frame_index')::int)
FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=2
GROUP BY version;

-- STORYBOARD rejection + regen audit
SELECT stage, decision, LEFT(rationale, 60) FROM approvals
WHERE pipeline_run_id='$RUN_ID' AND stage='STORYBOARD' ORDER BY created_at;

SELECT COUNT(*) FROM audit_events
WHERE pipeline_run_id='$RUN_ID' AND event_type='REGENERATION_REQUESTED'
AND payload->>'stage'='STORYBOARD';
-- Expected: ≥1
```

---

## 6–13

Environment prerequisites, out-of-scope list, deliverables, verification strategy, acceptance gates, risks, project status, and document control are defined in **`docs/sprints/sprint-3i-usv01-verification-plan.md`**.

---

## 12. Project status

| Item | Status |
|---|---|
| **US-17** | **CLOSED** (`v0.3.6-us17`) |
| **US-V01** | **BRIEF ACCEPTED (A-01)** — verification plan authorized |
| **Frontier** | **US-V01** |
| **M5 Visual MVP signed** | Blocked on US-V01 Olares PASS + closure |

---

## 13. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial brief |
| 1.1 | 2026-06-11 | Governance submission |
| **1.2** | **2026-06-11** | **ACCEPT WITH AMENDMENT A-01 (D-47 extension S-12a/b); plan authorized** |

**Next step:** Execute verification plan on Olares → acceptance package → M5 closure.
