# Runbook: Olares Operations

**Release:** `v0.13.0-phase3d`  
**Namespace:** `aimpos-mwayolares`  
**Host:** `olares@10.0.0.34` (default)

---

## Daily operations

| Task | Command |
|------|---------|
| Check app state | `sudo k3s kubectl get applications.app.bytetrade.io aimpos-mwayolares-aimpos` |
| Pod status | `sudo k3s kubectl get pods -n aimpos-mwayolares` |
| API logs | `sudo k3s kubectl logs -n aimpos-mwayolares deploy/aimpos-api -f --tail=100` |
| Worker logs | `sudo k3s kubectl logs -n aimpos-mwayolares deploy/aimpos-worker -f --tail=100` |
| Web logs | `sudo k3s kubectl logs -n aimpos-mwayolares deploy/aimpos-web --tail=50` |
| Drift check | `make check-drift-olares` (from workstation) |

---

## Image management

**Never use `:dev` or `:phase3c` in production.**

Pinned tags from `deploy/release/manifest.yaml`:

```
aimpos-api:v0.13.0-phase3d
aimpos-web:v0.13.0-phase3d
aimpos-worker:v0.13.0-phase3d
```

Deploy/update:

```powershell
make release-build
# SCP tars → Olares → deploy_release.sh
```

Import manually:

```bash
sudo ctr -a /run/containerd/containerd.sock -n k8s.io images import /tmp/aimpos-api-v0.13.0-phase3d.tar
```

---

## Secrets

| Secret | Purpose | Access |
|--------|---------|--------|
| `aimpos-api-env` | API token + config | Web login |
| `aimpos-postgres-auth` | DB password | Verify scripts |

Decode API token:

```bash
sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares \
  -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d; echo
```

---

## Shared AI services

Worker on cluster uses Olares shared services (not in-compose GPU):

- Ollama: story/script generation
- ComfyUI: Flux stills + WAN i2v

Local dev uses SSH tunnels (`scripts/dev/ensure-olares-ai-tunnels.ps1`).

GPU rule (D-08): never run Ollama and ComfyUI concurrently on single GPU.

---

## Application CR / launcher

```bash
sudo k3s kubectl apply -f deploy/olares/aimpos/templates/application.yaml
sudo k3s kubectl get applications.app.bytetrade.io aimpos-mwayolares-aimpos -o yaml
```

If launcher tile missing: refresh Olares desktop; confirm `status.state=running`.

---

## Verification schedule

| When | Action |
|------|--------|
| After every deploy | `make verify-all-olares` |
| Weekly | `make check-drift-olares` |
| Before release tag | `make verify-all` + evidence archive |

---

## Related runbooks

| Topic | Document |
|-------|----------|
| Install | `installation.md` |
| Upgrade | `upgrade.md` |
| Recovery | `recovery.md` |
| ComfyUI quality | `comfyui-quality.md` |
| Local dev | `local-development.md` |
