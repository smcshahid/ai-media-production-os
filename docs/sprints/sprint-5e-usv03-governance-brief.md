# Sprint 5E — US-V03 Phase 2 Acceptance (governance brief)

**Status:** **CLOSED** — governance ACCEPT 2026-06-15 · tag `v0.12.0-usv03` · **M7 complete**.  
**Story type:** **Verification / attestation** — not a feature story.  
**Story:** US-V03 Phase 2 integrated acceptance · EPIC-06 · **P0** · **2 SP**  
**Parent program:** Spark Full Phase 2 ([spark-full-phase2-governance-brief.md](./spark-full-phase2-governance-brief.md) **ACCEPT**)  
**Prerequisites (all closed):** US-20 ✅ · US-22 ✅ · US-23 ✅ · US-21 ✅ · US-V02 ✅ · M6 ✅  
**Baseline:** `v0.11.0-us21` (`59506aa`)  
**Blocks:** **M7 — Spark Full Phase 2 signed**

**Decision records under test:** **D-55 through D-59** (Phase 2) · **D-37 through D-54** (Phase 1 regression subset)

---

## 0. Story classification — integrated validation only

US-V03 is the **Phase 2 sign-off gate**. It **validates completed observability capabilities** as an integrated whole on Olares. It **does not** authorize new product functionality.

| Forbidden in US-V03 | Rationale |
|---|---|
| New API routes, response shapes, or WebSocket protocol changes | Phase 2 stories closed |
| New web screens, UX flows, or UI features | Acceptance validates shipped surfaces only |
| Schema migrations or Alembic revisions | Scope Freeze |
| Worker / Temporal workflow changes | D-37..D-54 frozen |
| Lineage editing, history restore, diff UI, notifications | Explicit Phase 2 exclusions |
| Publishing, collaboration, multi-project UI | Out of charter |
| Refactors, perf tuning, or "while we're here" fixes | Defect hotfix protocol only |
| Manual SQL to repair API/UI mismatches during acceptance | Invalidates attestation |

**Authorized work:** Verification plan, Olares verify scripts (`deploy/k8s/usv03-verify/`), evidence packages, acceptance report, governance closure, closure tag — **zero product code** unless a **blocking defect** is discovered (hotfix on underlying story, re-run US-V03).

---

## 1. Objective

Execute **one authoritative integrated acceptance run on Olares** that proves Phase 2 observability works **together** with the frozen Spark Full production pipeline:

```
US-V02 normative E2E (Idea → VIDEO → COMPLETED → Export)
        +
Phase 2 cross-feature attestation on the same run (or attested reference run)
        ├── US-20  Lineage Viewer      (D-55, D-56)
        ├── US-22  Asset History API   (D-57)
        ├── US-23  Asset History UI    (D-58) — API + content-read spot checks
        └── US-21  Realtime Updates    (D-59) — WS push + poll fallback
```

| Dimension | Intent |
|---|---|
| **User value** | Creator can trace provenance, browse all versions, and see live status — without SQL or manual refresh — on real hardware |
| **System value** | Repeatable integrated verify script + evidence pack closing **M7** |
| **Phase 2 boundary** | **Validation only** — no new capabilities beyond closed story tags |

### 1.1 Acceptance priorities (governance mandate)

| Priority | Focus | US-V03 treatment |
|---|---|---|
| **1** | **Cross-feature validation** | Single run ties lineage + history + realtime to same `project_id` / `run_id` |
| **2** | **Olares validation** | Primary gate on `aimpos-mwayolares`; bash verify scripts only |
| **3** | **End-to-end workflow verification** | Full US-V02 path on **fresh project** (or documented fresh run) |
| **4** | **Regression verification** | Re-attest export, lineage edges, audit, D-51 terminal semantics |
| **5** | **Evidence collection** | Structured packages under `evidence/us-v03-verification/` |

---

## 2. Completed capabilities under test

All four Phase 2 implementation stories are **CLOSED**. US-V03 attests their **integration**, not individual re-implementation.

| Story | Tag | Capability | Primary surface |
|---|---|---|---|
| **US-20** | `v0.8.0-us20` | Lineage Viewer | `GET /lineage/{run_id}` · `/lineage` · Export lineage panel |
| **US-22** | `v0.9.0-us22` | Asset History API | `GET /assets/history?project_id=` (D-57) |
| **US-23** | `v0.10.0-us23` | Asset History UI | `/history` · stage-grouped browser |
| **US-21** | `v0.11.0-us21` | Realtime Updates | `/ws/pipeline` · Live/Polling indicator |

