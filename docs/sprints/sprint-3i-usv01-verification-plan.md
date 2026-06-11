# Sprint 3I — US-V01 Verification Plan

**Status:** **CLOSED** — executed Olares PASS 2026-06-11 · governance ACCEPT · tag `v0.4.0-usv01`.  
**Parent brief:** `docs/sprints/sprint-3i-usv01-brief.md`  
**Story:** US-V01 Visual MVP demo acceptance validation · P0 · 2 SP  
**Baseline:** `v0.3.6-us17` (`aimpos-api:us17`, `aimpos-worker:us17`)  
**Goal:** Final Visual MVP acceptance package and **M5 sign-off evidence**

**Authorization boundary:** Olares verify scripts, evidence collection, verification report, acceptance package, closure documentation. **No product code. No new features.**

---

## 0. Plan summary

| Phase | Deliverable |
|---|---|
| Pre-flight | Fresh project, ComfyUI, image/tag check |
| Execute | Normative demo S-00..S-16 incl. **A-01** S-12a/b |
| Durability | Worker restart procedure (SC-V06 / AC-9) |
| Collect | SQL attestation V-01..V-08 + **V-47** |
| Package | `evidence/us-v01-verification/olares-<date>/US-V01-ACCEPTANCE-PACKAGE.md` |
| Close | Verification report + governance closure + tag `v0.4.0-usv01` (proposed) |

**Estimated wall-clock:** 25–40 min (SCRIPT regen + 2× STORYBOARD ComfyUI batches + worker restart).

**Regression gate (local, before Olares):** API 81 · worker 36 · web 23 — no new unit tests required.

---

## 1. Olares execution steps

### 1.1 Pre-flight (PF-01..PF-06)

| ID | Action | Pass criteria |
|---|---|---|
| PF-01 | Confirm deploy images ≥ `us17` | `aimpos-api:us17`, `aimpos-worker:us17` |
| PF-02 | Alembic 0003 present | STORYBOARD multi-frame partial indexes |
| PF-03 | `POST http://127.0.0.1:3000/api/start` | ComfyUI queue HTTP 200 |
| PF-04 | API `/health` | postgres, redis, minio green |
| PF-05 | Create **fresh project** | `POST /projects` → new UUID; **not** `ba0c4636-…` |
| PF-06 | Assert no active run | `GET /pipeline/status` → no `RUNNING`/`AWAITING_APPROVAL` or 404 |

Export for evidence: `PROJECT`, `RUN_ID` (after S-03), cluster IP, image tags.

### 1.2 Normative execution sequence

All API calls via ClusterIP with `Authorization: Bearer $TOKEN`.

| Step | HTTP / action | Capture for evidence |
|---|---|---|
| **S-00** | ComfyUI launcher start | Log line `comfyui_ready` |
| **S-01** | `POST /projects` | `PROJECT` UUID |
| **S-02** | `POST /ideas` | Idea JSON; `IDEA` asset id if returned |
| **S-03** | `POST /pipeline/start` | `RUN_ID`; HTTP 201 |
| **S-04** | Poll `GET /pipeline/status` | Timestamp T_story_gate |
| **S-05** | `GET /assets?project_id=&stage=STORY` → latest; `PUT /assets/{id}` | Edited text snippet; new version/branch |
| **S-06** | `POST /pipeline/approve` STORY APPROVED | Approval JSON |
| **S-07** | Poll until SCRIPT gate | — |
| **S-08** | `POST /pipeline/approve` SCRIPT REJECT + note | Rationale text |
| **S-09** | `POST /pipeline/regenerate` SCRIPT | HTTP 200; `regenerations_used` |
| **S-10** | Poll until SCRIPT gate | — |
| **S-11** | `POST /pipeline/approve` SCRIPT APPROVED | — |
| **S-12** | Poll until STORYBOARD gate | Record `SB_V1=1`; frame count 4 |
| **S-12a** | `POST /pipeline/approve` STORYBOARD REJECT + note | Note: `US-V01 A-01: increase contrast and wider shots.` |
| **S-12b** | `POST /pipeline/regenerate` STORYBOARD | HTTP 200 |
| **S-12c** | Poll until STORYBOARD gate | Record `SB_V2=2`; frame count 4 |
| **S-13** | `GET /assets/{frame_id}/content` | HTTP 200; PNG magic bytes |
| **S-14** | `POST /pipeline/approve` STORYBOARD APPROVED | Final status JSON → `COMPLETED` |
| **S-15** | Worker restart procedure (§6) | Pre/post status match |
| **S-16** | Run SQL attestation §4 | Save all query output |

