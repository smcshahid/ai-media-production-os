# Runbook: Upgrade

**Release:** `v0.13.0-phase3d`  
**See also:** `docs/release/UPGRADE-GUIDE.md`, `docs/release/UPGRADE-CHECKLIST.md`

---

## When to use

- Moving from `:dev` or `:phase3c` to pinned release
- Applying a hotfix tag (e.g. `v0.13.1-phase3d`)
- Refreshing cluster after local code changes

---

## Pre-upgrade

```powershell
# Record drift baseline
make check-drift-olares | Tee-Object evidence/pre-upgrade-drift.txt

# Confirm pipeline idle
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/pipeline/status?project_id=$PROJECT_ID"
```

---

## Upgrade steps

1. Update repo / manifest to target version
2. `make release-build`
3. SCP tars + chart + `deploy_release.sh` to Olares
4. Run deploy on Olares host
5. Apply Application CR if version changed
6. `make verify-all-olares`
7. `make check-drift-olares`

---

## Zero-downtime notes

- API/web rollouts use k8s rolling update (~1–3 min)
- Active WebSocket connections may drop; dashboard falls back to polling (D-59)
- Do not upgrade during active GPU generation if avoidable

---

## Rollback trigger

Rollback if:

- `verify-all-olares` FAIL ≠ 0 after retry
- `check-drift-olares` shows unexpected tags post-deploy
- Web entrance returns non-200

Procedure: `docs/runbooks/recovery.md`
