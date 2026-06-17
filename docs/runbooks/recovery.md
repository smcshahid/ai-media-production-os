# Runbook: Recovery

**Release:** `v0.13.0-phase3d`

---

## Image rollback

### Symptom

Verify fails after deploy; wrong images on cluster; drift detected.

### Procedure

1. Identify prior working tag (git tag or manifest history)

2. Build or locate prior image tars

3. On Olares:

   ```bash
   export AIMPOS_API_IMAGE=docker.io/library/aimpos-api:<prior-tag>
   export AIMPOS_WEB_IMAGE=docker.io/library/aimpos-web:<prior-tag>
   export AIMPOS_WORKER_IMAGE=docker.io/library/aimpos-worker:<prior-tag>
   export API_TAR=/tmp/aimpos-api-<prior-tag>.tar
   export WEB_TAR=/tmp/aimpos-web-<prior-tag>.tar
   export WORKER_TAR=/tmp/aimpos-worker-<prior-tag>.tar
   bash /tmp/deploy_release.sh
   ```

4. Verify: `make verify-all-olares`

---

## API pod crash loop

```bash
sudo k3s kubectl logs -n aimpos-mwayolares deploy/aimpos-api --tail=100
sudo k3s kubectl describe pod -n aimpos-mwayolares -l app=aimpos-api
```

Common causes:

- Database unreachable → check postgres pod
- Bad env secret → compare `aimpos-api-env`
- Migration not applied → `make verify-bootstrap`

---

## Web entrance 502

```bash
sudo k3s kubectl get pods -n aimpos-mwayolares -l app=aimpos-web
sudo k3s kubectl logs -n aimpos-mwayolares deploy/aimpos-web --tail=50
curl -s http://<aimposingress-cluster-ip>:8080/health
```

- Confirm API service reachable from web nginx
- Rebuild web with `VITE_API_URL=` (same-origin)

---

## Worker / pipeline stuck

```bash
sudo k3s kubectl logs -n aimpos-mwayolares deploy/aimpos-worker --tail=200
```

- Check Temporal UI (port 8080 on dev stack)
- Cancel stale run via existing verify scripts (`deploy/k8s/us16-verify/cancel_stale_run.sh`)
- GPU OOM → see `comfyui-quality.md` fallback path

---

## Database recovery

**Do not** manually edit `pipeline_runs` during attestation.

For migration issues:

```powershell
make migrate
make verify-bootstrap
```

Alembic head must be `0003`.

---

## Audit / evidence

After any recovery action, re-run:

```powershell
make verify-all
make verify-all-olares
```

Document incident in evidence package defect register.

---

## Escalation

| Severity | Response |
|----------|----------|
| S1 — data corruption | Stop operations; restore DB from backup |
| S2 — verify FAIL | Rollback images; re-verify |
| S3 — transient | Retry verify once |
