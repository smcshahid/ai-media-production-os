# Sprint 4C — US-V02 Spark Full Demo Acceptance (governance brief)

**Status:** **SUBMITTED** — governance review pending. **No verification scripts or Olares execution until brief ACCEPT.**  
**Story type:** **Verification / attestation** — not a feature story.  
**Story:** US-V02 "Spark Full demo acceptance validation" · EPIC-05 · **P0** · 2 SP.  
**Prerequisites (all closed):** US-18 ✅ · US-19 ✅ · Visual MVP US-V01 ✅ (`v0.4.0-usv01`).  
**Blocks:** **M6 — Spark Full signed** (`docs/sprints/spark-full-governance-brief.md` §6). Unblocks post–Spark Full planning only after US-V02 closure.

**Parent program:** Spark Full (`docs/sprints/spark-full-governance-brief.md` **ACCEPT**)  
**Baseline:** `v0.6.0-us19` (US-19 export bundle closure)  
**Decision records under test:** **`D-37` through `D-54`** (integrated attestation on Olares)

---

## 0. Story classification — verification only

US-V02 is the **Spark Full sign-off gate**. It **does not** authorize:

| Forbidden in US-V02 | Rationale |
|---|---|
| New API routes or response shapes | Platform frozen post US-19 |
| New worker agents or Temporal activities | All six stages + export implemented |
| New web screens or UX flows beyond existing review/export surfaces | Feature stories closed |
| Schema migrations | Scope Freeze |
| Lineage UI (US-20) or asset history UI (US-22/23) | Deferred — SQL attestation only |
| Publishing, collaboration, cloud sync | Out of Spark Full scope |
| Refactors, perf work, or "while we're here" fixes | Defect hotfix protocol only |

**Authorized work:** Olares verify scripts, evidence collection, verification plan, acceptance package, closure tag — **zero product code** unless a **blocking defect** is discovered (hotfix on underlying story, re-run US-V02).

---

## 1. Objective

Execute **one authoritative end-to-end Spark Full acceptance run on Olares** using a **fresh project**, validating the complete six-stage pipeline plus export bundle attestation and decision records **D-37 through D-54**:

```
Idea → STORY (human edit + approve) → SCRIPT (reject + regen + approve)
     → STORYBOARD (batch v1 → [reject + regen → batch v2] → batch approve)
     → VIDEO (reject + regen + approve) → COMPLETED
     → Export ZIP download + manifest hash verify
```

| Dimension | Intent |
|---|---|
| **User value** | Product-owner confidence that Spark Full delivers Idea → approved video → portable export on real hardware |
| **System value** | Repeatable demo script + evidence pack closing **M6** |
| **Spark Full boundary** | Terminates at **export bundle attestation** after **`COMPLETED`** at VIDEO approve (D-51) |

---

## 1A. Governance resolution — inherited Visual MVP path

US-V02 **re-attests** the US-V01 normative demo path through STORYBOARD (including A-01 D-47 extension) before entering VIDEO. Visual MVP terminal semantics at STORYBOARD approve **no longer apply** — STORYBOARD approve advances to VIDEO per D-51 (attested in US-18).

| Phase | Terminal status | US-V02 treatment |
|---|---|---|
| Through STORYBOARD approve (Visual MVP) | Was `COMPLETED` | **Not terminal** — must continue to VIDEO |
| After VIDEO approve | `COMPLETED` | **Terminal** per D-51 |
| Export | N/A in US-V01 | **Required** — `GET /export/{run_id}` after COMPLETED |

---

## 1B. Export bundle attestation (D-52..D-54)

After terminal `COMPLETED`, the Olares run **MUST** download the export bundle and verify:

| Check | Contract | Expected |
|---|---|---|
| Export gate | D-52 | HTTP 200 only when `COMPLETED`; HTTP 409 when not |
| ZIP contents | D-52 | Exactly 9 entries in deterministic order |
| Manifest | D-53 | `manifest_version=1`; 8 file records with hashes, versions, approval timestamps |
| Integrity | D-53 | On-disk SHA-256 matches manifest for all 8 assets |
| Audit | D-54 | `BUNDLE_EXPORTED` with `manifest_hash`, `file_count=8`, `zip_size_bytes` |
| Source | D-52 | Bytes from MinIO; bundle not persisted to object store |

**Negative test:** Attempt export on a non-COMPLETED run (if available) → HTTP 409.

---

## 2. Source review

### 2.1 Primary acceptance criteria (Spark Full)