**Reference attestation project (regression spot-check):** `76aa4418-d92d-45f7-954c-a10383ea511a` · run `042983f7-0f55-48c3-9d65-fce89a684625` (US-V02 COMPLETED path) — usable for read-only Phase 2 checks when fresh E2E wall-clock is deferred.

**Fresh E2E project:** US-V03 **MUST** include at least one **fresh-project** normative run for SC-P2-06 / D-51 regression (mirrors US-V02).

---

## 3. Success criteria mapping

### 3.1 Phase 2 primary (SC-P2)

| ID | Criterion | Target | US-V03 evidence |
|---|---|---|---|
| **SC-P2-01** | Lineage visibility | Chain idea → story → script → frames → **video** | `GET /lineage/{run_id}` node count + stage order |
| **SC-P2-02** | Lineage accuracy | API matches `lineage_edges` for run | SQL/API parity (S-V03-20) |
| **SC-P2-03** | Version transparency | All stages, newest-first | `GET /assets/history` row counts vs SQL |
| **SC-P2-04** | Version preview | Content-read per stage | HTTP 200 spot-check STORY + STORYBOARD |
| **SC-P2-05** | Realtime status | Gate transition → push **≤ 2 s** | WS timestamp delta during live gate (S-V03-21) |
| **SC-P2-06** | Phase 1 regression | US-V02 path PASS | COMPLETED at VIDEO · export 9 files · D-54 |
| **SC-P2-07** | No pipeline drift | D-37..D-54 unchanged | SQL attestation matrix §5 |

### 3.2 Inherited (must not regress)

| ID | Source | US-V03 treatment |
|---|---|---|
| SC-01, SC-02, SC-11 | Spark Full | Re-attested via US-V02 subset |
| SC-F01..F05 | Phase 1 VIDEO | Terminal COMPLETED · worker restart |
| SC-V04..V07 | Visual MVP | Version/audit visibility in history + SQL |

---

## 4. Cross-feature validation matrix

US-V03 **MUST** demonstrate that Phase 2 surfaces are **consistent with each other** on the same project/run.

| ID | Cross-check | Method | Pass criteria |
|---|---|---|---|
| **XF-01** | Lineage approved chain ⊆ History rows | Compare lineage `nodes[].asset_id` set vs history API IDs for run | Every lineage node asset exists in history `versions[]` |
| **XF-02** | History row count ≥ lineage node count | SQL `asset_versions` vs API history total | History ≥ lineage (history includes non-approved versions) |
| **XF-03** | Export manifest assets ∈ History | Export manifest file hashes vs history `content_hash` | 8 export files match approved-version hashes |
| **XF-04** | Realtime status ≡ REST at gate | `GET /pipeline/status` vs WS `pipeline.status` payload | Deep equality at subscribe snapshot and after gate |
| **XF-05** | COMPLETED → Lineage + Export + History readable | HTTP 200 on all three surfaces | No 409/404 on COMPLETED run |
| **XF-06** | No mutation from observability reads | `asset_versions` COUNT before/after Phase 2 read suite | Count unchanged |

**Forbidden:** Using `GET /assets` flat list as history data path in verify (D-57 only).

---

## 5. Decision record attestation (D-55 – D-59)

| ID | Title | Exercised? | Evidence |
|---|---|---|---|
| **D-55** | Lineage API read contract | **Yes** | `GET /lineage/{run_id}` 200; edges match SQL |
| **D-56** | Lineage UI scope (list/tree, read-only) | **Yes** | API/UI smoke; no graph libs; IDEA synthetic |
| **D-57** | Asset history read API | **Yes** | Stage groups; newest-first; SQL row parity |
| **D-58** | Asset history UI scope | **Yes** | `/history` route in bundle; content-read spot-check |
| **D-59** | Realtime channel contract | **Yes** | WS auth/subscribe; shared payload; poll fallback |

Phase 1 records **D-37..D-54** re-attested via US-V02 subset (§7) — not re-litigated individually unless regression fails.

---

## 6. Acceptance script (normative outline)

**Environment:** Olares `aimpos-mwayolares` · images ≥ `aimpos-api:us21` · `aimpos-worker:us21`

### 6.1 Phase A — Preflight (read-only)

| Step | Action | Expected |
|---|---|---|
| P-01 | Cluster health `/health` | postgres, redis, minio ok |
| P-02 | Image tags | `us21` on API + worker |
| P-03 | Unit regression (local CI reference) | API 106+ · web 36+ logged in evidence |

### 6.2 Phase B — US-V02 E2E (fresh project)

