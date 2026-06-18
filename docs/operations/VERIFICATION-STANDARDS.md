# AIMPOS Verification Standards

**Version:** 1.0 (Phase 6.5)  
**Authority:** Verification Lead  
**Scope:** US-V03 through US-V07 and future acceptance suites

---

## 1. Purpose

Standardize Olares and local acceptance scripts so verification defects (SEV-3 overlaps, orphaned runs, stdout pollution) do not recur.

---

## 2. Unified script architecture

### 2.1 Layout

| Layer | Location | Role |
|-------|----------|------|
| Shared library | `deploy/k8s/lib/verify_common.sh` *(target)* | `log`, `psql`, `poll_until`, `approve`, `cancel_active_runs`, `wait_for_project_idle` |
| Path runner | `deploy/k8s/usvXX-verify/verify_usvXX_e2e.sh` | Path orchestration only |
| Supplement | `deploy/k8s/usvXX-verify/verify_path_*_olares.sh` | Isolated path re-run after SEV-3 |
| Local gate | `deploy/dev/verify_phaseX_local.ps1` | Pytest/vitest aggregation |
| Orchestrator | `deploy/dev/verify_usvXX_olares.ps1` | SCP, deploy, E2E, evidence fetch |

**Current state:** US-V07 implements the target pattern inline; US-V05/V06 duplicate partial helpers without flock/Temporal terminate. Consolidation is **documented**; library extraction is deferred to a future implementation sprint (no schema/workflow change authorized in Phase 6.5).

### 2.2 Logging contract

```bash
log() { echo "$(date -Iseconds) $*" >> "$EVID/e2e-olares.log"; echo "$(date -Iseconds) $*" >&2; }
```

- **Never** use `tee` on stdout for functions whose output is captured (`create_episode`, `run_episode_path` return values).
- All operator-visible progress goes to **stderr** or log file only.

### 2.3 Concurrency protection

Every long-running E2E entrypoint **must**:

1. Acquire exclusive lock: `flock -n 9` on `$EVID/.e2e.lock`
2. Refuse start if another instance holds the lock
3. Document lock path in script header

**Incident:** US-V07-C1-ORPHAN — dual `verify_usv07_e2e.sh` + poll watcher (SEV-3, closed).

### 2.4 Cancel and idle semantics

`cancel_active_runs` **must**:

1. Collect `temporal_workflow_id` (or `spark-pipeline-{run_id}`) for active runs
2. `tctl workflow terminate` each workflow
3. `UPDATE pipeline_runs SET status='CANCELLED'`
4. `wait_for_project_idle` until zero rows in `(PENDING, RUNNING, AWAITING_APPROVAL)`

**Incident:** US-V05/V06 cancel was DB-only; Temporal continued → status drift.

### 2.5 Polling contract

| Context | Status URL |
|---------|------------|
| Legacy / single-run project | `GET /pipeline/status?project_id=` |
| Episode-scoped (US-V07+) | append `&episode_id=` |

Poll loop **must** fail fast on `status=FAILED`. Default interval: 15s. Stage timeouts:

| Stage | Default max (s) |
|-------|-----------------|
| STORY / SCRIPT | 900 |
| STORYBOARD (per scene) | 2400 |
| VIDEO + narration (per scene) | 5400 |
| COMPLETED | 120 |

### 2.6 Approval gate protection

1. Poll until `AWAITING_APPROVAL` with matching `current_stage` (and `current_scene_index` when applicable)
2. Call `POST /pipeline/approve` once per gate
3. Re-poll until stage advances or timeout

**Known product gap (debt TD-P6.5-01):** `POST /pipeline/approve` resolves **project-level** active run, not `episode_id`. Acceptable while one active run per project is enforced; verification must not start overlapping episode runs.

**Retry on approve:** US-V03 pattern — up to 12 attempts with 5s backoff on 409/502.

### 2.7 Retry standards

| Operation | Attempts | Backoff |
|-----------|----------|---------|
| Pipeline start (HTTP ≠ 201) | 5 | immediate new attempt after cancel |
| Path-level E2E | 5 | full path retry |
| Approve signal | 12 | 5s |
| curl probe | fail → log body | no silent swallow |

### 2.8 Supplemental attestation

When primary E2E fails a path due to **verification defect** (SEV-3), not product defect:

1. Cancel orphan via `cancel_stale_run.sh`
2. Run isolated supplement script sourcing shared helpers
3. Record in `PASS-FAIL-MATRIX.md`: Primary / Supplement / Final
4. Archive evidence under `path-{label}/` or `path-{label}-supplement/`

Valid for closure; not valid for masking SEV-1/SEV-2 product failures.

### 2.9 Evidence bundle (required artifacts)

| Artifact | Required |
|----------|----------|
| `summary*.txt` | run_id \| episode_id \| ep_num per path |
| `e2e-olares.log` | full timestamped trace |
| `path-{X}-manifest.json` | export manifest |
| `path-{X}-export.zip` | binary export |
| `PASS-FAIL-MATRIX.md` | primary + supplement + final |
| Governance JSON | audit, history, lineage, runs (PATH E) |

---

## 3. US-V03 → US-V07 review summary

| Suite | Paths | Concurrency | Temporal cancel | Episode poll | flock | Supplement pattern |
|-------|-------|-------------|-----------------|--------------|-------|-------------------|
| US-V03 | A/B | None | Manual scripts | N/A | No | No |
| US-V04 | Engine | None | N/A | N/A | No | No |
| US-V05 | A/B/C | None | DB-only | Project-level | No | PATH C manual |
| US-V06 | A/B/C/D | None | DB-only | Project-level | No | `verify_usv06_supplement.sh` |
| US-V07 | A–E | **flock** | **terminate + idle** | **episode_id** | **Yes** | `verify_path_c1_olares.sh` |
| US-V08 | A–E | **flock** | **terminate + idle** | **episode_id** | **Yes** | `USV08_ONLY_PATH` supplement |
| US-V08B | A–F | **flock** (`.e2e-v08b.lock`) | **terminate + idle** | **episode_id** | **Yes** | `USV08B_ONLY_PATH` supplement |

**Character cleanup (US-V08B):** `cleanup_project_characters()` only after `cancel_active_runs` + idle. PATH E validates snapshot survives delete.

**Snapshot evidence (US-V08B):** E2E asserts `json_array_length(character_snapshot)` matches character count on every character path export.

**Acceptance (WP-1):** Known race conditions **documented** with mitigations in US-V07; US-V05/V06 remain **at risk** if run concurrently or without idle wait. No **new** race class identified beyond those listed.

---

## 4. verify-all gap

| Entrypoint | Covers through | Gap |
|------------|----------------|-----|
| `verify_all.ps1` | Phase 3D | Missing Phase 4/5/6 local scripts |
| `verify_all_olares.ps1` | Phase 3C + drift | Missing US-V05/06/07; drift defaults Alembic **0003** |

**Recommendation:** Extend verify-all in a future **implementation** sprint (out of Phase 6.5 scope).
