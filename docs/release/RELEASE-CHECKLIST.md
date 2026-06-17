# Release Checklist — Phase 3D

Use this checklist for every platform release cut.

## Pre-release

- [ ] Phase governance brief ACCEPT
- [ ] All WPs closed with evidence
- [ ] `api/tests/unit` PASS
- [ ] `web` build + lint + vitest PASS
- [ ] CI green on `main`
- [ ] No open S1/S2 defects

## Manifest & build

- [ ] `deploy/release/manifest.yaml` updated with new version
- [ ] `release.git_commit` set to current HEAD
- [ ] `scripts/release/build-release-images.ps1` completed
- [ ] Image tags match manifest (`aimpos-api`, `aimpos-web`, `aimpos-worker`)
- [ ] `docs/release/notes/<version>.md` generated

## Local verification

- [ ] `make verify-bootstrap` PASS
- [ ] `make verify-usv04` PASS
- [ ] `make verify-phase3b` PASS
- [ ] `make verify-phase3c` PASS
- [ ] `make verify-phase3d` PASS
- [ ] `make verify-all` → FAIL=0

## Olares verification

- [ ] Images imported to cluster (`docker save` → `ctr import`)
- [ ] `deploy/k8s/phase3d-verify/deploy_release.sh` completed
- [ ] Application CR `state=running`
- [ ] `make verify-all-olares` → FAIL=0
- [ ] `make check-drift-olares` → no drift

## Documentation

- [ ] README status row updated
- [ ] DECISIONS.md release record appended
- [ ] Mission closure document written
- [ ] RELEASE-READINESS-REPORT.md written

## Release authorization (requires explicit approval)

- [ ] Git commit with release artifacts
- [ ] Annotated tag created
- [ ] Tag pushed to origin
- [ ] Evidence archived under `evidence/phase-3d-verification/`

## Post-release PO validation

- [ ] Open AIMPOS from Olares launcher
- [ ] Login with cluster token
- [ ] Dashboard + Audit + History functional
- [ ] Full pipeline smoke (optional, time-boxed)
