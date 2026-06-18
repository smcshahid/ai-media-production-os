# Release Readiness Recommendation — v0.17.1-phase7-character-hardening

**Date:** 2026-06-18  
**Status:** **RELEASE CUT — GO**  
**Governance:** Phase 7.5 release closure **AUTHORIZED**

---

## Recommendation

**GO** — `v0.17.1-phase7-character-hardening` released.

US-V08B **ACCEPTED**. Olares PATH A–F **PASS** (D/E supplemental). Local gate **PASS**. TD-P7-01 **CLOSED**.

---

## Gates (final)

| Gate | Status |
|------|--------|
| US-V08B Olares PATH A–F | **PASS** |
| Local pytest/vitest | **PASS** |
| TD-P7-01 snapshot | **CLOSED** |
| SEV-1 / SEV-2 open | **NONE** |
| Governance stop conditions | **NOT triggered** |

---

## Release contents

- Alembic **0007** (`character_snapshot`)
- Character CRUD UX + governed DELETE + PATCH fix
- Export/worker snapshot-first continuity
- Manifest v5 governance + operational runbooks
- US-V08B verification suite

---

## Migration

```bash
alembic upgrade head   # → 0007
```

Olares: `deploy/k8s/usv08b-verify/apply_0007_sql_olares.sh`

---

## Evidence

| Package | Path |
|---------|------|
| Olares US-V08B | `evidence/us-v08b-verification/olares-2026-06-18/` |
| Local verify | `evidence/us-v08b-verification/local-2026-06-18/` |
| Release evidence | `evidence/release-v0.17.1-phase7-character-hardening/` |

---

## Rollback

Revert to `v0.17.0-phase7-character-bible`. Nullable `character_snapshot` safe to retain.

---

## Platform maturity

**3.7/5** — Character Bible production-ready; export reproducibility; operational runbooks complete.

---

## Next phase

Phase 8 platform consolidation — verify_all extension, verification library, drift Alembic alignment. No new creator-domain SCR without governance approval.
