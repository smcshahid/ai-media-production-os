"""
Set branch protection on main + audit milestones for the AIMPOS repo.

Solo-founder friendly protection:
  - Require a PR before merging (0 approvals required - founder merges own PRs)
  - Block force-pushes and branch deletion on main
  - enforce_admins = False (founder keeps an escape hatch for hotfix/bootstrap)
  - No required status checks yet (added when CI lands in Sprint 0 T-01-04)

Also lists all milestones and flags empty/stale ones for manual review.

Token from GITHUB_TOKEN or GH_TOKEN env var (never stored in this file).

Usage (PowerShell):
  $env:GITHUB_TOKEN = "ghp_..."
  python backlog/protect_and_audit.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = "smcshahid/ai-media-production-os"
API = "https://api.github.com"
BRANCH = "main"

EXPECTED_MS = {
    "Sprint 0", "Sprint 1", "Sprint 2", "Sprint 3",
    "Sprint 4", "Sprint 5", "Future Release",
}


def request(token, method, path, body=None, query=None):
    url = f"{API}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aimpos-protect",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: set GITHUB_TOKEN or GH_TOKEN first.", file=sys.stderr)
        return 1

    print(f"Target: https://github.com/{REPO}\n")

    # --- Branch protection ---
    print(f"=== Branch protection: {BRANCH} ===")
    protection = {
        "required_status_checks": None,
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "required_approving_review_count": 0,
            "dismiss_stale_reviews": True,
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "required_linear_history": True,
    }
    try:
        request(token, "PUT",
                f"/repos/{REPO}/branches/{BRANCH}/protection", protection)
        print("  OK - main protected: PR required (0 approvals), "
              "no force-push, no deletion, linear history.")
    except urllib.error.HTTPError as e:
        print(f"  FAIL - HTTP {e.code}: {e.read().decode()[:200]}")

    # --- Milestone audit ---
    print("\n=== Milestone audit ===")
    milestones = request(token, "GET", f"/repos/{REPO}/milestones",
                         query={"state": "all", "per_page": 100}) or []
    for m in sorted(milestones, key=lambda x: x["number"]):
        flag = ""
        if m["title"] not in EXPECTED_MS:
            flag = "  <-- STALE (not in Sprint 0-5 / Future Release)"
        total = m["open_issues"] + m["closed_issues"]
        print(f"  #{m['number']:>2} {m['title']:<16} "
              f"state={m['state']:<6} issues={total}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
