"""
Clean up GitHub repo after Visual MVP import.

Actions:
  1. Close empty manual milestones M1–M5 (keep Sprint 1–4)
  2. Assign milestone to any open issues missing one
  3. Fix US-02 title typo (Olama → Olares) if present

Requires GITHUB_TOKEN, GH_TOKEN, or `gh auth login` with repo scope.

Usage:
  $env:GITHUB_TOKEN = "ghp_..."
  python backlog/cleanup_github.py
  python backlog/cleanup_github.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from github_auth import resolve_token, require_token

REPO = "smcshahid/ai-media-production-os"
API = "https://api.github.com"

# Manual architectural milestones to close (empty duplicates of frozen docs)
CLOSE_MILESTONE_PREFIXES = ("M1 -", "M2 -", "M3 -", "M4 -", "M5 -")

KEEP_MILESTONES = {"Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4"}

# Issue number → milestone title for known gaps
MILESTONE_FIXES: dict[int, str] = {
    37: "Sprint 4",  # FEAT-14 — Lineage Summary
    40: "Sprint 4",  # US-20 — View asset lineage chain
    42: "Sprint 1",  # EPIC-06 — cross-cutting, spans sprints
    43: "Sprint 4",  # US-V01 — Visual MVP sign-off
}

US02_NUMBER = 3
US02_TITLE = "[US-02] Deploy MVP stack on Olares"


class GitHub:
    def __init__(self, token: str, dry_run: bool = False):
        self.token = token
        self.dry_run = dry_run

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        query: dict | None = None,
    ) -> dict | list | None:
        url = f"{API}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "aimpos-cleanup",
                "Content-Type": "application/json",
            },
        )
        if self.dry_run and method != "GET":
            print(f"  [dry-run] {method} {path} {body or ''}")
            return None
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            raise RuntimeError(f"GitHub API {method} {path} ({e.code}): {err}") from e

    def paginate(self, path: str, query: dict | None = None) -> list:
        items: list = []
        page = 1
        while True:
            q = {"per_page": 100, "page": page, **(query or {})}
            batch = self._request("GET", path, query=q) or []
            if not batch:
                break
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return items

    def list_milestones(self) -> list[dict]:
        return self.paginate(f"/repos/{REPO}/milestones", {"state": "all"})

    def close_milestone(self, number: int, title: str) -> None:
        self._request("PATCH", f"/repos/{REPO}/milestones/{number}", {"state": "closed"})
        print(f"  closed milestone #{number}: {title}")

    def list_open_issues(self) -> list[dict]:
        return self.paginate(f"/repos/{REPO}/issues", {"state": "open"})

    def set_issue_milestone(self, issue_number: int, milestone_number: int, title: str) -> None:
        self._request(
            "PATCH",
            f"/repos/{REPO}/issues/{issue_number}",
            {"milestone": milestone_number},
        )
        print(f"  issue #{issue_number} → milestone {title!r}")

    def update_issue_title(self, issue_number: int, title: str) -> None:
        self._request("PATCH", f"/repos/{REPO}/issues/{issue_number}", {"title": title})
        print(f"  issue #{issue_number} title → {title!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean up AIMPOS GitHub milestones and issues")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    args = parser.parse_args()

    token = resolve_token()
    token_file = Path(__file__).parent / ".github-token"
    if not token and token_file.exists():
        token = token_file.read_text(encoding="utf-8").strip()
    if not token:
        require_token()
        return 1

    gh = GitHub(token, dry_run=args.dry_run)
    print(f"Target: https://github.com/{REPO}\n")

    # --- Milestones ---
    print("=== Milestones ===")
    milestones = gh.list_milestones()
    open_ms = [m for m in milestones if m["state"] == "open"]
    by_title = {m["title"]: m for m in milestones}

    for m in open_ms:
        title = m["title"]
        if title in KEEP_MILESTONES:
            print(f"  keep #{m['number']}: {title} ({m['open_issues']} open issues)")
            continue
        if any(title.startswith(p) for p in CLOSE_MILESTONE_PREFIXES):
            if m["open_issues"] == 0:
                gh.close_milestone(m["number"], title)
                if not args.dry_run:
                    time.sleep(0.3)
            else:
                print(f"  SKIP close #{m['number']}: {title} — has {m['open_issues']} issues")
            continue
        print(f"  unknown open milestone #{m['number']}: {title} ({m['open_issues']} issues) — review manually")

    # --- Issues without milestone ---
    print("\n=== Issues missing milestone ===")
    issues = gh.list_open_issues()
    # GitHub returns pull requests in issues API — filter
    issues = [i for i in issues if "pull_request" not in i]
    no_ms = [i for i in issues if i.get("milestone") is None]
    print(f"  open issues: {len(issues)}, without milestone: {len(no_ms)}")

    sprint_ids = {t: by_title[t]["number"] for t in KEEP_MILESTONES if t in by_title}

    for issue in no_ms:
        num = issue["number"]
        fix_title = MILESTONE_FIXES.get(num)
        if fix_title and fix_title in sprint_ids:
            gh.set_issue_milestone(num, sprint_ids[fix_title], fix_title)
            if not args.dry_run:
                time.sleep(0.3)
        else:
            print(f"  manual review needed: #{num} {issue['title'][:60]}")

    # Apply explicit milestone fixes even when milestone is wrong (optional re-run)
    for num, fix_title in MILESTONE_FIXES.items():
        if fix_title not in sprint_ids:
            continue
        issue = next((i for i in issues if i["number"] == num), None)
        if not issue:
            continue
        current = (issue.get("milestone") or {}).get("title")
        if current != fix_title:
            gh.set_issue_milestone(num, sprint_ids[fix_title], fix_title)
            if not args.dry_run:
                time.sleep(0.3)

    # --- US-02 title ---
    print("\n=== Title fixes ===")
    us02 = next((i for i in issues if i["number"] == US02_NUMBER), None)
    if us02:
        current = us02["title"]
        if "Olama" in current or current != US02_TITLE:
            if args.dry_run:
                print(f"  [dry-run] would rename #{US02_NUMBER}: {current!r} → {US02_TITLE!r}")
            else:
                gh.update_issue_title(US02_NUMBER, US02_TITLE)
        else:
            print(f"  #{US02_NUMBER} title OK: {current!r}")
    else:
        print(f"  issue #{US02_NUMBER} not found")

    # --- Summary ---
    print("\n=== Summary ===")
    milestones_after = gh.list_milestones()
    open_after = [m for m in milestones_after if m["state"] == "open"]
    sprint_issues = sum(m["open_issues"] for m in open_after if m["title"] in KEEP_MILESTONES)
    print(f"  open milestones: {len(open_after)}")
    for m in open_after:
        print(f"    #{m['number']} {m['title']}: {m['open_issues']} issues")
    print(f"  sprint milestone issue total: {sprint_issues}")
    print(f"  open issues: {len(issues)}")
    if args.dry_run:
        print("\n(dry-run — no changes written)")
    else:
        print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
