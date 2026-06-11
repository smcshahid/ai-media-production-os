# US-17 Acceptance Package — Olares Verification

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-11  
**API image:** `docker.io/library/aimpos-api:us17`  
**Worker image:** `docker.io/library/aimpos-worker:us17`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Run:** `806b671a-29fe-4b62-8229-d57009a0792e`  
**Verify log:** `logs/us17-e2e.log`  
**Implementation report:** `docs/sprints/sprint-3h-us17-implementation-report.md`

---

## Verification summary

| Check | Result |
|---|---|
| V-01 — 4 frames at batch v2 (D-45) | **PASS** |
| V-02 — STORYBOARD PNG content-read (HTTP 200) | **PASS** |
| V-03 — Reject + regen → v3; prior v2 batch preserved (AC-4, D-47) | **PASS** |
| V-04 — Approve batch → `COMPLETED` (AC-3, D-46) | **PASS** |
| V-05 — Batch approvals audit (1 REJECTED + 1 APPROVED) | **PASS** |

**Closure recommendation:** **ACCEPT** (pending governance review)

---

## Test gates before deployment

| Suite | Result |
|---|---|
| API unit | **81 passed** |
| Worker unit | **36 passed** |
| Web unit | **23 passed** |

Local logs: `evidence/us-17-verification/local-2026-06-11/logs/`

---

## E2E flow (single run)

```
POST /ideas → IDEA v15
POST /pipeline/start → run_id=806b671a-29fe-4b62-8229-d57009a0792e (HTTP 201)
Approve STORY → SCRIPT generation
Approve SCRIPT → STORYBOARD batch v2 (4 PNG frames)
GET /assets/{id}/content → HTTP 200 (PNG)
Reject STORYBOARD with note → POST /pipeline/regenerate → batch v3 (4 frames)
Approve STORYBOARD → status COMPLETED
```

**Wall-clock:** ~2 min from pipeline start to COMPLETED (includes one STORYBOARD regen with ComfyUI).

---

## Acceptance criteria mapping

| AC | Olares evidence |
|---|---|
| **AC-1** Grid of 4 images | V-01 `FRAME_COUNT=4` at latest batch; web unit `storyboardReview.test.ts` |
| **AC-2** Lightbox preview | `StoryboardLightbox.tsx` (UI component; manual screenshot optional) |
| **AC-3** Approve-all → COMPLETED | V-04 `FINAL status=COMPLETED`; single STORYBOARD APPROVED approval |
| **AC-4** Reject → regenerate | V-03 regen HTTP 200; v2→v3 increment; `PRIOR_V2=4 NEW_V3=4` |
| **AC-5** AI badge on frames | `ReviewPage.tsx` badge markup (web; not exercised in headless Olares script) |

---

## Governance compliance

| Constraint | Verified |
|---|---|
| Batch-level approve/reject only | V-05 — one REJECTED + one APPROVED row for STORYBOARD; no per-frame approvals |
| Regen creates version+1 batch | v2 → v3 with 4 rows each |
| Prior batches immutable | V-03 `PRIOR_V2=4` after regen |
| D-47 inputs (script + rejection note) | Worker `us17` deployed; regen succeeded after REJECTED note |
| No schema migrations | None applied |
| No asset history / lineage UI | Not shipped |
| No video workflow | Pipeline terminates at COMPLETED |

---

## Approvals audit (run 806b671a)

```
STORYBOARD | REJECTED | US-17 Olares: increase contrast and wide
STORYBOARD | APPROVED |
```

---

## Deploy commands used

```bash
# On dev machine
docker build -f api/Dockerfile -t aimpos-api:us17 .
docker build -f worker/Dockerfile -t aimpos-worker:us17 .
docker save … | scp olares@10.0.0.34:/tmp/

# On Olares
API_TAR=/tmp/aimpos-api-us17.tar WORKER_TAR=/tmp/aimpos-worker-us17.tar bash /tmp/deploy_us17.sh
bash /tmp/run_e2e_remote.sh
```

Scripts: `deploy/k8s/us17-verify/`
