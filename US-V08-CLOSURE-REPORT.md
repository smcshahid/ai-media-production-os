# US-V08 Character Bible Pilot — Closure Report

**Date:** 2026-06-18  
**Acceptance:** US-V08 **ACCEPTED**  
**Release:** `v0.17.0-phase7-character-bible`  
**Recommendation:** **RELEASE READY WITH CONDITIONS** (see [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md))

---

## Outcome

Olares authoritative acceptance completed for Character Bible Pilot (SCR-2026-005). All US-V08 paths **PASS** with PATH C1 supplemental attestation mirroring US-V07 C1 pattern.

---

## Authoritative runs

| Path | Run ID | Episode # |
|------|--------|-----------|
| A | `e2fbec9b-047a-4fde-8e0b-50a2a6290861` | 49 |
| B | `925b2faa-6d34-47de-8c24-c79dd1ea1382` | 50 |
| C1 | `885b7b2c-56b9-409d-b640-8111af7c9434` | 55 |
| C2 | `ae26081f-2783-4edd-a700-deb3d2f9c80a` | 54 |

---

## Verification summary

| Layer | Result |
|-------|--------|
| Local (`verify_phase7_local.ps1`) | FAIL=0 |
| Olares deploy (0006 + usv08-phase7) | PASS |
| Olares E2E Paths A–E | PASS (C1 supplement) |

Evidence root: `evidence/us-v08-verification/olares-2026-06-18/`

---

## Conditions for release

1. **TD-P7-01 (SEV-3):** Export manifest v5 requires character rows to exist at export time — document in migration/release notes; consider snapshot at run bind in Phase 8.
2. **Verification hygiene:** Run US-V08 E2E with flock only; use `USV08_ONLY_PATH` for supplemental paths.

---

## Lessons learned

1. Verification scripts must parse JSON with Python, not grep, for multiline manifests.
2. Pilot `cleanup_project_characters` must not run while another path's run is in flight.
3. Local Docker build + Olares `ctr` import remains the reliable deploy path (no Docker on Olares node).

---

## Phase 8 recommendation

Proceed with **character edit UX** and optional **export-time character snapshot** before expanding beyond 3-character pilot.
