# US-V08B Character Bible Hardening — Acceptance Package

**Date:** 2026-06-18  
**Mission:** Phase 7.5 — Character Bible Consolidation & Production Hardening  
**Baseline:** `v0.17.0-phase7-character-bible`  
**Release:** `v0.17.1-phase7-character-hardening`  
**Governance decision:** **US-V08B ACCEPTED**  
**Release:** `v0.17.1-phase7-character-hardening` · **Phase 7.5 CLOSED**

---

## Executive summary

| Path | Scope | Primary E2E | Final | Authoritative run | Evidence |
|------|-------|-------------|-------|-------------------|----------|
| **A** | 1 character, 1 scene, snapshot + v5 | **PASS** | **PASS** | `adf931ba-…` ep **56** | `path-A/` |
| **B** | 3 characters, 3 scenes | **PASS** | **PASS** | `959ab565-…` ep **57** | `path-B/` |
| **C** | Cross-episode (C1+C2) | **PASS** | **PASS** | `19aa82c2-…` ep **58**, `67d00c52-…` ep **59** | `path-C1/`, `path-C2/` |
| **D** | Edit lifecycle (snapshot isolation) | FAIL (verify + PATCH bug) | **PASS** (supplement) | run1 `a6894d3e-…`, run2 `cf274c65-…` | `path-D*` |
| **E** | Delete after export | FAIL (blocked by D) | **PASS** (supplement) | `cf274c65-…` | `path-E-*` |
| **F** | Regression + v2/v3 ladder | **PASS** | **PASS** | ref `adf931ba-…` | `path-F-*` |
| **Local** | pytest/vitest | **PASS** | **PASS** | FAIL=0 | `local-2026-06-18/logs/` |
| **Deploy** | Alembic **0007**, `usv08b-phase75` images | **PASS** | **PASS** | Alembic 0007 | `logs/migration-0007.log` |

**Final matrix:** All paths **PASS**. Primary E2E reported FAIL=1 for PATH D/E due to verification script manifest path bug and PATCH 500 (async `updated_at`); both remediated; supplemental attestation **PASS**.

---

## Olares authoritative runs

| Path | Run ID | Episode | Snapshot |
|------|--------|---------|----------|
| A | `adf931ba-b63e-4fb1-aa19-cbe8b432d7b3` | 56 | count=1 |
| B | `959ab565-2336-405d-9fe5-8110325a1a8d` | 57 | count=3 |
| C1 | `19aa82c2-18e7-44b6-b022-f70cf7b4d152` | 58 | count=3 |
| C2 | `67d00c52-3446-4d42-bc28-8a1b7f90fad4` | 59 | count=3 |
| D run1 | `a6894d3e-df8e-412b-9e13-73add88060c2` | 62 | `Maya-D-a1` |
| D run2 | `cf274c65-ecf5-4c56-9f8b-6b5bbb88a15f` | 63 | `Maya-D-a1-Edited` |
| E | `cf274c65-ecf5-4c56-9f8b-6b5bbb88a15f` | 63 | unchanged after char delete |

Evidence root: `evidence/us-v08b-verification/olares-2026-06-18/`

---

## Defects closed during acceptance

| ID | Sev | Issue | Resolution |
|----|-----|-------|------------|
| TD-P7-01 | SEV-3 | Export depended on live character rows | `character_snapshot` at pipeline start (D-93) |
| BUG-P75-01 | SEV-2 | PATCH `/characters` returned 500 | Explicit `updated_at` before flush |
| V-P75-01 | SEV-3 | PATH D verify re-export empty manifest | Compare `path-D1/D2-manifest.json` from verify step |
| OPS-P75-01 | SEV-3 | Olares rollout did not refresh pod image | Force pod delete after `set image` |

---

## Supplemental attestation (PATH D/E)

Primary E2E log: `logs/e2e-olares.log` (FAIL=1 at PATH D compare).  
Supplement scripts: `deploy/k8s/usv08b-verify/run_path_d_olares.sh`, `run_path_e_olares.sh`.

---

## Governance

- **D-93** Export-time character snapshot  
- **D-94** Governed character delete  
- **D-95** Character UX completion  

No governance stop conditions triggered.

---

## Sign-off

| Role | Status | Date |
|------|--------|------|
| Verification Lead | **US-V08B ACCEPTED** | 2026-06-18 |
| Release Manager | **GO — v0.17.1 cut** | 2026-06-18 |
| Governance | **Phase 7.5 AUTHORIZED** | 2026-06-18 |
