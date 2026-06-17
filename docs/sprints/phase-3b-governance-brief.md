# Phase 3B — Asset Intelligence & Creator Experience — Governance Brief

**Mission:** Improve creator usability, asset intelligence, and operational visibility without expanding workflow scope.

**Baseline:** Phase 3A CLOSED (US-V04 PASS, US-23b, WP-3 bootstrap)

## Work packages

| WP | Story | Deliverable |
|----|-------|-------------|
| WP-1 | Audit export | `GET /audit/export` CSV + JSON; UI download buttons |
| WP-2 | US-30 | Story/Script version diff (read-only, side-by-side) |
| WP-3 | US-31 | `GET /pipeline/runs` + dashboard run history |
| WP-4 | US-V04 UX | Inline video in History, auto-preview, version nav |
| WP-5 | PO findings | Clearer errors, status copy, video source labels |
| WP-6 | Ops hardening | Docs, verify scripts, evidence archive |

## Stop conditions (unchanged)

No schema change, no workflow semantic change, no new infrastructure.

## Decisions

- **D-66** — Audit export (WP-1)
- **D-67** — Version diff UI supersedes D-58 prohibition (WP-2)
- **D-68** — Pipeline run list read API (WP-3)
