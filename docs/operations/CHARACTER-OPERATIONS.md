# Character Operations Guide

**Version:** 1.0 (Phase 7.5)  
**Scope:** Character Bible production operations

---

## Overview

Characters are project-scoped profiles (max **3** per project). Pipeline runs bind up to **3** character IDs at start; an immutable **snapshot** is stored on the run for export and worker continuity.

---

## Lifecycle

| Action | API | UI | Notes |
|--------|-----|-----|-------|
| Create | `POST /characters` | Character panel → Add | Blocked at 3/project |
| View | `GET /characters` | View button | Read-only detail |
| Edit | `PATCH /characters/{id}` | Edit → Save | Affects **future** runs only |
| Delete | `DELETE /characters/{id}` | Delete (confirm) | Blocked if bound to **active** run |
| Bind to run | `POST /pipeline/start` | Checkbox selection | Snapshot taken at start |

---

## Snapshot semantics

- Captured at pipeline start from live profile fields.
- Worker story/script/storyboard agents read snapshot (not live rows when snapshot exists).
- Export manifest v5 uses snapshot; re-export after character delete remains identical.

---

## Pre-flight checklist (Olares / production)

1. Alembic head **0007** (`character_snapshot` column present).
2. No concurrent E2E on same project (`flock` on `$EVID/.e2e-v08b.lock`).
3. Cancel active runs before character seed/cleanup scripts.
4. Verify `character_snapshot` non-null on completed character runs:

```sql
SELECT id, json_array_length(character_snapshot::json)
FROM pipeline_runs
WHERE character_ids IS NOT NULL AND status = 'COMPLETED'
ORDER BY updated_at DESC LIMIT 5;
```

---

## Verification scripts

| Script | Purpose |
|--------|---------|
| `deploy/dev/verify_usv08b_local.ps1` | Local pytest/vitest gate |
| `deploy/dev/verify_usv08b_olares.ps1` | Deploy + US-V08B PATH A–F |
| `deploy/k8s/usv08b-verify/verify_usv08b_e2e.sh` | Olares path runner |

Supplemental path re-run: `USV08B_ONLY_PATH=A|B|C1|C2|D|E|F`.

---

## Character cleanup standard

Verification scripts use `cleanup_project_characters()` **only** after `cancel_active_runs` and `wait_for_project_idle`. Never delete characters while a run referencing them is active.
