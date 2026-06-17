# AIMPOS Olares Web Deployment (Phase 3C / 3D)

Deploy the AIMPOS web SPA as a first-class Olares application entrance alongside the existing `aimpos-mwayolares` backend stack.

**Release:** `v0.13.0-phase3d` — see `deploy/release/manifest.yaml` for pinned images.

## Architecture

```
Olares Desktop → aimposingress:8080 → aimpos-web:80 → aimpos-api:8000 (nginx proxy)
```

- Web image built with `VITE_API_URL=""` (same-origin API via nginx reverse proxy).
- `OlaresManifest.yaml` declares the `aimpos` entrance for Olares Studio / Market install.
- Backend (API, worker, postgres, minio, redis, temporal) remains in `aimpos-mwayolares` from M1-DV / story verify deploys.

## Quick install (Phase 3D)

From operator workstation:

```powershell
make release-build
# Transfer chart + tars — see docs/release/INSTALLATION-GUIDE.md
```

On Olares host:

```bash
AIMPOS_RELEASE=v0.13.0-phase3d bash /tmp/aimpos-olares-chart/install.sh
```

Verify:

```powershell
make verify-all-olares
make check-drift-olares
```

## Build web image (operator workstation)

```powershell
cd <repo-root>
docker build -f web/Dockerfile `
  --build-arg VITE_API_URL= `
  -t aimpos-web:v0.13.0-phase3d .
docker save aimpos-web:v0.13.0-phase3d -o $env:TEMP\aimpos-web-v0.13.0-phase3d.tar
```

Or use `make release-build` for API + web + worker.

## Deploy full release (API + web + worker)

```powershell
pwsh scripts/release/build-release-images.ps1
scp deploy/k8s/phase3d-verify/deploy_release.sh olares@10.0.0.34:/tmp/
# SCP all three tars + chart
ssh olares@10.0.0.34 "bash /tmp/deploy_release.sh"
```

See `docs/release/INSTALLATION-GUIDE.md` for complete procedure.

## Verify

```powershell
make verify-all-olares
make check-drift-olares
```

## Dependencies

See `DEPENDENCIES.md` in this directory.

## Related documents

| Document | Purpose |
|----------|---------|
| `docs/release/INSTALLATION-GUIDE.md` | Fresh install |
| `docs/release/UPGRADE-GUIDE.md` | Upgrade from prior tags |
| `docs/runbooks/olares-operations.md` | Daily ops |
| `docs/runbooks/recovery.md` | Rollback |

## Acceptance

- AIMPOS opens from Olares launcher (no `npm run dev`, no API port-forward).
- Login with token from `aimpos-api-env` secret.
- Full pipeline workflow functional (API + worker on cluster).
- Images match `deploy/release/manifest.yaml` (no drift).
