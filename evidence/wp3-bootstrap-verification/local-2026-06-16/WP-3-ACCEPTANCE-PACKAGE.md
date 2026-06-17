# WP-3 — Bootstrap acceptance package

**Date:** 2026-06-16  
**Result:** **PASS**

## Command

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/ensure-db-migrated.ps1
```

## Output (summary)

```
Database at Alembic revision: 0003
Migration validation OK.
```

## Index attestation

```
uq_asset_versions_project_stage_version_single
uq_asset_versions_storyboard_batch_frame
```

## Integration

`make up-dev` now invokes this gate automatically before starting worker/api/web.
