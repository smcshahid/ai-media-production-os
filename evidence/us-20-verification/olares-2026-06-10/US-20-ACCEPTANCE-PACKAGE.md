# US-20 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-11  
**Baseline:** `v0.7.0-usv02`  
**API image:** `docker.io/library/aimpos-api:us20`  
**Olares E2E:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| S-20-01 `GET /lineage/{RUN_ID}` HTTP 200 | **PASS** | `logs/us20-verify.log` |
| S-20-02 Display chain stages | **PASS** | IDEA→STORY→SCRIPT→4×STORYBOARD→VIDEO |
| S-20-03 **API vs SQL edge parity** | **PASS** | `SQL_EDGE_COUNT=18` = `API_EDGE_COUNT=18` |
| S-20-04 **Synthetic IDEA node** | **PASS** | `synthetic: true`; `parent_asset_ids: []` |
| S-20-04 **No IDEA→STORY edge** | **PASS** | IDEA asset absent from all `edges[]` pairs |
| S-20-05 STORYBOARD→VIDEO (4 edges) | **PASS** | `STORYBOARD_TO_VIDEO=4` |
| S-20-06 Unknown run → 404 | **PASS** | `UNKNOWN http=404` |
| S-20-07 **Export regression** | **PASS** | `EXPORT http=200` |
| V-20-L04 **Lineage row count unchanged** | **PASS** | `LINEAGE_EDGES_BEFORE=94` = `AFTER=94` |

**Closure recommendation:** **READY** — Olares evidence collected; governance closure review may proceed.

---

## Run attestation

| Field | Value |
|---|---|
| **PROJECT** | `76aa4418-d92d-45f7-954c-a10383ea511a` |
| **RUN_ID** | `042983f7-0f55-48c3-9d65-fce89a684625` |
| **STATUS** | `COMPLETED` (US-V02 reference run) |
| **IDEA node** | `9fac7440-034a-44f3-886f-92a4814cbd1e` (`synthetic: true`) |
| **VIDEO node** | `9888d683-376f-4feb-89b0-7574ae1dada3` |
| **Edge count (run-scoped)** | 18 |
| **Global lineage_edges** | 94 (unchanged) |

---

## Governance constraints attested

| Constraint | Olares evidence |
|---|---|
| **D-55** GET-only read API | HTTP 200 JSON; no mutation endpoints invoked |
| **D-55** API/SQL parity | S-20-03 count match |
| **D-56** list/tree data contract | 8 display nodes; metadata in response |
| **C-01** synthetic IDEA | Presentation-only; not in `edges[]` |
| **C-01** no lineage writes | V-20-L04 before/after count identical |

---

## Artifacts

| File | Description |
|---|---|
| `logs/us20-verify.log` | Full verify script output |
| `logs/lineage-response.json` | Captured `GET /lineage/{RUN_ID}` body |
| `sql/v20-l01-edges.txt` | Run-scoped edge count |
| `sql/v20-l02-stage-pairs.txt` | Stage pair breakdown |
| `sql/v20-l03-sb-video.txt` | STORYBOARD→VIDEO count to final VIDEO |
| `sql/v20-l04-no-writes-*.txt` | Global lineage row count before/after |
| `images/aimpos-api-us20.tar` | Deployed API image |

**Verify script:** `deploy/k8s/us20-verify/verify_us20.sh` via `run_remote.sh`
