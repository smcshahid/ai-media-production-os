# Installation Guide — AIMPOS on Olares

**Release:** `v0.13.0-phase3d`  
**Audience:** Operators installing AIMPOS for the first time

---

## Overview

AIMPOS deploys to Olares in two layers:

1. **Backend stack** — API, worker, PostgreSQL, MinIO, Redis, Temporal (from M1-DV / prior story deploys)
2. **Web entrance** — SPA + nginx ingress + Olares Application CR (Phase 3C/3D chart)

This guide covers a **fresh install** of the web entrance and **pinned release images** for API/worker.

---

## Prerequisites

- Olares node with GPU access (24 GB VRAM recommended)
- SSH access: `olares@<host>` (default `10.0.0.34`)
- Backend namespace `aimpos-mwayolares` with postgres, minio, redis, temporal running
- Shared Olares Ollama + ComfyUI provisioned (see `docs/runbooks/comfyui-quality.md`)
- Operator workstation: Docker, repo clone, `.env` configured

---

## Step 1 — Build release images (workstation)

```powershell
cd <repo-root>
make release-build
# Output: $env:TEMP\aimpos-release-v0.13.0-phase3d\*.tar
```

---

## Step 2 — Transfer artifacts to Olares

```powershell
$RELEASE = "v0.13.0-phase3d"
$OUT = "$env:TEMP\aimpos-release-$RELEASE"

scp -r deploy/olares/aimpos olares@10.0.0.34:/tmp/aimpos-olares-chart
scp "$OUT\aimpos-api-$RELEASE.tar" olares@10.0.0.34:/tmp/
scp "$OUT\aimpos-web-$RELEASE.tar" olares@10.0.0.34:/tmp/
scp "$OUT\aimpos-worker-$RELEASE.tar" olares@10.0.0.34:/tmp/
scp deploy/k8s/phase3d-verify/deploy_release.sh olares@10.0.0.34:/tmp/
scp deploy/olares/aimpos/templates/application.yaml olares@10.0.0.34:/tmp/aimpos-application.yaml
```

---

## Step 3 — Install on Olares host

```bash
export AIMPOS_RELEASE=v0.13.0-phase3d
export API_TAR=/tmp/aimpos-api-v0.13.0-phase3d.tar
export WEB_TAR=/tmp/aimpos-web-v0.13.0-phase3d.tar
export WORKER_TAR=/tmp/aimpos-worker-v0.13.0-phase3d.tar
export CHART_DIR=/tmp/aimpos-olares-chart
chmod +x /tmp/deploy_release.sh
bash /tmp/deploy_release.sh
```

Or use the guided script:

```bash
chmod +x /tmp/aimpos-olares-chart/install.sh
AIMPOS_RELEASE=v0.13.0-phase3d bash /tmp/aimpos-olares-chart/install.sh
```

---

## Step 4 — Register Olares Application

```bash
sudo k3s kubectl apply -f /tmp/aimpos-application.yaml
sudo k3s kubectl get applications.app.bytetrade.io aimpos-mwayolares-aimpos -o jsonpath='{.status.state}'
# Expected: running
```

Refresh Olares desktop if launcher tile does not appear immediately.

---

## Step 5 — Validate

From operator workstation:

```powershell
make verify-all-olares
make check-drift-olares
```

See `docs/release/VALIDATION-GUIDE.md` for manual checks.

---

## Step 6 — First login

1. Open **AIMPOS Spark** from Olares launcher
2. Sign in with token from cluster secret:

   ```bash
   sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares \
     -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d
   ```

3. Confirm Dashboard, Audit, History pages load

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| Web 502 | Check `aimpos-api` pod running; verify nginx proxy in web container |
| Login 401 | Confirm token matches `aimpos-api-env` secret |
| Pipeline fails at STORYBOARD | Verify ComfyUI tunnel / shared service; see `comfyui-quality.md` |
| Drift detected | Re-run `deploy_release.sh` with correct tars |

See `docs/runbooks/recovery.md` for rollback.

---

## Related documents

- `deploy/olares/aimpos/DEPENDENCIES.md` — full dependency inventory
- `docs/runbooks/installation.md` — operator runbook
- `docs/release/UPGRADE-GUIDE.md` — upgrading from prior versions