### 1.3 Idea payload (canonical)

```json
{
  "project_id": "<PROJECT>",
  "title": "US-V01 Visual MVP Acceptance",
  "paragraph": "A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.",
  "style_note": "cinematic"
}
```

### 1.4 Poll configuration

| Gate | Max wait | Interval | Fail on |
|---|---|---|---|
| STORY | 15 min | 15 s | `FAILED` |
| SCRIPT | 15 min | 15 s | `FAILED` |
| STORYBOARD (each) | 30 min | 20 s | `FAILED` |
| Post-regen STORYBOARD | 30 min | 20 s | `FAILED` |

### 1.5 Script layout (proposed files)

```
deploy/k8s/usv01-verify/
  verify_usv01.sh          # Full E2E S-00..S-16 + inline V-47 checks
  collect_usv01.sh         # Post-run SQL attestation → evidence folder
  run_remote.sh            # Source secrets; tee log
  prep_comfyui.sh          # Launcher start + probe
  create_project.sh        # Fresh project helper
```

**No product code** — bash + curl + psql only.

---

## 2. D-37 through D-47 validation mapping

Integrated attestation for the **full Olares run** (normative path + A-01).

| ID | Decision | Validated at | SQL / log evidence | Pass criteria |
|---|---|---|---|---|
| **D-37** | Approved story, no branch promotion | S-05, S-06 | V-03 STORY rows; approvals STORY/APPROVED | Latest STORY is `human-edit`; no STORY insert on S-06 |
| **D-38** | Append-only ai-draft regen | S-09, S-12b | V-04, V-47 | Monotonic versions; prior hashes unchanged |
| **D-39** | `script.fountain` semantics | S-07, S-11 | V-06 partial | SCRIPT row `text/plain`; lineage STORY→SCRIPT |
| **D-40** | Fountain validation | S-07, S-11 | Implicit | SCRIPT stored successfully |
| **D-41** | Approved script, no promotion | S-11, S-12 | V-03 | No SCRIPT insert on S-11 |
| **D-42** | Script regen inputs | S-08, S-09 | V-04; worker log | Regen only after SCRIPT reject |
| **D-43** | Storyboard frame contract | S-12, S-12c | V-05, V-47 | Shared `version`; `frame_index` 1..4 |
| **D-44** | Batch completeness | S-12, S-12c | V-05, V-47 | Exactly 4 frames per batch; no v1.5 orphans |
| **D-45** | Frame count = 4 | S-12, S-12c | V-05, V-47 | `COUNT=4` per version |
| **D-46** | Approved batch, no promotion | S-14 | V-02, V-03 | STORYBOARD/APPROVED once; row count stable on S-14 |
| **D-47** | Storyboard regen inputs | **S-12a, S-12b** | **V-47** | v1 intact; v2 new hashes; STORYBOARD reject note in approvals; regen audit |

---

## 3. Issue 43 AC + Scope Freeze SC mapping

