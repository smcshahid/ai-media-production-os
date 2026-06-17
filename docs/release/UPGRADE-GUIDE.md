# Upgrade Guide — AIMPOS on Olares

**Release:** `v0.13.0-phase3d`  
**From:** `:dev`, `:phase3c`, or prior semver tags

---

## Before you upgrade

1. Complete `docs/release/UPGRADE-CHECKLIST.md`
2. Ensure no pipeline run is `RUNNING` or `AWAITING_APPROVAL` with pending actions
3. Export audit trail if needed (Audit → Export JSON)

---

## Upgrade procedure

### 1. Record baseline

```powershell
make check-drift-olares | Tee-Object evidence/pre-upgrade-drift.txt
```

### 2. Build new release images

```powershell
git pull   # or checkout release tag when available
make release-build
```

Confirm `deploy/release/manifest.yaml` shows target version.

### 3. Deploy pinned images

Same as fresh install — transfer tars and run:

```bash
export AIMPOS_RELEASE=v0.13.0-phase3d
export API_TAR=/tmp/aimpos-api-v0.13.0-phase3d.tar
export WEB_TAR=/tmp/aimpos-web-v0.13.0-phase3d.tar
export WORKER_TAR=/tmp/aimpos-worker-v0.13.0-phase3d.tar
export CHART_DIR=/tmp/aimpos-olares-chart
bash /tmp/deploy_release.sh
```

### 4. Update Application CR (if manifest version changed)

```bash
sudo k3s kubectl apply -f /tmp/aimpos-application.yaml
```

### 5. Verify

```powershell
make verify-all-olares
make check-drift-olares
```

Expected: FAIL=0, no drift.

---

## What changes in v0.13.0-phase3d

| Area | Change |
|------|--------|
| Images | Pinned `v0.13.0-phase3d` (replaces `:dev` / `:phase3c`) |
| Manifest | `deploy/release/manifest.yaml` source of truth |
| Verify | `make verify-all` consolidated entrypoint |
| Docs | Installation, upgrade, recovery runbooks |
| Olares chart | Chart `0.13.0`, manifest `0.13.0` |

No database migration required (Alembic head remains `0003`).  
No workflow or API contract changes.

---

## Rollback

If verification fails after upgrade:

1. Restore prior image tars (or rebuild from prior git tag)
2. Set `AIMPOS_*_IMAGE` env vars to prior tags
3. Re-run `deploy_release.sh`
4. Verify with `make verify-all-olares`

See `docs/runbooks/recovery.md`.

---

## Related

- `docs/release/RELEASE-PROCESS.md`
- `docs/release/UPGRADE-CHECKLIST.md`
