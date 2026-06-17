# Runbook: Installation

**Release:** `v0.13.0-phase3d`  
**See also:** `docs/release/INSTALLATION-GUIDE.md`

---

## Quick reference

| Step | Command / location |
|------|-------------------|
| Build images | `make release-build` |
| Install on Olares | `deploy/olares/aimpos/install.sh` |
| Verify | `make verify-all-olares` |
| Login token | `aimpos-api-env` secret → `AIMPOS_API_TOKEN` |

---

## Operator procedure

### A. Workstation — build

```powershell
make release-build
make release-notes
```

Verify manifest: `deploy/release/manifest.yaml`

### B. Transfer to Olares

Copy chart, three image tars, deploy script, application CR (see INSTALLATION-GUIDE §2).

### C. Olares host — deploy

```bash
bash /tmp/deploy_release.sh
sudo k3s kubectl apply -f /tmp/aimpos-application.yaml
```

### D. Workstation — validate

```powershell
make verify-all-olares
make check-drift-olares
```

### E. PO sign-off

Open launcher → login → dashboard + audit + history smoke.

---

## Dependencies

Full inventory: `deploy/olares/aimpos/DEPENDENCIES.md`

Minimum running in `aimpos-mwayolares`:

- PostgreSQL (`aimpos-postgres-0`)
- MinIO, Redis, Temporal
- API + Worker deployments
- Shared Olares Ollama + ComfyUI

---

## Escalation

| Symptom | Runbook |
|---------|---------|
| Deploy fails | `recovery.md` |
| Verify FAIL | `verification.md` |
| GPU / quality issues | `comfyui-quality.md` |
