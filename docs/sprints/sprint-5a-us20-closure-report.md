# US-20 Repository Closure Report

**Date:** 2026-06-11  
**Story:** US-20 — Lineage Viewer  
**Formal status:** **ACCEPTED**  
**Release tag:** `v0.8.0-us20`  
**Spark Full milestone:** **M7a — Phase 2 traceability** (first Phase 2 story closed)

---

## 1. Commits (US-20 closure)

| # | SHA (short) | Message |
|---|---|---|
| 1 | `db54981` | `feat(us20): lineage viewer, Olares verification, and repository closure` |

**Prior baseline:** `v0.7.0-usv02` (`905f1f1`)

---

## 2. Repository state

| Field | Value |
|---|---|
| **Branch** | `main` |
| **HEAD** | `db54981` · **tag** `v0.8.0-us20` → `db54981` |
| **Tag** | `v0.8.0-us20` |
| **Remote** | `origin/main` — pushed 2026-06-11 |
| **Tag remote** | `origin/v0.8.0-us20` — pushed |
| **Working tree** | **Clean** (post-closure) |

---

## 3. Deliverables indexed

| Artifact | Path |
|---|---|
| Governance brief | `docs/sprints/sprint-5a-us20-brief.md` |
| Implementation plan | `docs/sprints/sprint-5a-us20-implementation-plan.md` |
| Implementation report | `docs/sprints/sprint-5a-us20-implementation-report.md` |
| Verification report | `docs/sprints/sprint-5a-us20-verification-report.md` |
| Olares acceptance | `evidence/us-20-verification/olares-2026-06-10/US-20-ACCEPTANCE-PACKAGE.md` |
| Local test evidence | `evidence/us-20-verification/local-2026-06-10/logs/` |
| Verify scripts | `deploy/k8s/us20-verify/` |
| Decision records | `DECISIONS.md` → **D-55**, **D-56** |
| US-22 brief (submitted) | `docs/sprints/sprint-5b-us22-brief.md` |

---

## 4. Verification summary

| Check | Result |
|---|---|
| GET /lineage on COMPLETED run | **PASS** (HTTP 200) |
| Display chain idea → video | **PASS** (8 nodes) |
| API vs SQL edge parity | **PASS** (18 = 18) |
| Synthetic IDEA (`synthetic: true`) | **PASS** |
| No IDEA→STORY edge in `edges[]` | **PASS** |
| V-20-L04 lineage row count unchanged | **PASS** (94 = 94) |
| Export regression (D-52..D-54) | **PASS** (HTTP 200) |
| C-01 no lineage writes / no schema change | **PASS** |
| Local regression: API 94 / web 26 | **PASS** |

**Olares pass run:** `042983f7-0f55-48c3-9d65-fce89a684625` · project `76aa4418-d92d-45f7-954c-a10383ea511a` · image `aimpos-api:us20`

---

## 5. Governance decision

| Item | Status |
|---|---|
| Implementation plan | **ACCEPT** |
| Olares verification | **PASS** |
| Governance closure | **ACCEPT** (2026-06-11) |
| **US-20** | **CLOSED** |

---

## 6. Project status

| Item | Status |
|---|---|
| **US-20** | **CLOSED** |
| **Spark Full Phase 2 frontier** | **US-22** — Asset History API |
| **M7 Phase 2** | In progress (US-20 ✅; US-22/23/21/V03 pending) |

US-22 implementation is **not authorized** until governance brief ACCEPT.

---

## 7. Release history (Spark Full + Visual MVP tags)

| Tag | Story | Commit (short) | Date |
|---|---|---|---|
| `v0.3.0-us12` | US-12 Workflow skeleton | — | 2026-06-09 |
| `v0.3.1-us13` | US-13 Story review | `4c01eba` | 2026-06-10 |
| `v0.3.2-us09` | US-09 Regenerate | `f80278d` | 2026-06-10 |
| `v0.3.3-us14` | US-14 Screenwriter | `db9370c` | 2026-06-10 |
| `v0.3.4-us15` | US-15 Script review | `7efd89c` | 2026-06-11 |
| `v0.3.5-us16` | US-16 Storyboard frames | `40116c9` | 2026-06-11 |
| `v0.3.6-us17` | US-17 Storyboard gallery review | `4604e5f` | 2026-06-11 |
| `v0.4.0-usv01` | US-V01 Visual MVP acceptance | `93214fc` | 2026-06-11 |
| `v0.5.0-us18` | US-18 Generate short video clip | `e764f5d` | 2026-06-11 |
| `v0.6.0-us19` | US-19 Export production bundle | `8caf81b` | 2026-06-11 |
| `v0.7.0-usv02` | US-V02 Spark Full acceptance | `905f1f1` | 2026-06-11 |
| **`v0.8.0-us20`** | **US-20 Lineage Viewer** | **`db54981`** | **2026-06-11** |

---

## 8. Push confirmation

*(Populated after push.)*

---

## 9. Next authorized planning

**US-22** Asset History API — governance brief at `docs/sprints/sprint-5b-us22-brief.md` (**SUBMITTED**). No implementation until brief ACCEPT.