| Requirement | Evidence ID | Source step |
|---|---|---|
| AC-1 Fresh project | PF-05, S-01 | Project create log |
| AC-2 Start pipeline | S-03 | `run_id` in log |
| AC-3 Story edit + approve | S-05, S-06 | PUT + approval |
| AC-4 Script reject/regen/approve | S-08 – S-11 | V-04 |
| AC-5 Approve all storyboard frames | S-14 | V-05 on v2 batch |
| AC-6 COMPLETED | S-14 | V-01 |
| AC-7 4 approvals + 3+ model calls | S-16 | V-02, V-07 (≥4 invocations with A-01) |
| AC-8 Lineage idea → frames | S-16 | V-06 |
| AC-9 Worker restart | S-15 | §6 durability log |
| SC-V01 Complete pipeline | V-01 | COMPLETED + STORYBOARD approved |
| SC-02 Local inference | V-07 | `model_id` present; no cloud URLs |
| SC-V03 3/3 gates | V-02 | §1B four core decisions |
| SC-V04 Versioned assets | V-04, V-05, V-47 | ≥4 types; 8 STORYBOARD rows |
| SC-V05 Audit completeness | V-07 | All agent completions logged |
| SC-V06 Durability | §6 | Status stable post-restart |
| SC-V07 Time to first story | V-08 | Δ < 5 min |
| SC-V08 Comprehension | Plan §1.2 API path | Documented in acceptance package |

---

## 4. SQL attestation queries

Run via `psql` on Olares postgres pod. Substitute `$PROJECT`, `$RUN_ID`.

### V-01 — Terminal state (SC-V01, AC-6)

```sql
SELECT id, status, current_stage, updated_at
FROM pipeline_runs WHERE id = '$RUN_ID';
-- Expected: status=COMPLETED, current_stage IS NULL
```

### V-02 — Human gate decisions (AC-7, SC-V03)

```sql
SELECT stage, decision, LEFT(rationale, 80) AS rationale, created_at
FROM approvals WHERE pipeline_run_id = '$RUN_ID'
ORDER BY created_at;
-- Expected minimum:
--   STORY/APPROVED, SCRIPT/REJECTED, SCRIPT/APPROVED,
--   STORYBOARD/REJECTED (A-01), STORYBOARD/APPROVED
```

### V-03 — No asset write on approve (D-37, D-41, D-46)

```sql
-- Snapshot total STORYBOARD rows before S-14 (from log) must equal after S-14
SELECT stage, COUNT(*) FROM asset_versions
WHERE project_id = '$PROJECT'
GROUP BY stage ORDER BY stage;
```

### V-04 — SCRIPT regen immutability (D-38, D-42)

```sql
SELECT version, branch, content_hash, created_at
FROM asset_versions
WHERE project_id = '$PROJECT' AND stage = 'SCRIPT'
ORDER BY version;
-- Expected: ≥2 rows; distinct content_hash; all ai-draft
```

### V-05 — Storyboard batch structure (D-43, D-45)

```sql
SELECT version,
       COUNT(*) AS frame_count,
       array_agg(metadata_json->>'frame_index' ORDER BY (metadata_json->>'frame_index')::int) AS frames
FROM asset_versions
WHERE project_id = '$PROJECT' AND stage = 'STORYBOARD'
GROUP BY version ORDER BY version;
-- Expected: version 1 → 4 frames [1,2,3,4]; version 2 → 4 frames [1,2,3,4]
```

### V-06 — Lineage chain (AC-8)

```sql
SELECT parent.stage AS parent_stage, child.stage AS child_stage, COUNT(*) AS edges
FROM lineage_edges le
JOIN asset_versions parent ON le.parent_id = parent.id
JOIN asset_versions child ON le.child_id = child.id
WHERE parent.project_id = '$PROJECT'
GROUP BY parent.stage, child.stage ORDER BY 1, 2;
-- Expected: STORY→SCRIPT (1+); SCRIPT→STORYBOARD (8 = 4 per batch × 2 batches)
```

### V-07 — Local model invocations (AC-7, SC-02, SC-V05)

