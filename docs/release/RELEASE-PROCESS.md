# AIMPOS-Spark — Release Process

**Version:** 1.0 · Phase 3D  
**Authority:** Release Manager · Repository Custodian

---

## 1. Purpose

Establish repeatable release mechanics so every AIMPOS deployment traces to a semver tag, pinned container images, and a verification evidence bundle.

---

## 2. Release cadence

| Type | When | Tag pattern | Example |
|------|------|-------------|---------|
| **Platform release** | After phase closure (3A–3D) | `v0.N.0-phase3X` | `v0.13.0-phase3d` |
| **Story release** | Individual story closure | `v0.N.0-usXX` | `v0.12.0-usv03` |
| **Hotfix** | Defect on released tag | `v0.N.1-phase3X` | `v0.13.1-phase3d` |

Phase 3D introduces the **platform release** track for distribution readiness.

---

## 3. Release cut procedure

### 3.1 Pre-cut gates

- [ ] All phase work packages PASS (local + Olares verify)
- [ ] No open Severity-1 or Severity-2 defects
- [ ] API unit tests pass (`cd api && pytest tests/unit -q`)
- [ ] Web build/lint/test pass (`cd web && npm run build && npm run lint && npm test`)
- [ ] `make verify-all` → FAIL=0 (local)
- [ ] Olares `make verify-all-olares` → FAIL=0 (when cluster available)

### 3.2 Cut steps

1. **Confirm manifest** — edit `deploy/release/manifest.yaml`:
   - Set `release.version`, `release.date`
   - Set all `images.*.tag` to the new version
   - Set `release.git_commit` via `git rev-parse HEAD`

2. **Build release images** (operator workstation):

   ```powershell
   pwsh scripts/release/build-release-images.ps1
   ```

3. **Generate release notes**:

   ```powershell
   pwsh scripts/release/generate-release-notes.ps1 -Version v0.13.0-phase3d
   ```

4. **Deploy to Olares** (see `docs/release/INSTALLATION-GUIDE.md` or upgrade guide)

5. **Run verification**:

   ```powershell
   make verify-all
   make verify-all-olares
   ```

6. **Archive evidence** under `evidence/phase-3d-verification/<date>/`

7. **Update repository**:
   - `DECISIONS.md` (release D-record)
   - `README.md` status row
   - Phase mission closure document

8. **Tag and commit** (requires explicit authorization):

   ```powershell
   git tag -a v0.13.0-phase3d -m "Phase 3D release hardening"
   git push origin v0.13.0-phase3d
   ```

### 3.3 Post-cut

- Publish release notes from `docs/release/notes/`
- Register Olares Application if chart version changed
- Notify PO for operational validation sign-off

---

## 4. Image traceability

Every deployed image **must** match `deploy/release/manifest.yaml`:

| Service | Manifest key | Olares deployment |
|---------|--------------|-------------------|
| API | `images.api` | `deployment/aimpos-api` |
| Web | `images.web` | `deployment/aimpos-web` |
| Worker | `images.worker` | `deployment/aimpos-worker` |

Verify with:

```powershell
make check-drift-olares
```

---

## 5. Rollback

1. Identify previous tag in `deploy/release/manifest.yaml` git history
2. Restore manifest to prior version
3. Re-run `deploy/k8s/phase3d-verify/deploy_release.sh` with prior image tars
4. Run `make verify-all-olares`
5. Document rollback in evidence package

See `docs/runbooks/recovery.md`.

---

## 6. Related documents

| Document | Purpose |
|----------|---------|
| `deploy/release/manifest.yaml` | Version + image pins |
| `docs/release/RELEASE-CHECKLIST.md` | Operator checklist |
| `docs/release/UPGRADE-CHECKLIST.md` | Upgrade checklist |
| `docs/runbooks/installation.md` | Install runbook |
| `docs/runbooks/verification.md` | Verify runbook |
