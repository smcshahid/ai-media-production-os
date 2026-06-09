"""
Reassign AIMPOS GitHub issues to Sprint 0-5 + Future Release milestones.

Source of truth: Sprint Reclassification.md (frozen).
Reads issue-id -> GitHub number from github-issue-mapping.json.
Token from GITHUB_TOKEN, GH_TOKEN, or `gh auth token` (keyring).

Usage:
  python backlog/reassign_milestones.py --dry-run
  python backlog/reassign_milestones.py
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

from github_auth import require_token

REPO = "smcshahid/ai-media-production-os"
API = "https://api.github.com"

# Milestone titles + descriptions (per Sprint Reclassification.md)
MILESTONES = {
    "Sprint 0": "Platform Skeleton - Login, Create Project, Upload Asset, View Dashboard",
    "Sprint 1": "Infrastructure Validation - full 9-service stack, Olares deploy, GPU smoke",
    "Sprint 2": "Workflow Foundation - Temporal skeleton, approve/reject, live dashboard",
    "Sprint 3": "Idea to Story - idea capture, Story Architect, story review",
    "Sprint 4": "Story to Script - Screenwriter, script review, audit viewer",
    "Sprint 5": "Script to Storyboard - ComfyUI frames, gallery, US-V01 sign-off",
    "Future Release": "Deferred / pre-approved cuts - not in Visual MVP critical path",
}

# issue-id -> milestone title (Sprint Reclassification.md)
ISSUE_SPRINT: dict[str, str] = {
    # Epics
    "EPIC-01": "Sprint 1", "EPIC-02": "Sprint 2", "EPIC-03": "Sprint 4",
    "EPIC-04": "Sprint 5", "EPIC-06": "Sprint 0",
    # Features
    "FEAT-INFRA": "Sprint 1", "FEAT-01": "Sprint 0", "FEAT-02": "Sprint 3",
    "FEAT-03": "Sprint 2", "FEAT-04": "Sprint 3", "FEAT-05": "Sprint 3",
    "FEAT-06": "Sprint 4", "FEAT-07": "Sprint 4", "FEAT-08": "Sprint 5",
    "FEAT-09": "Sprint 5", "FEAT-12": "Sprint 5", "FEAT-13": "Sprint 4",
    "FEAT-14": "Future Release", "FEAT-16": "Sprint 2",
    # User stories
    "US-01": "Sprint 0", "US-02": "Sprint 1", "US-03": "Sprint 0",
    "US-04": "Sprint 0", "US-05": "Sprint 0", "US-06": "Sprint 1",
    "US-07": "Sprint 2", "US-08": "Sprint 2", "US-09": "Sprint 3",
    "US-10": "Sprint 2", "US-11": "Sprint 3", "US-12": "Sprint 3",
    "US-13": "Sprint 3", "US-14": "Sprint 4", "US-15": "Sprint 4",
    "US-16": "Sprint 5", "US-17": "Sprint 5", "US-20": "Future Release",
    "US-22": "Sprint 5", "US-23": "Sprint 4", "US-24": "Sprint 5",
    "US-25": "Sprint 0", "US-26": "Sprint 0", "US-V01": "Sprint 5",
    # Tasks
    "T-02-01": "Sprint 1", "T-02-02": "Sprint 0", "T-02-03": "Sprint 0",
    "T-02-04": "Sprint 1", "T-02-05": "Sprint 1", "T-02-06": "Sprint 1",
    "T-04-01": "Sprint 0", "T-04-02": "Sprint 0", "T-04-03": "Sprint 0",
    "T-03-01": "Sprint 0", "T-03-02": "Sprint 0", "T-03-03": "Sprint 0",
    "T-05-01": "Sprint 0", "T-05-02": "Sprint 0", "T-05-03": "Sprint 0",
    "T-05-04": "Sprint 0", "T-06-01": "Sprint 1", "T-06-02": "Sprint 1",
    "T-06-03": "Sprint 1", "T-01-01": "Sprint 0", "T-01-02": "Sprint 0",
    "T-01-03": "Sprint 0", "T-01-04": "Sprint 0", "T-26-01": "Sprint 0",
    "T-26-02": "Sprint 0",
}


class GitHub:
    def __init__(self, token: str, dry_run: bool = False):
        self.token = token
        self.dry_run = dry_run

    def _request(self, method, path, body=None, query=None):
        url = f"{API}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "aimpos-reassign",
                "Content-Type": "application/json",
            },
        )
        if self.dry_run and method != "GET":
            print(f"  [dry-run] {method} {path} {body or ''}")
            return None
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None

    def paginate(self, path, query=None):
        items, page = [], 1
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

    def list_milestones(self):
        return self.paginate(f"/repos/{REPO}/milestones", {"state": "all"})

    def create_milestone(self, title, description):
        return self._request("POST", f"/repos/{REPO}/milestones",
                             {"title": title, "description": description})

    def update_milestone(self, number, description):
        return self._request("PATCH", f"/repos/{REPO}/milestones/{number}",
                             {"description": description})

    def set_issue_milestone(self, issue_number, milestone_number):
        return self._request("PATCH", f"/repos/{REPO}/issues/{issue_number}",
                             {"milestone": milestone_number})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = require_token()

    mapping_path = Path(__file__).parent / "github-issue-mapping.json"
    id_to_number: dict[str, int] = json.loads(mapping_path.read_text(encoding="utf-8"))

    gh = GitHub(token, dry_run=args.dry_run)
    print(f"Target: https://github.com/{REPO}\n")

    # --- Ensure milestones exist ---
    print("=== Milestones ===")
    existing = {m["title"]: m for m in gh.list_milestones()}
    title_to_number: dict[str, int] = {}
    for title, desc in MILESTONES.items():
        if title in existing:
            num = existing[title]["number"]
            title_to_number[title] = num
            print(f"  exists #{num}: {title}")
            if not args.dry_run:
                gh.update_milestone(num, desc)
        else:
            created = gh.create_milestone(title, desc)
            if created:
                title_to_number[title] = created["number"]
                print(f"  created #{created['number']}: {title}")
            else:
                print(f"  [dry-run] would create: {title}")

    # --- Reassign issues ---
    print("\n=== Issue reassignment ===")
    counts: dict[str, int] = {t: 0 for t in MILESTONES}
    missing, errors = [], []
    for issue_id, sprint in sorted(ISSUE_SPRINT.items()):
        number = id_to_number.get(issue_id)
        if number is None:
            missing.append(issue_id)
            continue
        ms_number = title_to_number.get(sprint)
        if ms_number is None and args.dry_run:
            print(f"  [dry-run] #{number} {issue_id} -> {sprint}")
            counts[sprint] += 1
            continue
        try:
            gh.set_issue_milestone(number, ms_number)
            counts[sprint] += 1
            print(f"  #{number} {issue_id} -> {sprint}")
            if not args.dry_run:
                time.sleep(0.2)
        except urllib.error.HTTPError as e:
            errors.append((issue_id, number, e.code, e.read().decode()[:120]))

    # --- Summary ---
    print("\n=== Summary ===")
    for title in MILESTONES:
        print(f"  {title}: {counts[title]} issues")
    print(f"  total assigned: {sum(counts.values())}")
    if missing:
        print(f"  MISSING from mapping: {missing}")
    if errors:
        print(f"  ERRORS: {errors}")
    if args.dry_run:
        print("\n(dry-run - no changes written)")
    else:
        print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