```sql
SELECT event_type,
       payload->>'agent' AS agent,
       payload->>'stage' AS stage,
       model_id,
       created_at
FROM audit_events
WHERE pipeline_run_id = '$RUN_ID'
  AND event_type IN ('AGENT_TASK_COMPLETED', 'STAGE_STARTED')
ORDER BY created_at;
-- Expected: ≥4 AGENT_TASK_COMPLETED (story, script×2, storyboard×2)
-- All model_id non-null for AI completions
```

### V-08 — Time to first story (SC-V07)

```sql
SELECT event_type, payload->>'stage' AS stage, created_at
FROM audit_events
WHERE pipeline_run_id = '$RUN_ID'
  AND (event_type = 'STAGE_STARTED' OR event_type = 'PIPELINE_STATUS_CHANGED')
ORDER BY created_at;
-- Compute: idea/start → first AWAITING_APPROVAL at STORY < 5 minutes
```

### V-47 — D-47 extension (Amendment A-01)

```sql
-- Prior batch v1 unchanged (4 distinct content_hash)
SELECT version, frame_index, content_hash
FROM (
  SELECT version,
         metadata_json->>'frame_index' AS frame_index,
         content_hash
  FROM asset_versions
  WHERE project_id = '$PROJECT' AND stage = 'STORYBOARD' AND version = 1
) t ORDER BY frame_index::int;

-- New batch v2 (4 distinct content_hash; all differ from v1)
SELECT version, frame_index, content_hash
FROM (
  SELECT version,
         metadata_json->>'frame_index' AS frame_index,
         content_hash
  FROM asset_versions
  WHERE project_id = '$PROJECT' AND stage = 'STORYBOARD' AND version = 2
) t ORDER BY frame_index::int;

-- Rejection rationale stored for STORYBOARD
SELECT decision, rationale FROM approvals
WHERE pipeline_run_id = '$RUN_ID' AND stage = 'STORYBOARD' AND decision = 'REJECTED';

-- Regeneration audit
SELECT payload, created_at FROM audit_events
WHERE pipeline_run_id = '$RUN_ID'
  AND event_type = 'REGENERATION_REQUESTED'
  AND payload->>'stage' = 'STORYBOARD';
```

**V-47 pass criteria:**

| Check | Expected |
|---|---|
| v1 row count | 4 |
| v2 row count | 4 |
| v1 hashes after S-12b | Identical to snapshot at S-12 |
| v2 hashes | All differ from v1 (fresh generation) |
| STORYBOARD REJECTED | 1 row with non-empty rationale |
| REGENERATION_REQUESTED | ≥1 for STORYBOARD |

---

## 5. Evidence package structure

```
evidence/us-v01-verification/
  local-<date>/
    logs/
      pytest-api-baseline.txt      # optional regression snapshot
      pytest-worker-baseline.txt
      vitest-baseline.txt
  olares-<date>/
    US-V01-ACCEPTANCE-PACKAGE.md   # Master attestation document
    logs/
      usv01-verify.log             # Full script stdout
      usv01-collect.log            # SQL attestation output
      worker-restart.log           # S-15 durability
      worker-tail-storyboard.log   # D-47 agent completion excerpts
    sql/
      v01-terminal.txt
      v02-approvals.txt
      ...
      v47-d47-extension.txt
    metadata.json                  # PROJECT, RUN_ID, images, timestamps
```

### 5.1 US-V01-ACCEPTANCE-PACKAGE.md sections

| § | Content |
|---|---|
| 1 | Verification summary (PASS/FAIL table) |
| 2 | Environment (Olares, images, fresh project UUID, run_id) |
| 3 | Issue 43 AC mapping (AC-1..AC-9) |
| 4 | Scope Freeze SC-V01..SC-V08 attestation |
| 5 | D-37..D-47 validation matrix with evidence links |
| 6 | Amendment A-01 / V-47 attestation |
| 7 | Worker restart durability (SC-V06) |
| 8 | Deferred items (T-V01-03): video, export, lineage UI, asset history |
| 9 | Regression baseline (unit test counts) |
| 10 | M5 closure recommendation |

### 5.2 metadata.json template