| # | Criterion | Demo step |
|---|---|---|
| AC-1 | Enter idea on **fresh project** | S-01, S-02 |
| AC-2 | Start pipeline | S-03 |
| AC-3 | Approve story **with one edit** | S-05, S-06 |
| AC-4 | Reject script once, regenerate, approve | S-08 – S-11 |
| AC-5 | Storyboard batch reject + regen + approve (A-01 path) | S-12a – S-14 |
| AC-6 | VIDEO gate reached; reject + regen + approve | S-15 – S-20 |
| AC-7 | Pipeline status **COMPLETED** after VIDEO approve | S-20 (D-51) |
| AC-8 | Export ZIP download succeeds | S-21 |
| AC-9 | Manifest hashes verify | S-22 |
| AC-10 | `BUNDLE_EXPORTED` audit recorded | S-23 |
| AC-11 | Lineage idea → video (SQL) | S-24 |
| AC-12 | Audit: human gates + local model invocations | S-24 |
| AC-13 | Worker restart — COMPLETED stable | S-25 |
| — | Pass without manual DB intervention | All steps |
| — | 100% local inference (**SC-02**) | Worker audit `model_id` |

### 2.2 Success criteria mapping (Spark Full + inherited)

| ID | Criterion | US-V02 evidence |
|---|---|---|
| **SC-01** | Idea → approved video | E2E `COMPLETED` after VIDEO approve |
| **SC-02** | 100% local inference | Audit `model_id`; no cloud URLs |
| **SC-11** | Export integrity | ZIP + manifest hash verify (D-52..D-54) |
| **SC-F01** | Fourth human gate (VIDEO) | `approvals` VIDEO APPROVED |
| **SC-F02** | Video artifact MP4 15–30 s, ≤480p | Asset row + content-read |
| **SC-F03** | Lineage chain to video | SQL on `lineage_edges` |
| **SC-F04** | Visual MVP path regression | STORYBOARD stages unchanged vs US-V01 |
| **SC-F05** | Worker durability at terminal | Restart after COMPLETED |
| **SC-V04** | Versioned assets | SQL asset chain incl. VIDEO + export files |
| **SC-V05** | AI calls logged | Audit trail per agent |
| **SC-V06** | Workflow durability | Worker restart procedure |
| **SC-V07** | Time to first story < 5 min | Audit timestamp delta |

### 2.3 Approved deliverables (verification story)

| Task | US-V02 deliverable |
|---|---|
| T-V02-01 | `deploy/k8s/usv02-verify/verify_usv02.sh` (+ deploy/run helpers) |
| T-V02-02 | Acceptance package § SC-01, SC-11, SC-F01..F05 |
| T-V02-03 | Acceptance package § D-37..D-54 matrix |
| T-V02-04 | Stakeholder sign-off in closure report |

---

## 3. Decision record attestation matrix (D-37 – D-54)

| ID | Title | Exercised? | Demo phase | Olares evidence |
|---|---|---|---|---|
| **D-37** | Approved story (no branch promotion) | **Yes** | STORY | human-edit; no row on approve |
| **D-38** | Regeneration append-only | **Yes** | SCRIPT, STORYBOARD, VIDEO | version chains |
| **D-39** | Script asset (`script.fountain`) | **Yes** | SCRIPT | SCRIPT rows + lineage |
| **D-40** | Fountain validation gate | **Yes** (implicit) | SCRIPT | Successful store |
| **D-41** | Approved script (no branch promotion) | **Yes** | SCRIPT approve | No SCRIPT row on approve |
| **D-42** | Script regen input contract | **Yes** | SCRIPT regen | Regen after reject |
| **D-43** | Storyboard frame contract | **Yes** | STORYBOARD | batch version + frame_index |
| **D-44** | Batch completeness | **Yes** | STORYBOARD | 4 frames per batch |
| **D-45** | Frame count = 4 | **Yes** | STORYBOARD | COUNT=4 per batch |
| **D-46** | Approved storyboard batch | **Yes** | STORYBOARD approve | Single APPROVED |
| **D-47** | Storyboard regen input contract | **Yes** | STORYBOARD regen | v1 preserved; v2 fresh |
| **D-48** | VIDEO asset contract | **Yes** | VIDEO | `scene_video.mp4` in MinIO |
| **D-49** | Approved storyboard as video input | **Yes** | VIDEO gen | 4 approved frames |
| **D-50** | VIDEO regen input contract | **Yes** | VIDEO regen | Reject note → v2 |
| **D-51** | Pipeline terminal at VIDEO approval | **Yes** | VIDEO approve | COMPLETED only here |
| **D-52** | Export bundle contract | **Yes** | Export | 9 entries; COMPLETED gate |
| **D-53** | Manifest contract v1 | **Yes** | Export | hashes + metadata |
| **D-54** | Export audit contract | **Yes** | Export | `BUNDLE_EXPORTED` |

