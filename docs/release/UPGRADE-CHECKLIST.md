# Upgrade Checklist — AIMPOS on Olares

Use when upgrading from a prior release tag (e.g. `v0.12.0-usv03` or `:dev` images) to a pinned release.

## Pre-upgrade

- [ ] Record current cluster state: `make check-drift-olares > evidence/pre-upgrade-drift.txt`
- [ ] Export audit trail if needed: Audit page → Export JSON
- [ ] Note current image tags:

  ```bash
  sudo k3s kubectl get deploy -n aimpos-mwayolares \
    -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}'
  ```

- [ ] Confirm no active pipeline run (`GET /pipeline/status` → not RUNNING)

## Build & transfer

- [ ] Update local repo to release tag/commit
- [ ] Verify `deploy/release/manifest.yaml` matches target version
- [ ] Build images: `pwsh scripts/release/build-release-images.ps1`
- [ ] Copy to Olares:
  - Chart: `deploy/olares/aimpos/`
  - Image tars from `$env:TEMP\aimpos-release-*.tar`
  - `deploy/k8s/phase3d-verify/deploy_release.sh`

## Deploy

- [ ] Run deploy script on Olares host (see `docs/release/UPGRADE-GUIDE.md`)
- [ ] Wait for rollouts: api, web, worker, aimposingress
- [ ] Apply Application CR if manifest version changed

## Post-upgrade verification

- [ ] `make verify-all-olares` → FAIL=0
- [ ] `make check-drift-olares` → no drift
- [ ] Web entrance HTTP 200
- [ ] API proxy `/health` HTTP 200
- [ ] Audit pagination works
- [ ] History video playback works

## Rollback (if verify fails)

- [ ] Restore prior image tags via `deploy_release.sh` with old tars
- [ ] Re-run verify
- [ ] Document failure in evidence package

See `docs/runbooks/recovery.md` for detailed rollback steps.
