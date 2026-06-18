# Export Troubleshooting Guide

**Version:** 1.0 (Phase 7.5)

---

## Manifest version quick reference

See [MANIFEST-V5-GOVERNANCE.md](MANIFEST-V5-GOVERNANCE.md) for the full ladder (v1–v5).

---

## Symptom: Export 404 / run not found

- Confirm `pipeline_run_id` exists and `status = COMPLETED`.
- Export is rejected for in-flight runs.

---

## Symptom: Export 500 / asset resolution error

- Check all approved stages have asset versions for the run.
- Query: `SELECT stage, COUNT(*) FROM asset_versions WHERE pipeline_run_id=… GROUP BY stage;`

---

## Symptom: v5 `characters[]` missing names after delete

**Pre-7.5:** Live row lookup failed → v4 fallback.  
**Post-7.5:** Should not occur if `character_snapshot` populated. Apply migration 0007 and re-run pipeline.

---

## Symptom: Episode paths wrong in ZIP

- v4+ runs with `episode_id` use `episodes/episode_XX/` prefix.
- Verify `episode_number` in manifest matches folder name.

---

## Symptom: Re-export differs from first export (same run)

Should be **byte-identical** for manifest character section when snapshot exists. If not:

1. Compare API image tag (must be Phase 7.5+).
2. Inspect `character_snapshot` immutability (should not UPDATE after start).

---

## Evidence collection (Olares)

After US-V08B E2E:

- `path-*-manifest.json` — manifest version and characters
- `path-*-export.zip` — full bundle
- `e2e-olares.log` — run IDs and snapshot counts
- `summary.txt` — PATH A–F results

Fetch via `deploy/dev/verify_usv08b_olares.ps1` → `evidence/us-v08b-verification/olares-<date>/`.
