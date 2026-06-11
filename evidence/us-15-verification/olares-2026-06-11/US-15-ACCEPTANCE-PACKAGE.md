# US-15 Acceptance Package — Olares Verification

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-11  
**API image:** `docker.io/library/aimpos-api:us15`  
**Worker image:** `docker.io/library/aimpos-worker:us15`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Run:** `ad45f3a7-e772-437b-be00-c62a9121cec1`  
**Verify log:** `logs/us15-verify.log`  
**Implementation report:** `docs/sprints/sprint-3f-us15-implementation-report.md`

---

## Verification summary

| Check | Result |
|---|---|
| V-01 — Fountain content sample (AC-1) | **PASS** |
| V-02 — SCRIPT reject with note | **PASS** |
| V-03 — Regenerate #1–#3 → new SCRIPT versions | **PASS** |
| V-04 — 4th regenerate → 429 | **PASS** |
| V-05 — Approve → STORYBOARD gate (AC-2) | **PASS** |
| V-06 — D-41 approved script (AC-4) | **PASS** |
| V-07 — D-42 regen worker evidence (AC-3) | **PASS** |

**Closure recommendation:** **ACCEPT**

---

## Test gates before deployment

| Suite | Result |
|---|---|
| API unit | 78 passed |
| Worker unit | 21 passed |
| Web unit | 20 passed |

Local log: `evidence/us-15-verification/local-2026-06-11/logs/pytest-summary.txt`

---

## Setup

Verification continued the US-14 run at `AWAITING_APPROVAL`/`SCRIPT` (active run prevented a second `pipeline/start`). SCRIPT v1 asset: `e96cae0b-29f5-4bdb-b26b-f95efeee175b`.

---

## V-01 / AC-1 — Fountain sample

```
INT. RESEARCH LAB - DAWN
...
DR. ELARA VOSS
(whispering)
If I send this...
```

Content-read API extended to SCRIPT (`text/plain`). Web formatter unit tests pass (scene, action, character, dialogue).

---

## V-02 — Reject SCRIPT

```
POST /pipeline/approve {"stage":"SCRIPT","decision":"REJECTED","note":"US-15 verify: deepen dialogue and clarify stakes."}
HTTP 200 → approval_id 287c88b6-9bed-4d9f-a18d-75240eb95f9a
```

---

## V-03 / AC-3 — Regenerate #1, #2, #3

| Regen | HTTP | regenerations_used | New version | asset_version_id | content_hash (prefix) |
|---|---|---|---|---|---|
| #1 | 200 | 1 | v1→**v2** | `a12e7212-…` | `a38558ad…` |
| #2 | 200 | 2 | v2→**v3** | `4ba320d7-…` | `87b3529d…` |
| #3 | 200 | 3 | v3→**v4** | `45bc3ede-…` | `e7ece1ea…` |

Append-only chain preserved (v1 row unchanged).

**D-42 note:** Regen activities used approved STORY + DB SCRIPT rejection rationale; worker logs show distinct `script_agent_completed` events (activity ids 8, 11, 14). Regen #2 attempt 1 failed D-40 validator; retry succeeded — no invalid asset stored.

---

## V-04 — 4th regenerate (429)

```
HTTP 429
{"detail":"regeneration limit reached for stage SCRIPT (max 3 per run)"}
```

---

## V-05 / AC-2 — Approve SCRIPT → STORYBOARD

```
POST /pipeline/approve {"stage":"SCRIPT","decision":"APPROVED"}
HTTP 200 → approval_id 6b54f2c5-03b2-4a0c-bdb6-f970b7ab8093

GET /pipeline/status
→ status=AWAITING_APPROVAL, current_stage=STORYBOARD
```

Presentation: dashboard maps `RUNNING` → GENERATING during stub storyboard generation.

---

## V-06 / AC-4 / D-41 — Approved script resolution

| Field | Value |
|---|---|
| Latest SCRIPT version | **4** (`45bc3ede-2ac7-4b58-aad8-bae8a5debf2d`) |
| content_hash | `e7ece1ea235102fe97f088cb4e58a5f2c94294a7e902b6ebda96213b0b84c18a` |
| SCRIPT approval | `APPROVED` (`6b54f2c5-…`) |
| New SCRIPT row on approve? | **No** — approve only writes `approvals` |

D-41 resolution: latest SCRIPT version + `APPROVED` approval for `stage=SCRIPT`.

---

## D-40 / D-42 attestation

- **D-40:** Invalid regen output rejected before store (regen #2 attempt 1).
- **D-42:** Inputs = approved STORY + latest SCRIPT rejection rationale; no prior SCRIPT bytes in prompt.

---

## Scope attestation

| In scope | Delivered |
|---|---|
| SCRIPT review mode + Fountain preview | ✅ |
| SCRIPT approve/reject/regenerate | ✅ |
| D-41 approved script contract | ✅ |
| D-42 regeneration input contract | ✅ |

| Out of scope | Status |
|---|---|
| Schema migration | None |
| Storyboard agent | Stub only |
| Human-edit SCRIPT | None |
| Asset browser/history/PDF | None |

---

## Formal closure request

All four Visual MVP ACs evidenced on Olares with regression suites green. **Recommend ACCEPT** for US-15 formal closure review.
