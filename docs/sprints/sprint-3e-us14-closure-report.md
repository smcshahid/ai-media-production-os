# US-14 Repository Closure Report

**Date:** 2026-06-10  
**Story:** US-14 — Generate one-scene script  
**Formal status:** **ACCEPTED**  
**Release tag:** `v0.3.3-us14`

---

## 1. Commits (US-14 closure)

| # | SHA (short) | Message |
|---|---|---|
| 1 | *(see git log)* | `feat(us14): Screenwriter agent, Fountain validator, and SCRIPT workflow swap` |
| 2 | *(see git log)* | `docs(us14): governance brief, plan, and implementation report` |
| 3 | *(see git log)* | `docs(us14): Olares verification package and acceptance evidence` |

---

## 2. Repository state

| Field | Value |
|---|---|
| **Branch** | `main` |
| **HEAD** | *(updated after push — see §6)* |
| **US-14 release tag** | `v0.3.3-us14` |
| **Prior baseline** | `v0.3.2-us09` (`f80278d`) |
| **Remote** | `origin/main` |
| **Working tree** | **Clean** (post-closure) |

---

## 3. Deliverables indexed

| Artifact | Path |
|---|---|
| Governance brief | `docs/sprints/sprint-3e-us14-brief.md` |
| Implementation plan | `docs/sprints/sprint-3e-us14-implementation-plan.md` |
| Implementation report | `docs/sprints/sprint-3e-us14-implementation-report.md` |
| Olares acceptance | `evidence/us-14-verification/olares-2026-06-10/US-14-ACCEPTANCE-PACKAGE.md` |
| Local test evidence | `evidence/us-14-verification/local-2026-06-10/logs/` |
| Verify scripts | `deploy/k8s/us14-verify/` |
| Decision records | `DECISIONS.md` → **D-39**, **D-40** |

---

## 4. Verification summary

| Check | Result |
|---|---|
| AC-1 One-scene Fountain script | **PASS** (Olares sample + D-40 unit tests) |
| AC-2 SCRIPT asset stored | **PASS** |
| AC-3 Fountain, `is_ai_generated=true` | **PASS** |
| AC-4 Lineage story → script | **PASS** |
| AC-5 Workflow to SCRIPT review gate | **PASS** |
| Constraint: no API changes | **PASS** |
| Constraint: no schema migrations | **PASS** |
| Constraint: no review UI | **PASS** |
| Regression: API 76 / worker 16 / web 14 | **PASS** |

**Olares run:** `ad45f3a7-e772-437b-be00-c62a9121cec1` · worker `aimpos-worker:us14`

---

## 5. Operational note

Workflow activity-type changes (`run_stub_stage` → `run_script_agent`) are **non-deterministic** for in-flight runs started under the old worker. Verification cancelled stale run `980617a8-…` before fresh E2E. Document in runbooks: redeploy worker only on **new** pipeline runs after SCRIPT agent swaps.

---

## 6. Next authorized planning

**US-15** script review UI is unblocked for **governance review only**.  
Governance brief: `docs/sprints/sprint-3f-us15-brief.md` — **not authorized until brief is accepted**.

US-16 (storyboard) remains blocked on US-15 + approved script contract.
