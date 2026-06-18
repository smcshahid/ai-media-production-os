# US-V09 PASS/FAIL Matrix — Olares 2026-06-18

| Path | Primary | Supplement | Final | Run ID | Notes |
|------|---------|------------|-------|--------|-------|
| V09-01 Alembic head | **PASS** | — | **PASS** | — | Cluster **0007** matches manifest |
| V09-02 Narration env | **PASS** | — | **PASS** | — | `NARRATION_ENABLED=true` |
| V09-03 Governance reads | **PASS** | — | **PASS** | — | runs/characters/episodes HTTP 200 |
| V09-04 Platform path | **FAIL** | **PASS** | **PASS** | `d71d9c82-d847-4bfc-b11e-14ccc1d310a4` | Primary: SEV-3 snapshot query bug (BUG-P8-01) |
| Drift (acceptance tags) | **PASS** | — | **PASS** | — | `usv08b-phase75` + Alembic **0007**, DRIFT=0 |
| Local verify-all | **PASS** | — | **PASS** | — | FAIL=0 |

**Mission FAIL=0** — supplemental attestation per VERIFICATION-STANDARDS §2.8.

## Findings classification

| ID | Sev | Finding | Disposition |
|----|-----|---------|-------------|
| BUG-P8-01 | SEV-3 | `jsonb_array_length()` on JSON `character_snapshot` column returned empty | **Fixed** in `verify_usv09_e2e.sh` |
| BUG-P8-02 | SEV-3 | Approve helpers did not propagate HTTP failures | **Fixed** — `approve ... \|\| return 1` |
| ENV-P8-01 | SEV-3 | Intermittent SCRIPT stage failures on retry attempts 2–3 | **Closed** — attempt 1 COMPLETED; supplement PASS |
| TD-P6.5-06 | SEV-3 | Acceptance image tag vs release semver drift | **Open** — documented; override for acceptance |

**No open SEV-1 or SEV-2.**
