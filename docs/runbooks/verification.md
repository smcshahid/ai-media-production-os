# Runbook: Verification

**Release:** `v0.13.0-phase3d`

---

## Consolidated commands

| Target | Command | Expected |
|--------|---------|----------|
| Local full | `make verify-all` | FAIL=0 |
| Olares full | `make verify-all-olares` | FAIL=0 |
| Drift only | `make check-drift-olares` | DRIFT=0 |
| Bootstrap | `make verify-bootstrap` | FAIL=0 |
| US-V04 | `make verify-usv04` | FAIL=0 |
| Phase 3D | `make verify-phase3d` | FAIL=0 |

---

## Verify-all sequence (local)

1. `verify_bootstrap.sh` — Alembic 0003 + STORYBOARD indexes
2. `verify_usv04_local.ps1` — Flux workflow + i2v enabled
3. `verify_phase3b_local.ps1` — export, runs, history
4. `verify_phase3c_local.ps1` — pagination + 3B regression
5. `verify_phase3d_local.ps1` — manifest + alembic + worker env

Logs: `evidence/phase-3d-verification/local-<date>/logs/`

---

## Verify-all sequence (Olares)

1. `check_drift.sh` — image tags vs manifest
2. `verify_release.sh` — US-V04 SQL + API regressions
3. `run_olares_phase3c.sh` — web entrance + pagination
4. `verify_usv04.sh` — cluster attestation (when present)

Logs: `evidence/phase-3d-verification/olares-<date>/logs/`

---

## CI verification (PR gate)

On every PR:

- API: ruff, mypy, pytest (including audit tests)
- Web: build, lint, vitest
- Manifest: schema validation (`scripts/release/validate-manifest.py`)

Nightly (optional): compose verify — see `.github/workflows/verify-nightly.yml`

---

## Unit test gates (pre-PR)

```powershell
cd api; .\.venv\Scripts\python.exe -m pytest tests/unit -q
cd web; npm run build; npm run lint; npm test
```

---

## Olares remote execution

Scripts copied via SCP to `/tmp/` on Olares host, executed over SSH.

Environment variables set by runner scripts:

- `TOKEN` — from `aimpos-api-env`
- `PGPW` — from `aimpos-postgres-auth`
- `PROJECT_ID` — first project in DB

---

## Interpreting failures

| Output | Meaning |
|--------|---------|
| `FAIL=0` | Pass |
| `DRIFT=1` | Cluster images ≠ manifest |
| `SKIP postgres not running` | Start `make up-dev` for live checks |
| `WARN US-V04 slideshow fallback` | i2v failed; acceptable with evidence |

---

## Related

- `docs/release/VALIDATION-GUIDE.md`
- `deploy/release/manifest.yaml`
