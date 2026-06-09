"""
Import AIMPOS-Spark Visual MVP backlog into GitHub Issues.

Requires GITHUB_TOKEN or GH_TOKEN with repo scope for smcshahid/ai-media-production-os.

Usage:
  python backlog/import_to_github.py --dry-run
  python backlog/import_to_github.py --parents
  python backlog/import_to_github.py --tasks
  python backlog/import_to_github.py --all
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Reuse Visual MVP issue definitions
sys.path.insert(0, str(Path(__file__).parent))
from generate_github_issues_visual_mvp import (  # noqa: E402
    FLAT_ORDER,
    INCLUDED_IDS,
    issue_body,
    load_backlog,
    load_blocks,
    load_tasks,
)
from github_auth import resolve_token, require_token  # noqa: E402

ROOT = Path(__file__).parent.parent
TASKS_CSV = Path(__file__).parent / "github-issues-tasks-01-25.csv"
REPO = "smcshahid/ai-media-production-os"
API = "https://api.github.com"

MILESTONES = {
    "Sprint 1": "Weeks 1–2: Platform running on Olares",
    "Sprint 2": "Weeks 3–4: 4-stage workflow + dashboard",
    "Sprint 3": "Weeks 5–6: Idea → approved script",
    "Sprint 4": "Weeks 7–8: Storyboard + lineage + Visual MVP sign-off",
}

SPRINT_TO_MILESTONE = {
    "S1": "Sprint 1",
    "S2": "Sprint 2",
    "S3": "Sprint 3",
    "S4": "Sprint 4",
    "S1-S5": "Sprint 1",
}

LABEL_COLORS = {
    "aimpos-spark": "1D76DB",
    "visual-mvp": "0E8A16",
    "epic": "5319E7",
    "feature": "1D76DB",
    "user-story": "0075CA",
    "task": "FBCA04",
    "priority:p0": "B60205",
    "priority:p1": "D93F0B",
    "sprint:s1": "C5DEF5",
    "sprint:s2": "BFD4F2",
    "sprint:s3": "BFDADC",
    "sprint:s4": "C2E0C6",
    "devops": "006B75",
    "backend": "0052CC",
    "frontend": "E99695",
    "ai": "7057FF",
    "docs": "FEF2C0",
    "test": "EDEDED",
    "qa": "F9D0C4",
    "foundation": "D4C5F9",
    "infrastructure": "C2E0C6",
    "governance": "FBCA04",
}


class GitHubClient:
    def __init__(self, token: str, dry_run: bool = False):
        self.token = token
        self.dry_run = dry_run
        self._milestone_ids: dict[str, int] = {}
        self._issue_numbers: dict[str, int] = {}

    def _request(self, method: str, path: str, body: dict | None = None) -> dict | list | None:
        url = f"{API}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "aimpos-spark-import",
                "Content-Type": "application/json",
            },
        )
        if self.dry_run:
            if method == "GET":
                return []
            print(f"  [dry-run] {method} {path}")
            if body:
                preview = {k: (v[:80] + "…" if isinstance(v, str) and len(v) > 80 else v) for k, v in body.items()}
                print(f"            {json.dumps(preview, indent=2)}")
            fake_num = len(self._issue_numbers) + 1
            if path.endswith("/milestones") and method == "POST" and body:
                self._milestone_ids[body["title"]] = fake_num
            return {"number": fake_num, "title": body.get("title", "") if body else ""}

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            raise RuntimeError(f"GitHub API {method} {path} failed ({e.code}): {err}") from e

    def ensure_milestones(self) -> None:
        existing = self._request("GET", f"/repos/{REPO}/milestones?state=all&per_page=100") or []
        by_title = {m["title"]: m for m in existing} if existing else {}
        for title, desc in MILESTONES.items():
            if title in by_title:
                self._milestone_ids[title] = by_title[title]["number"]
                print(f"  milestone exists: {title} (#{by_title[title]['number']})")
            elif title in self._milestone_ids:
                print(f"  [dry-run] milestone: {title}")
            else:
                m = self._request("POST", f"/repos/{REPO}/milestones", {"title": title, "description": desc})
                self._milestone_ids[title] = m["number"]
                print(f"  created milestone: {title} (#{m['number']})")
                if not self.dry_run:
                    time.sleep(0.3)

    def ensure_labels(self, labels: set[str]) -> None:
        existing = self._request("GET", f"/repos/{REPO}/labels?per_page=100") or []
        have = {l["name"] for l in existing}
        for name in sorted(labels):
            if name in have:
                continue
            color = LABEL_COLORS.get(name, "BFDADC")
            self._request("POST", f"/repos/{REPO}/labels", {"name": name, "color": color})
            print(f"  created label: {name}")
            if not self.dry_run:
                time.sleep(0.2)

    def create_issue(
        self,
        external_id: str,
        title: str,
        body: str,
        labels: list[str],
        milestone: str | None,
    ) -> int:
        payload: dict = {"title": title, "body": body, "labels": labels}
        if milestone and milestone in self._milestone_ids:
            payload["milestone"] = self._milestone_ids[milestone]

        result = self._request("POST", f"/repos/{REPO}/issues", payload)
        number = result["number"]
        self._issue_numbers[external_id] = number
        print(f"  #{number} [{external_id}] {title}")
        time.sleep(0.5)
        return number

    def save_mapping(self, path: Path) -> None:
        path.write_text(json.dumps(self._issue_numbers, indent=2), encoding="utf-8")


def parent_title(item: dict) -> str:
    return f"[{item['ID']}] {item['Title']}"


def parent_labels(item: dict) -> list[str]:
    wtype = item["Work Item Type"].lower().replace(" ", "-")
    labels = ["aimpos-spark", "visual-mvp", wtype, f"priority:{item['Priority'].lower()}"]
    sprint = item.get("Sprint", "")
    if sprint and sprint != "S1-S5":
        labels.append(f"sprint:{sprint.lower()}")
    if item.get("Epic ID"):
        labels.append(f"epic:{item['Epic ID']}")
    if item.get("Feature ID"):
        labels.append(f"feature:{item['Feature ID']}")
    for part in item.get("Labels", "").split(";"):
        part = part.strip()
        if part:
            labels.append(part)
    return list(dict.fromkeys(labels))


def task_body(row: dict, parent_issue_num: int | None) -> str:
    deps = row.get("Dependencies", "None")
    ac = row.get("Acceptance Criteria", "")
    ac_lines = "\n".join(f"- [ ] {p.strip()}" for p in ac.split(";") if p.strip())
    parent_ref = f"#{parent_issue_num}" if parent_issue_num else f"#{row['Parent Story']}"
    return "\n".join(
        [
            f"**Task ID:** `{row['Issue ID']}`",
            f"**Parent story:** {row['Parent Story']} ({parent_ref})",
            f"**Epic:** {row['Epic']} · **Feature:** {row['Feature']}",
            f"**Implementation order:** {row['Implementation Order']}",
            "",
            "## Description",
            row["Description"],
            "",
            "## Dependencies",
            deps if deps and deps != "None" else "_None._",
            "",
            "## Acceptance Criteria",
            ac_lines or "_See parent story._",
            "",
            "## Definition of Done",
            "- [ ] Code merged to main",
            "- [ ] AC verified locally on Olares stack",
            "- [ ] Parent story checklist updated",
        ]
    )


def collect_all_labels(by_id: dict, task_rows: list[dict]) -> set[str]:
    labels: set[str] = set(LABEL_COLORS)
    for iid in FLAT_ORDER:
        labels.update(parent_labels(by_id[iid]))
    for row in task_rows:
        labels.update(l.strip() for l in row["Labels"].split(",") if l.strip())
    return labels


def import_parents(client: GitHubClient, by_id: dict, blocks, tasks) -> None:
    print("\n=== Parent issues (43 epics / features / stories) ===")
    for idx, iid in enumerate(FLAT_ORDER, 1):
        item = by_id[iid]
        title = parent_title(item)
        body = issue_body(item, idx, blocks, tasks)
        sprint = item.get("Sprint", "S1")
        milestone = SPRINT_TO_MILESTONE.get(sprint)
        client.create_issue(iid, title, body, parent_labels(item), milestone)


def import_tasks(client: GitHubClient) -> None:
    print("\n=== Task issues (01–25) ===")
    with open(TASKS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        labels = [l.strip() for l in row["Labels"].split(",") if l.strip()]
        parent_num = client._issue_numbers.get(row["Parent Story"])
        body = task_body(row, parent_num)
        client.create_issue(
            row["Issue ID"],
            row["Title"],
            body,
            labels,
            row["Milestone"],
        )


def validate() -> dict:
    """Return gap analysis vs frozen Visual MVP scope."""
    by_id = load_backlog()
    with open(TASKS_CSV, encoding="utf-8") as f:
        task_rows = list(csv.DictReader(f))

    all_tasks = []
    with open(Path(__file__).parent / "aimpos-spark-backlog.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Work Item Type"] == "Task" and row["Parent ID"] in INCLUDED_IDS:
                all_tasks.append(row["ID"])

    imported_task_ids = {r["Issue ID"] for r in task_rows}
    missing_tasks = [t for t in all_tasks if t not in imported_task_ids]

    return {
        "repo": f"https://github.com/{REPO}",
        "parent_issues_ready": len(FLAT_ORDER),
        "tasks_ready_csv": len(task_rows),
        "total_visual_mvp_tasks_in_backlog": len(all_tasks),
        "tasks_not_yet_in_github_csv": len(missing_tasks),
        "missing_task_ids_sample": missing_tasks[:10],
        "milestones_needed": list(MILESTONES.keys()),
        "excluded_from_visual_mvp": ["EPIC-05", "FEAT-10", "FEAT-11", "FEAT-15", "US-18", "US-19", "US-21", "US-27"],
        "github_repo_has_issues": "check via gh issue list after import",
        "local_git_initialized": (ROOT / ".git").exists(),
        "auth_required": "GITHUB_TOKEN or gh auth login",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import AIMPOS-Spark issues to GitHub")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API writes")
    parser.add_argument("--parents", action="store_true", help="Import 43 parent issues")
    parser.add_argument("--tasks", action="store_true", help="Import 25 task issues")
    parser.add_argument("--all", action="store_true", help="Import parents then tasks")
    parser.add_argument("--validate", action="store_true", help="Print gap analysis only")
    args = parser.parse_args()

    if args.validate or (not args.parents and not args.tasks and not args.all and not args.dry_run):
        report = validate()
        print(json.dumps(report, indent=2))
        if not args.validate:
            print("\nRun with --dry-run, --parents, --tasks, or --all after setting GITHUB_TOKEN.")
        return 0

    token = resolve_token()
    if not token and not args.dry_run:
        require_token()  # prints helpful message and exits
        return 1

    do_parents = args.parents or args.all
    do_tasks = args.tasks or args.all
    if args.dry_run and not do_parents and not do_tasks:
        do_parents = do_tasks = True

    by_id = load_backlog()
    blocks = load_blocks()
    tasks = load_tasks()
    with open(TASKS_CSV, encoding="utf-8") as f:
        task_rows = list(csv.DictReader(f))

    client = GitHubClient(token or "dry-run-token", dry_run=args.dry_run)
    print(f"Target: https://github.com/{REPO}")
    print("Ensuring milestones and labels…")
    client.ensure_milestones()
    client.ensure_labels(collect_all_labels(by_id, task_rows))

    if do_parents:
        import_parents(client, by_id, blocks, tasks)
    if do_tasks:
        if do_parents and not args.dry_run:
            print("  (tasks reference parent issue numbers from this run)")
        import_tasks(client)

    mapping_path = Path(__file__).parent / "github-issue-mapping.json"
    if not args.dry_run:
        client.save_mapping(mapping_path)
        print(f"\nSaved issue mapping → {mapping_path}")

    print("\n=== Validation summary ===")
    print(json.dumps(validate(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
