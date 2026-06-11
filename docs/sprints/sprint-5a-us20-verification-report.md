# Sprint 5A — US-20 Olares Verification Report

**Date:** 2026-06-11  
**Story:** US-20 Lineage Viewer  
**Environment:** Olares `olares@10.0.0.34`, namespace `aimpos-mwayolares`  
**API image:** `docker.io/library/aimpos-api:us20` (deployed from local build)  
**Reference run:** US-V02 COMPLETED — `042983f7-0f55-48c3-9d65-fce89a684625`  
**Result:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## 1. Deploy

| Step | Result |
|---|---|
| Build `aimpos-api:us20` (local Docker) | ✅ |
| `docker save` → `/tmp/aimpos-api-us20.tar` | ✅ (~164 MB) |
| `deploy_us20.sh` import + rollout | ✅ |
| Prior image | `aimpos-api:us19` |

---

## 2. Verification steps

| Step | Action | Pass criteria | Result |
|---|---|---|---|
| S-20-01 | `GET /lineage/{RUN_ID}` | HTTP 200; JSON parse | **PASS** |
| S-20-02 | Display chain stages | IDEA (synthetic), STORY, SCRIPT, ≥4 STORYBOARD, VIDEO | **PASS** — 8 nodes |
| S-20-03 | **API vs SQL edge parity** | `len(edges)` == SQL COUNT | **PASS** — 18 = 18 |
| S-20-04 | **Synthetic IDEA** | `synthetic=true`; no IDEA in `edges[]` | **PASS** |
| S-20-05 | STORYBOARD→VIDEO | 4 edges to final VIDEO | **PASS** |
| S-20-06 | Unknown run | HTTP 404 | **PASS** |
| S-20-07 | **Export regression** | `GET /export/{RUN_ID}` HTTP 200 | **PASS** |
| V-20-L04 | **No lineage writes** | `COUNT(*)` from `lineage_edges` unchanged | **PASS** — 94 = 94 |

---

## 3. Key attestation details

### API vs SQL parity (S-20-03)

```
SQL_EDGE_COUNT=18
API_EDGE_COUNT=18
```

Run-scoped query (§1.5 implementation plan): both endpoints same `project_id`; either endpoint references `pipeline_run_id`.

### Synthetic IDEA (S-20-04)

From `logs/lineage-response.json`:

- IDEA node: `9fac7440-034a-44f3-886f-92a4814cbd1e`
- `"synthetic": true`
- `"parent_asset_ids": []`
- IDEA asset ID **not present** in any `edges[]` pair (no IDEA→STORY edge)

### C-01 lineage immutability (V-20-L04)

```
LINEAGE_EDGES_BEFORE=94
LINEAGE_EDGES_AFTER=94
```

Verify is read-path only — no INSERT/UPDATE/DELETE on `lineage_edges`.

### Export regression (S-20-07)

```
EXPORT http=200
```

D-52..D-54 export contract unchanged after lineage deploy.

---

## 4. SQL attestation

| ID | File | Value |
|---|---|---|
| V-20-L01 | `sql/v20-l01-edges.txt` | 18 |
| V-20-L02 | `sql/v20-l02-stage-pairs.txt` | STORY→SCRIPT:2; SCRIPT→STORYBOARD:8; STORYBOARD→VIDEO:8 |
| V-20-L03 | `sql/v20-l03-sb-video.txt` | 4 (to final VIDEO v2) |
| V-20-L04 | `sql/v20-l04-no-writes-*.txt` | 94 before / 94 after |

---

## 5. Evidence location

`evidence/us-20-verification/olares-2026-06-10/`

**Primary log:** `logs/us20-verify.log`

---

## 6. Closure status

| Gate | Status |
|---|---|
| Local tests | **PASS** (94 API / 26 web) |
| Olares verify | **PASS** |
| Commit / tag / push | **Not performed** (per governance instruction) |
| Governance closure review | **READY TO SUBMIT** |