| Step | Action | Expected |
|---|---|---|
| B-01 | Create fresh project | UUID captured |
| B-02 | US-V02 normative path S-01..S-25 | COMPLETED at VIDEO approve (D-51) |
| B-03 | Export ZIP + manifest verify | 9 entries; hashes match (D-52, D-53) |
| B-04 | `BUNDLE_EXPORTED` audit | D-54 row present |
| B-05 | Worker restart | COMPLETED stable (SC-F05) |

*Reuse `deploy/k8s/usv02-verify/` helpers where applicable; US-V03 orchestrates or embeds subset.*

### 6.3 Phase C — Phase 2 integrated attestation (same run)

Executed after **COMPLETED** (or at documented gates during B-02 for SC-P2-05).

| Step | Story | Action | Expected |
|---|---|---|---|
| C-01 | US-20 | `GET /lineage/{run_id}` | 200; VIDEO node; edge SQL parity |
| C-02 | US-22 | `GET /assets/history?project_id=` | 200; 5 stage groups; SQL row parity |
| C-03 | US-22 | STORY versions newest-first | `[2,1]` or higher after regen path |
| C-04 | US-23 | Content-read from history STORY `asset_id` | HTTP 200 |
| C-05 | US-23 | Web bundle contains `/history` | Local build grep (S-V03-23-01) |
| C-06 | US-21 | WS smoke (in-pod) | `WS_SMOKE=PASS` |
| C-07 | US-21 | REST poll fallback | `GET /pipeline/status` 200 |
| C-08 | US-21 | Redis-down degradation | Publish non-fatal; poll still works (spot-check or documented) |
| C-09 | Cross | XF-01..XF-06 matrix | All PASS |

### 6.4 Phase D — Regression on reference project (optional fast path)

| Step | Action | Expected |
|---|---|---|
| D-01 | Re-run `us20`/`us22`/`us23`/`us21` verify subsets on US-V02 reference project | FAIL=0 |
| D-02 | Confirm no schema migration files in repo diff | Zero Alembic changes |

**Time budget:** Allow **60–90+ minutes** if Phase B fresh E2E includes full GPU path (inherits US-V02).

---

## 7. Regression verification

### 7.1 Phase 1 (Spark Full) — mandatory subset

| Check | Source | US-V03 step |
|---|---|---|
| Terminal COMPLETED at VIDEO only | D-51 | B-02, V-03-01 |
| Export 409 when not COMPLETED | D-52 | V-03-02 (negative) |
| Export 9 files + manifest hashes | D-52, D-53 | B-03 |
| `BUNDLE_EXPORTED` audit | D-54 | B-04 |
| Lineage edges to VIDEO | SC-F03 | C-01 + SQL |
| Regen append-only | D-38 | SQL version chains |
| Worker restart stable | SC-F05 | B-05 |

### 7.2 Per-story verify script regression

US-V03 **MUST** invoke or equivalent-check outputs from:

| Script | Story | Minimum checks |
|---|---|---|
| `deploy/k8s/us20-verify/verify_us20.sh` | US-20 | Lineage API/SQL parity |
| `deploy/k8s/us22-verify/verify_us22.sh` | US-22 | History API/SQL parity |
| `deploy/k8s/us23-verify/verify_us23.sh` | US-23 | History + lineage + export regression |
| `deploy/k8s/us21-verify/verify_us21.sh` | US-21 | WS smoke + poll + regressions |

**Integration rule:** US-V03 verify script is the **orchestrator**; individual story scripts remain the **regression library** — not replaced.

---

## 8. Olares validation strategy

### 8.1 Deliverables (proposed)

```
deploy/k8s/usv03-verify/
  verify_usv03.sh       # Master orchestrator (S-V03-01..S-V03-30)
  run_remote.sh
  collect_usv03.sh      # Evidence harvest
  deploy_usv03.sh       # Pin us21 images (if not already deployed)
```

### 8.2 Measurable acceptance steps (preview)

| ID | Check | Pass threshold |
|---|---|---|
| S-V03-01 | Fresh project E2E reaches COMPLETED | `pipeline_runs.status=COMPLETED` |
| S-V03-02 | Export regression | HTTP 200; 9 ZIP entries |
| S-V03-10 | Lineage API/SQL parity | Edge count match |
| S-V03-11 | Lineage includes VIDEO node | `nodes[]` contains VIDEO |
| S-V03-20 | History API/SQL parity | API count = SQL count |
| S-V03-21 | Realtime latency | Gate → WS event **≤ 2000 ms** (SC-P2-05) |
| S-V03-22 | WS reconnect after API rollout | Re-subscribe **≤ 60 s** |
| S-V03-23 | Poll fallback | REST 200; UI mode Polling acceptable |
| S-V03-24 | Cross-feature XF-01..06 | All PASS |
| S-V03-30 | No observability writes | `asset_versions` COUNT unchanged |

