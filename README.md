# AIMPOS-Spark Visual

Privacy-first, local-AI media production platform — **Visual MVP** scope: Idea → Story → Script → Storyboard.

## Status

**Architecture frozen** — June 9, 2026. Implementation begins at Sprint 0.

| State | Detail |
|-------|--------|
| Backlog | 68 GitHub issues (#1–#68) imported |
| Governance | Workflow, DoD, branching, coding standards in place |
| Application code | Not yet started — Sprint 0 next |

## Document authority (frozen)

| Priority | Document | Role |
|----------|----------|------|
| 1 | [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md) | Scope contract |
| 2 | [Architecture Freeze Review.md](./Architecture%20Freeze%20Review.md) | Freeze boundary |
| 3 | [Sprint Reclassification.md](./Sprint%20Reclassification.md) | Issue → sprint map |
| 4 | [Sprint 0 — Platform Skeleton.md](./Sprint%200%20%E2%80%94%20Platform%20Skeleton.md) | Sprint 0 execution |
| 5 | [GitHub Issues - Visual MVP.md](./GitHub%20Issues%20-%20Visual%20MVP.md) | 43 epics / features / stories |
| 6 | [docs/governance/](./docs/governance/) | Engineering workflow |

**Read-only references** (do not edit during Visual MVP): Blueprint, Business Capabilities, DDD, System Architecture, Workflow Architecture, Multi-Agent Architecture, Technology Recommendations, Enterprise Knowledge Graph.

**Archived** (do not use for execution): MVP Definition, MVP Backlog, GitHub Issues - Full MVP (Superseded), Solo Founder Development Plan.

## Sprint plan

| Sprint | Deliverable | Issues |
|--------|-------------|--------|
| **Sprint 0** | Platform Skeleton — Login, Project, Upload, Dashboard | 24 |
| **Sprint 1** | Infrastructure Validation — Olares, GPU smoke | 11 |
| **Sprint 2** | Workflow Foundation — Temporal skeleton | 6 |
| **Sprint 3** | Idea → Story | 7 |
| **Sprint 4** | Story → Script | 7 |
| **Sprint 5** | Script → Storyboard + sign-off | 9 |
| **Future Release** | Deferred (P1 cuts) | 2 |

See [Sprint Reclassification.md](./Sprint%20Reclassification.md) for full issue mapping.

## GitHub

- **Repository:** https://github.com/smcshahid/ai-media-production-os
- **Project board:** AI Media Production OS (AIMPOS)
- **Codename:** `AIMPOS-Spark-Visual`
- **First implementation issue:** T-02-02 (PostgreSQL init) or US-04 (database schema) — Sprint 0

### Backlog maintenance

```powershell
# One-time setup after gh auth login (no manual tokens)
.\scripts\setup-github.ps1

# Or verify anytime (uses gh keyring automatically)
python backlog/verify_github_token.py
python backlog/protect_and_audit.py
```

Do **not** re-run `import_to_github.py --all` unless resetting the repo — it creates duplicate issues.

Do **not** create new architecture documents in this planning repository. Changes require SCR per MVP Scope Freeze §11.

## Repository layout

See [Repository Structure.md](./Repository%20Structure.md) for the monorepo folder plan (scaffold in Sprint 0 Day 1).
