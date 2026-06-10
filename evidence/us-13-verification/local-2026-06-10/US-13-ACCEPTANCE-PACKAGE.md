# US-13 Acceptance Package — Local Verification

**Environment:** Local dev (unit tests + web build)  
**Date:** 2026-06-10  
**Baseline:** Post-implementation (pre-Olares E2E)  
**Recommendation:** **CONDITIONAL ACCEPT** — AC-2 fully evidenced via unit tests; AC-1/3/4 require Olares E2E or local stack run for UI/Temporal evidence.

---

## Acceptance criteria status

| AC | Description | Status | Evidence |
|---|---|---|---|
| AC-1 | Review screen shows editable treatment | **PARTIAL** | API: `test_get_asset_content_returns_story_bytes`. UI: implementation complete; screenshot pending stack run. |
| AC-2 | Save creates human-edit version | **PASS** | See §AC-2 evidence below |
| AC-3 | Approve advances pipeline | **PARTIAL** | `test_pipeline_approve.py` regression; E2E stage transition pending Olares |
| AC-4 | Reject enables regenerate (affordance) | **PARTIAL** | Reject API regression + UI affordance implemented; network log / screenshot pending |

---

## AC-2 evidence (governance-required fields)

**Test:** `api/tests/unit/test_assets_us13.py`

### `test_put_asset_creates_human_edit_version`

| Field | Expected | Observed |
|---|---|---|
| New human-edit version created | Yes | `PUT` returns 200 with new `id`, `version=2` |
| Version incremented | 1 → 2 | `body["version"] == 2` |
| `branch` | `human-edit` | `body["branch"] == "human-edit"` |
| `is_ai_generated` | `false` | `body["is_ai_generated"] is False` |
| Content stored | Edited text in MinIO | `GET .../content` returns edited body |

### `test_put_asset_does_not_change_pipeline_status`

| Field | Expected | Observed |
|---|---|---|
| Pipeline `status` unchanged | `AWAITING_APPROVAL` | `status_body["status"] == "AWAITING_APPROVAL"` |
| `current_stage` unchanged | `STORY` | `status_body["current_stage"] == "STORY"` |

Log reference: `logs/pytest-us13.txt`

---

## AC-1 API evidence

```
test_get_asset_content_returns_story_bytes PASSED
- GET /assets/{id}/content returns 200
- Content-Type includes text/markdown
- Body equals seeded story.md bytes
```

---

## AC-3 / AC-4 regression evidence

```
test_pipeline_approve.py — approve/reject contract unchanged (US-08)
Full API unit suite: 72 passed
```

---

## Constraint verification

| Check | Result |
|---|---|
| No `POST /pipeline/regenerate` in codebase | PASS (grep: no route added) |
| No worker/temporal/workflow file changes | PASS |
| No Alembic migration | PASS |
| No branch promotion on approve | PASS (`D-37`) |

---

## CI-equivalent gates

| Gate | Result |
|---|---|
| `pytest tests/unit/` | 72 passed |
| `npm test` | 13 passed |
| `npm run build` | PASS |
| `ruff check app/routes/assets.py` | PASS |

---

## Olares E2E checklist (for full ACCEPT)

- [ ] `POST /ideas` → `POST /pipeline/start` → `AWAITING_APPROVAL`/`STORY`
- [ ] Review UI screenshot with editable treatment (AC-1)
- [ ] Save → SQL `asset_versions` human-edit row (AC-2 — corroborate unit evidence)
- [ ] Reject with note → stage held + UI affordance (AC-4)
- [ ] Approve → `current_stage=SCRIPT` + Temporal history (AC-3)

---

## Closure recommendation

**CONDITIONAL ACCEPT** for development sign-off on implementation correctness.  
**Full ACCEPT** pending Olares E2E evidence package (mirror US-12 `olares-2026-06-10` format).