### 8.3 Local verification gate (pre-Olares)

| Suite | Threshold |
|---|---|
| API unit | ≥ 106 passed |
| Web unit | ≥ 36 passed |
| Web build | PASS (includes `/history`, `/ws/pipeline` client) |
| Worker unit | PASS (publish non-fatal) |

Evidence: `evidence/us-v03-verification/local-<date>/`

---

## 9. Evidence collection

### 9.1 Required artifacts

| Artifact | Path |
|---|---|
| Olares acceptance package | `evidence/us-v03-verification/olares-<date>/US-V03-ACCEPTANCE-PACKAGE.md` |
| Master verify log | `evidence/.../logs/usv03-verify.log` |
| US-V02 E2E log (Phase B) | `evidence/.../logs/usv02-e2e.log` |
| Phase 2 cross-feature log | `evidence/.../logs/phase2-cross.log` |
| SQL attestation | `evidence/.../sql/v03-*.txt` |
| Local regression | `evidence/us-v03-verification/local-<date>/logs/` |

### 9.2 Acceptance package contents

| Section | Content |
|---|---|
| Executive summary | PASS/FAIL · project/run UUIDs · image tags |
| SC-P2 matrix | SC-P2-01..07 with evidence links |
| Cross-feature matrix | XF-01..06 results |
| D-55..D-59 attestation | Per-decision PASS |
| Phase 1 regression | D-37..D-54 subset PASS |
| Closure recommendation | READY / NOT READY for M7 |

---

## 10. Explicit exclusions

US-V03 validates **shipped** Phase 2 capabilities only.

| Exclusion | Rationale |
|---|---|
| New lineage/history/realtime features | Stories closed |
| Asset restore, rollback, promote, diff UI | Deferred |
| Audit trail browser as primary UI | Deferred |
| HTML5 video player | Phase 1 unchanged |
| WebSocket event replay / persistence | D-59 out of scope |
| Multi-project UI | MVP single-project |
| Publishing / collaboration | Scope Freeze |
| Cloud inference / egress | Sovereignty |
| M7 closure before Olares PASS | Governance lifecycle |

---

## 11. Deliverables

| Artifact | Path |
|---|---|
| Governance brief | `docs/sprints/sprint-5e-usv03-governance-brief.md` (this document) |
| Verification plan | `docs/sprints/sprint-5e-usv03-verification-plan.md` (after brief ACCEPT) |
| Verify scripts | `deploy/k8s/usv03-verify/` |
| Verification report | `docs/sprints/sprint-5e-usv03-verification-report.md` |
| Closure report | `docs/sprints/sprint-5e-usv03-closure-report.md` |
| Closure tag | `v0.12.0-usv03` *(proposed)* |

---

## 12. Required lifecycle (after brief ACCEPT)

| Step | Activity | Authorization |
|---|---|---|
| 1 | Verification plan governance review | Plan ACCEPT |
| 2 | Author `verify_usv03.sh` + helpers | Plan ACCEPT |
| 3 | Local regression gate | Pre-Olares |
| 4 | Olares integrated run | Evidence PASS |
| 5 | Governance closure review | ACCEPT |
| 6 | Commit · tag · push · closure report | Post-Olares PASS only |

**No repository closure before successful Olares verification.**

---

## 13. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-V03-01 | Fresh E2E wall-clock exceeds session budget | Phase D reference-project fast path + async B-02 |
| R-V03-02 | Cross-feature UUID drift (wrong run_id) | Capture `run_id` once; parametrize all C-steps |
| R-V03-03 | WS latency flake on slow gates | Measure over 3 samples; median ≤ 2 s |
| R-V03-04 | US-V02 regression broken by Phase 2 | B-phase mandatory; fail-closed on D-51 |
| R-V03-05 | Evidence package incomplete | `collect_usv03.sh` checklist |

---

## 14. Authorization boundary

| Stage | Status |
|---|---|
| Phase 2 program brief | **ACCEPT** |
| US-20 / US-22 / US-23 / US-21 | **CLOSED** |
| **US-V03 brief** | **CLOSED** — `v0.12.0-usv03` |
| **US-V03 verification plan** | **EXECUTED PASS** |
| **US-V03 closure** | **CLOSED** — M7 complete |

**Upon plan ACCEPT:** Implement verify scripts → local gate → Olares Path A → acceptance package → M7 closure.

---

## 15. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-10 | Initial submission — Phase 2 integrated acceptance (post US-21 closure) |
| 1.1 | 2026-06-10 | Governance ACCEPT WITH CONDITION — verification planning authorized |