---

## 4. Demo script (normative outline)

**Environment:** Olares `aimpos-mwayolares`. **Fresh project UUID.** **Images:** ≥ `v0.6.0-us19` (`aimpos-api:us19`, `aimpos-worker:us18` or unified tag).

| Step | Action | Expected state | Decisions |
|---|---|---|---|
| S-00 | ComfyUI + ffmpeg preflight | Queue ready; ffmpeg in worker | D-08 |
| S-01 – S-14 | **US-V01 path** (incl. A-01) | STORYBOARD approved; **not COMPLETED** | D-37..D-47 |
| S-15 | Poll VIDEO gate | `AWAITING_APPROVAL` / `VIDEO` | D-48 |
| S-16 | Reject VIDEO + note | Rejection recorded | D-50 setup |
| S-17 | Regenerate VIDEO | New VIDEO version | D-38, D-50 |
| S-18 | Poll VIDEO gate | `AWAITING_APPROVAL` / `VIDEO` | — |
| S-19 | Approve VIDEO | **`COMPLETED`** | **D-51** |
| S-20 | Confirm STORYBOARD approve ≠ COMPLETED | SQL attestation | D-51 regression |
| S-21 | `GET /export/{run_id}` | HTTP 200 ZIP | D-52 |
| S-22 | Unzip + manifest hash verify | 9 files; hashes match | D-52, D-53 |
| S-23 | SQL `BUNDLE_EXPORTED` | audit row present | D-54 |
| S-24 | SQL attestation | lineage + gates + models | AC-11, AC-12 |
| S-25 | Worker restart + poll | `COMPLETED` unchanged | SC-F05 |

**Forbidden:** Manual SQL to unblock the demo.

**Time budget:** Allow 60+ minutes wall-clock (ComfyUI storyboard batches + VIDEO generation).

---

## 5. Olares SQL attestation (summary)

Full query catalog in verification plan (to be authored after brief ACCEPT). Summary checks:

| ID | Check |
|---|---|
| V-01 | Terminal `COMPLETED` after VIDEO approve only |
| V-02 | Human gate decisions (STORY, SCRIPT, STORYBOARD, VIDEO) |
| V-03 | No asset write on approve (D-37, D-41, D-46, D-51) |
| V-04 | Regen immutability (D-38, D-42, D-47, D-50) |
| V-05 | Storyboard batch structure (D-43..D-45) |
| V-06 | VIDEO asset + metadata (D-48) |
| V-07 | Lineage chain to video (SC-F03) |
| V-08 | Local model invocations (SC-02) |
| V-09 | Export audit (D-54) |
| V-10 | Export 409 on non-COMPLETED (D-52 gate) |

---

## 6. Deliverables

| Artifact | Path (proposed) |
|---|---|
| Governance brief | `docs/sprints/sprint-4c-usv02-brief.md` (this document) |
| Verification plan | `docs/sprints/sprint-4c-usv02-verification-plan.md` (after ACCEPT) |
| Verify scripts | `deploy/k8s/usv02-verify/` |
| Olares acceptance | `evidence/us-v02-verification/olares-<date>/US-V02-ACCEPTANCE-PACKAGE.md` |
| Closure report | `docs/sprints/sprint-4c-usv02-closure-report.md` |
| Closure tag | `v0.7.0-usv02` *(proposed)* |

---

## 7. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-01 | Long Olares wall-clock (> 60 min) | Async polling; slideshow fallback for VIDEO (D-48) |
| R-02 | GPU sequencer contention | D-08 sequencing in verify preflight |
| R-03 | Export on wrong run status | Negative 409 test in verify script |
| R-04 | US-V01 regression if D-51 broken | V-01/V-20 SQL checks mid-run |

---

## 8. Project status

| Item | Status |
|---|---|
| **US-19** | **CLOSED** (`v0.6.0-us19`) |
| **US-V02** | **BRIEF SUBMITTED** — awaiting governance review |
| **Frontier** | **US-V02** |
| **M6 Spark Full signed** | Blocked on US-V02 Olares PASS + closure |

**Next step:** Governance review of this brief. Upon ACCEPT, author verification plan and execute Olares run — **no product code until then**.

---

## 9. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial brief — submitted at US-19 closure |
