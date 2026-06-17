# Phase 3A — Trust & Visibility (governance brief)

**Status:** **AUTHORIZED** — Phase 3A mission  
**Date:** 2026-06-16  
**Baseline:** `v0.12.0-usv03` (M7 closed)

## Objective

Increase trust, observability, and operational readiness **without expanding pipeline scope**.

## Authorized work packages

| WP | Story | Deliverable |
|----|-------|-------------|
| WP-1 | US-V04 | Flux storyboard + WAN i2v re-acceptance evidence |
| WP-2 | US-23b | `GET /audit` + Audit UI (D-64) |
| WP-3 | WP-3 | `ensure-db-migrated.ps1` in `make up-dev` (D-65) |

## Forbidden (mission constraints)

Multi-scene, character bible, audio, multi-project, Keycloak, asset restore/rollback/promote, workflow/schema redesign, new infrastructure.

## Decision records

- **D-64** — Audit trail API + UI  
- **D-65** — Dev bootstrap migration gate

## Exit criteria

- US-V04: worker Flux + i2v env; 4-frame storyboard batch; audit regression PASS  
- US-23b: audit API/SQL parity; UI route live  
- WP-3: fresh bootstrap applies 0003 + partial indexes
