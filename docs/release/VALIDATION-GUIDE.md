# Validation Guide — AIMPOS Release

**Release:** `v0.13.0-phase3d`

---

## Automated validation (required)

### Local (developer workstation)

Prerequisites: `make up-dev` running, `.env` with `AIMPOS_API_TOKEN`.

```powershell
make verify-all
```

Expected output: `verify-all DONE FAIL=0`

Individual phases (for debugging):

| Command | Scope |
|---------|-------|
| `make verify-bootstrap` | Alembic 0003 + indexes |
| `make verify-usv04` | Flux + WAN worker env |
| `make verify-phase3b` | Audit export, run history |
| `make verify-phase3c` | Audit pagination |
| `make verify-phase3d` | Manifest + regressions |

### Olares cluster

Prerequisites: SSH to Olares, backend stack running, release images deployed.

```powershell
make verify-all-olares
make check-drift-olares
```

Expected: FAIL=0, DRIFT=0

Logs archived to: `evidence/phase-3d-verification/<date>/logs/`

---

## Manual validation checklist

### Web entrance

- [ ] Olares launcher opens AIMPOS (no port-forward)
- [ ] Login with cluster token succeeds
- [ ] Dashboard shows pipeline stepper

### Observability

- [ ] Audit page loads; pagination Previous/Next works
- [ ] Audit Export CSV + JSON download
- [ ] History page shows 5 stages
- [ ] Story/Script Compare versions works
- [ ] Video inline playback in History

### API smoke (with token)

```powershell
$token = (Select-String .env 'AIMPOS_API_TOKEN=(.+)').Matches[0].Groups[1].Value
$h = @{ Authorization = "Bearer $token" }
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod "http://localhost:8000/pipeline/runs?project_id=<id>" -Headers $h
```

### US-V04 production engine

Worker env must show:

- `COMFYUI_WORKFLOW=flux_storyboard.json`
- `VIDEO_I2V_ENABLED=true`

Latest VIDEO asset metadata:

- `source=comfyui_i2v` (preferred) or `source=slideshow` with `fallback_reason`

---

## Release verification bundle

After successful verify, create acceptance package:

```
evidence/phase-3d-verification/local-<date>/
  PHASE-3D-ACCEPTANCE-PACKAGE.md
  logs/
    bootstrap.log
    usv04.log
    phase3b.log
    phase3c.log
    phase3d.log
```

Olares:

```
evidence/phase-3d-verification/olares-<date>/
  logs/
    drift.log
    release.log
    phase3c.log
    usv04.log
```

---

## Failure protocol

| Severity | Action |
|----------|--------|
| S1 — data loss, auth bypass | Block release; fix + full re-verify |
| S2 — verify script FAIL | Block release; fix + affected phase re-run |
| S3 — flaky timing | Retry once; document in evidence |
| Drift detected | Re-deploy from manifest; re-run check |

---

## Related

- `docs/runbooks/verification.md`
- `docs/release/RELEASE-CHECKLIST.md`
