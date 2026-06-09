# AIMPOS-Spark Visual — Branching Strategy

**Document Type:** Engineering Governance  
**Version:** 1.0  
**Status:** FROZEN — Effective June 9, 2026  
**Date:** June 9, 2026  
**Product:** AIMPOS-Spark Visual

---

## Purpose

Define branch naming, lifetime, and merge rules for the `aimpos-spark` monorepo. Visual MVP uses **trunk-based development** on a single long-lived `main` branch.

**Related documents:**

- [development-workflow.md](./development-workflow.md)
- [definition-of-done.md](./definition-of-done.md)
- [Repository Structure.md](../../Repository%20Structure.md)

---

## Branches

| Branch | Role | Lifetime |
|--------|------|----------|
| **`main`** | Production-ready trunk; always deployable via `docker compose up` | Permanent |
| **`feature/*`** | Issue implementation | Delete after merge |
| **`fix/*`** | Bug fix or revert follow-up | Delete after merge |

**Not used in Visual MVP:** `develop`, `staging`, release branches, or environment branches.

---

## Branch Naming

```
feature/<task-id>-<short-slug>
fix/<task-id>-<short-slug>
```

| Segment | Rule | Example |
|---------|------|---------|
| `<task-id>` | GitHub task ID when available; otherwise user story ID | `T-02-01`, `US-07` |
| `<short-slug>` | Lowercase kebab-case, ≤ 4 words | `docker-compose`, `pipeline-start` |

**Examples:**

- `feature/T-02-01-docker-compose`
- `feature/US-07-pipeline-workflow`
- `fix/T-04-02-migration-rollback`

---

## Rules

### `main`

- Must pass applicable verification before merge (see [definition-of-done.md](./definition-of-done.md)).
- Must be deployable: `docker compose up` succeeds for the current sprint scope.
- Receives changes **only via pull request**, except bootstrap commits (below).

### Feature and fix branches

| Rule | Detail |
|------|--------|
| **Source** | Always branch from latest `main` |
| **Scope** | One issue per branch |
| **Lifetime** | Short-lived — hours to days, not weeks |
| **Sync** | Rebase or merge `main` before PR if trunk moved |
| **Cleanup** | Delete branch immediately after merge |

### Direct commits to `main`

Allowed **only** for repo bootstrap before application work begins:

- LICENSE, `.gitignore`
- Governance documents in `docs/governance/`
- Empty repo skeleton with no application logic

**After T-02-01 begins:** all application code, compose, migrations, and configs merge via PR.

---

## Pull Request Merge

| Rule | Detail |
|------|--------|
| **Target** | Always `main` |
| **Strategy** | Squash merge preferred (one commit per issue on trunk) |
| **Reviewer** | Self-review acceptable for solo execution |
| **Title** | `[<issue-id>] <description>` matching [development-workflow.md](./development-workflow.md) |

---

## Tags (Optional)

Milestone tags may be applied at sprint boundaries for demo snapshots:

```
sprint-s1-week2-gate
visual-mvp-signoff
```

Tags are optional. They do not replace issue closure or DoD verification.

---

## Hotfix Procedure

1. Branch from `main`: `fix/<task-id>-<slug>`
2. Fix with minimal diff — no unrelated changes
3. PR to `main` with DoD checklist
4. Verify regression smoke for affected area
5. Delete branch after merge

If a bad merge already landed on `main`, revert the merge commit on `main` via `fix/*` PR rather than force-pushing.

---

## Prohibited

| Action | Reason |
|--------|--------|
| Force push to `main` | Destroys audit trail; use revert PR |
| Long-lived feature branches | Conflicts with WIP = 1 and trunk-based flow |
| Branch per file or per commit | One issue per branch |
| Committing secrets | Use `.env` (gitignored) per `.env.example` |

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-09 | Initial branching strategy for Visual MVP |

*End of document*
