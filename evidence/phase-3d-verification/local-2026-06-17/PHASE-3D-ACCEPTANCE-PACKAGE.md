# Phase 3D — Local acceptance package

**Date:** 2026-06-17  
**Release:** `v0.13.0-phase3d`  
**Result:** **PASS** (local gates)

## Verification

```
make verify-phase3d           FAIL=0 (manifest gates; live checks when Docker up)
scripts/release/validate-manifest.py   PASS
api/tests/unit                114 passed
web vitest                    43 passed
```

## Work packages

| WP | Status | Evidence |
|----|--------|----------|
| WP-1 Release Engineering | **PASS** | `docs/release/`, `deploy/release/manifest.yaml` |
| WP-2 Olares Distribution | **PASS** | `deploy/olares/aimpos/install.sh`, guides |
| WP-3 Deployment Reliability | **PASS** | `deploy/k8s/phase3d-verify/check_drift.sh` |
| WP-4 Verification Automation | **PASS** | `make verify-all` |
| WP-5 US-V04 Attestation | **PASS** | `evidence/us-v04-verification/phase3d-2026-06-17/` |
| WP-6 Operational Runbooks | **PASS** | `docs/runbooks/*.md` |

## Key paths

- `deploy/release/manifest.yaml` — version + image pins
- `deploy/dev/verify_all.ps1` — consolidated local verify
- `deploy/k8s/phase3d-verify/` — Olares deploy + drift + release verify
- `docs/release/INSTALLATION-GUIDE.md`

## Olares verification

Run when cluster available:

```
make verify-all-olares
make check-drift-olares
```

Logs: `evidence/phase-3d-verification/olares-2026-06-17/logs/`
