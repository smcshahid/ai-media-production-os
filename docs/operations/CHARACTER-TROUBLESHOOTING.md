# Character Troubleshooting Guide

**Version:** 1.0 (Phase 7.5)

---

## Symptom: Export manifest is v4 instead of v5

| Cause | Check | Fix |
|-------|-------|-----|
| Run has no `character_ids` | `SELECT character_ids FROM pipeline_runs WHERE id=…` | Expected for non-character runs |
| Legacy run, characters deleted, no snapshot | `SELECT character_snapshot FROM pipeline_runs WHERE id=…` | Re-run pipeline on Phase 7.5+ |
| Snapshot empty | Start pipeline after 0007 migration | Upgrade API + migrate |

---

## Symptom: Character delete returns 409

**Cause:** Character bound to active run (`PENDING`, `RUNNING`, `AWAITING_APPROVAL`).

**Fix:** Wait for run to complete or cancel via verification cleanup / admin cancel. Completed runs do not block delete.

---

## Symptom: Continuity drift across scenes

| Check | Action |
|-------|--------|
| Snapshot present on run | Worker reads snapshot first |
| Bible injected in activities | Inspect story/script/storyboard agent logs |
| Profile fields complete | Ensure visual_traits and personality_notes populated |

Continuity is prompt-based only — no memory/RAG layer in Phase 7.5.

---

## Symptom: Edit did not affect completed export

**Expected behavior.** Edits apply to **future** pipeline starts. Re-export of an old run uses the original snapshot.

---

## Symptom: US-V08B PATH E failure (export changed after delete)

1. Confirm Alembic **0007** applied.
2. Confirm run started **after** Phase 7.5 deploy (snapshot populated at start).
3. Compare `path-E-before-manifest.json` vs `path-E-after-manifest.json` in evidence.

---

## Symptom: E2E lock failure

```
FAIL another US-V08B E2E instance holds …/.e2e-v08b.lock
```

Terminate orphaned E2E SSH session or remove stale lock on Olares after confirming no active runner.
