# Phase 3D — Release Hardening & Distribution — Governance Brief

**Mission:** Transform AIMPOS from a working project into a repeatable, distributable, and supportable platform release.

**Baseline:** Phase 3C CLOSED  
**Status:** **AUTHORIZED**

## Work packages

| WP | Goal | Deliverables |
|----|------|--------------|
| WP-1 | Release engineering | Process, manifest, pinning, checklists, release notes |
| WP-2 | Olares distribution | Application package, install/upgrade/validation guides, dependency inventory |
| WP-3 | Deployment reliability | Drift detection, cluster consistency, version validation |
| WP-4 | Verification automation | `make verify-all`, CI integration, release verification bundle |
| WP-5 | US-V04 attestation | Evidence package, release history update |
| WP-6 | Operational runbooks | Install, upgrade, recovery, verification, Olares ops |

## Decisions (planned)

- **D-71** — Release manifest as image pin source of truth (WP-1)
- **D-72** — Consolidated `verify-all` entrypoint (WP-4)
- **D-73** — US-V04 release attestation package (WP-5)

## Stop conditions (unchanged)

No schema change, no workflow semantic change, no auth/security model change, no new infrastructure classes beyond release/distribution tooling.
