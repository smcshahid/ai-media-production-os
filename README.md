# AIMPOS-Spark Visual

Privacy-first, local-AI media production platform — **Visual MVP** scope: Idea → Story → Script → Storyboard.

## Status

Planning and backlog phase. Application code not yet started.

| Document | Purpose |
|----------|---------|
| [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md) | Frozen scope contract |
| [GitHub Issues - Visual MVP.md](./GitHub%20Issues%20-%20Visual%20MVP.md) | 43 epics / features / stories |
| [GitHub Issues - Tasks 01-25.md](./GitHub%20Issues%20-%20Tasks%2001-25.md) | First 25 implementation tasks |
| [Solo Founder Development Plan.md](./Solo%20Founder%20Development%20Plan.md) | Sprint schedule |

## Import backlog to GitHub

```powershell
# 1. Authenticate (one-time)
gh auth login

# 2. Set token for the import script
$env:GITHUB_TOKEN = gh auth token

# 3. Preview
python backlog/import_to_github.py --dry-run

# 4. Import all 68 issues (43 parents + 25 tasks)
python backlog/import_to_github.py --all
```

## Repository

- **GitHub:** https://github.com/smcshahid/ai-media-production-os
- **Codename:** `AIMPOS-Spark-Visual`