```json
{
  "story": "US-V01",
  "date": "2026-06-11",
  "baseline_tag": "v0.3.6-us17",
  "project_id": "<uuid>",
  "run_id": "<uuid>",
  "api_image": "aimpos-api:us17",
  "worker_image": "aimpos-worker:us17",
  "amendment_a01": true,
  "storyboard_v1_version": 1,
  "storyboard_v2_version": 2,
  "final_status": "COMPLETED"
}
```

---

## 6. Worker restart durability procedure (SC-V06 / AC-9)

**When:** After **S-14** (`COMPLETED`). Pipeline must be in terminal success state — **not** mid-generation.

### 6.1 Procedure

| Step | Action | Record |
|---|---|---|
| DR-01 | Capture baseline | `GET /pipeline/status?project_id=$PROJECT` → save JSON |
| DR-02 | Capture run row | V-01 SQL output |
| DR-03 | Restart worker | `kubectl rollout restart deployment/aimpos-worker -n aimpos-mwayolares` |
| DR-04 | Wait ready | `kubectl rollout status deployment/aimpos-worker --timeout=300s` |
| DR-05 | Wait 30 s | Allow worker registration |
| DR-06 | Re-poll status | `GET /pipeline/status` × 3 at 10 s intervals |
| DR-07 | Compare | `status`, `current_stage`, `run_id` unchanged |
| DR-08 | Optional SQL | `pipeline_runs` row unchanged |

### 6.2 Pass criteria

| Field | Pre-restart | Post-restart |
|---|---|---|
| `status` | `COMPLETED` | `COMPLETED` |
| `current_stage` | `null` | `null` |
| `run_id` | `$RUN_ID` | `$RUN_ID` |

**Fail action:** Log incident; do **not** manual DB repair; file defect against US-12/workflow durability.

### 6.3 Out of scope

- Restart mid-`RUNNING` generation (not required by AC-9 for COMPLETED terminal state)
- API or Postgres restart (SC-V06 specifies worker)

---

## 7. T-V01-03 — Deferred items (release notes section)

Document in acceptance package §8 — **not in Visual MVP scope**:

| Item | Issue | Status |
|---|---|---|
| Video generation | US-18 | Deferred → Spark Full |
| Export bundle | US-19 | Deferred |
| Lineage graph UI | US-20 | Deferred |
| Asset history UI | US-22/US-23 | Deferred |
| Multi-project | — | Future |
| Keycloak / RBAC | US-25 area | Deferred |
| WebSocket live updates | — | Deferred |

---

## 8. Acceptance gates

| Verdict | Condition |
|---|---|
| **PASS / ACCEPT** | All Issue 43 ACs; SC-V01..SC-V08; D-37..D-47 incl. **V-47**; DR-01..08 pass; fresh project; no manual DB |
| **FAIL / REJECT** | Any check fails → defect on underlying story; hotfix + full re-run |

**M5 signed** when US-V01 governance closure ACCEPT follows Olares PASS.

---

## 9. Execution checklist

| # | Task | Owner | Done |
|---|---|---|---|
| 1 | Local regression green (81/36/23) | Dev | ✅ |
| 2 | Create `deploy/k8s/usv01-verify/` scripts | Dev | ✅ |
| 3 | PF-01..PF-06 pre-flight on Olares | Ops | ✅ |
| 4 | Execute S-00..S-16 incl. A-01 | Ops | ✅ |
| 5 | Execute DR-01..08 worker restart | Ops | ✅ |
| 6 | Run collect_usv01.sh SQL attestation | Ops | ✅ (inline S-16 + sql/) |
| 7 | Write US-V01-ACCEPTANCE-PACKAGE.md | Dev | ✅ |
| 8 | Write verification report | Dev | ✅ |
| 9 | Governance closure review | PO | ✅ |

---

## 10. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial plan — brief ACCEPT WITH AMENDMENT A-01 |

**Next step:** Implement verify scripts (bash only) → Olares run → acceptance package → M5 closure.
