"""Generate GitHub Issues markdown from AIMPOS-Spark backlog."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKLOG = Path(__file__).parent / "aimpos-spark-backlog.csv"
DEPS = Path(__file__).parent / "aimpos-spark-dependencies.csv"
OUT = ROOT / "GitHub Issues.md"

# Business value by feature/epic
BV = {
    "EPIC-01": "Enables sovereign local-AI production on Olares. Without a runnable stack, no MVP capability can be demonstrated. De-risks GPU and ComfyUI early (week 2 kill criterion).",
    "EPIC-02": "Proves workflow-driven production with human-in-the-loop gates — the core AIMPOS architectural principle. Unblocks all five pipeline stages and SC-03, SC-06.",
    "EPIC-03": "Delivers the text half of the creative pipeline (Idea → Story → Script). Validates LangGraph agents, Ollama inference, and first three approval gates.",
    "EPIC-04": "Proves local visual AI via ComfyUI. Transforms approved script into reviewable storyboard frames — prerequisite for video.",
    "EPIC-05": "Completes the MVP promise: Idea to approved short video with export. Satisfies SC-01 (end-to-end run) and stakeholder demo.",
    "EPIC-06": "Provides trust, traceability, and usability across the pipeline. Supports SC-04 (versioning), SC-05 (audit), SC-08 (comprehension).",
    "F-01": "Removes setup friction for solo creator; one-click start to production.",
    "F-INFRA": "Foundation for all persistence, assets, and AI runtimes. Investment here prevents 1–2 weeks rework later.",
    "F-02": "Captures creative intent as first versioned asset; root of lineage chain.",
    "F-03": "Single action starts governed production; replaces ad-hoc scripts with Temporal control.",
    "F-04": "First AI value moment — treatment from idea in <5 min (SC-07).",
    "F-05": "Human creative control over AI story output; enforces approval gate.",
    "F-06": "Produces shootable screenplay for one scene; bridges narrative to visual production.",
    "F-07": "Final text gate before GPU-intensive visual work begins.",
    "F-08": "Visualizes scene before video; highest ComfyUI image risk isolated here.",
    "F-09": "Creator controls which frames proceed; prevents bad visuals propagating to video.",
    "F-10": "MVP climax — motion video from local AI. Proves full media pipeline.",
    "F-11": "Human sign-off completes production; triggers export and SC-01.",
    "F-12": "Transparency into AI drafts vs human edits; supports regenerate workflow.",
    "F-13": "Verifiable audit trail for model usage and approvals (SC-05).",
    "F-14": "Shows derivation chain idea→video without Neo4j; builds trust in AI outputs.",
    "F-15": "Archivable deliverable with integrity hashes (SC-11); demo step 10.",
    "F-16": "Creator always knows pipeline state and next action (SC-08).",
}

STORY_BV = {
    "US-01": "Creator opens app and immediately has a project — zero onboarding.",
    "US-02": "Team can develop and demo on Olares with one command.",
    "US-03": "Fast diagnosis of integration failures; ops readiness.",
    "US-04": "Single source of truth for pipeline, assets, audit — architectural requirement.",
    "US-05": "Content-addressable assets enable versioning, export hashes, deduplication.",
    "US-06": "Validates GPU path before agent sprints; avoids late MVP kill.",
    "US-07": "Pipeline automation begins; core workflow value delivered.",
    "US-08": "Human-in-the-loop enforced — agents cannot bypass creator (SC-03).",
    "US-09": "Improves AI output quality without pipeline restart (SC-10).",
    "US-10": "Reduces creator confusion; shows progress and required actions.",
    "US-11": "Production starts from creator's own idea — MVP entry point.",
    "US-12": "First AI-generated creative asset; proves local LLM story capability.",
    "US-13": "Creator refines treatment before scripting — quality gate.",
    "US-14": "Automates screenplay draft; saves hours of manual writing.",
    "US-15": "Locks script before expensive GPU storyboard work.",
    "US-16": "Generates visual plan locally; core differentiator vs cloud tools.",
    "US-17": "Creator curates visuals; maintains creative control.",
    "US-18": "Delivers final media artifact — MVP primary outcome.",
    "US-19": "Formal completion and audit closure of production run.",
    "US-20": "Explains how each asset was derived; regulatory/trust readiness.",
    "US-21": "Portable production package for archive and sharing.",
    "US-22": "Compare AI drafts, edits, and approvals across stages.",
    "US-23": "Full transparency of what AI did and when (SC-05).",
    "US-24": "Long GPU jobs survive restarts — creator confidence (SC-06).",
    "US-25": "Basic LAN security for lab deployment.",
    "US-26": "Unified UX across five screens; SC-08 comprehension.",
    "US-27": "Objective MVP readiness proof for stakeholders.",
}

COMPLEXITY_SP = {"2": "Low", "3": "Low", "5": "Medium", "8": "High", "": "Medium"}
IMPL_ORDER = {
    "US-02": 1, "US-04": 2, "US-03": 3, "US-05": 4, "US-06": 5, "US-01": 6,
    "US-26": 7, "US-07": 8, "US-08": 9, "US-09": 10, "US-24": 11, "US-25": 12,
    "US-10": 13, "US-11": 14, "US-12": 15, "US-13": 16, "US-14": 17, "US-15": 18,
    "US-23": 19, "US-16": 20, "US-17": 21, "US-22": 22, "US-18": 23, "US-19": 24,
    "US-20": 25, "US-21": 26, "US-27": 27,
}

DOD_EPIC = """- [ ] All child features and P0 user stories closed
- [ ] Epic acceptance criteria verified on Olares hardware
- [ ] No P0 defects open against this epic
- [ ] Documented in sprint review / release notes"""

DOD_FEATURE = """- [ ] All child user stories closed
- [ ] Feature traced to MVP feature ID (F-xx) in release notes
- [ ] Integration tested with upstream dependencies
- [ ] Product Owner acceptance"""

DOD_STORY = """- [ ] All implementation tasks complete (see checklist)
- [ ] Acceptance criteria verified manually or via test
- [ ] Code merged to main branch
- [ ] No regression on dependent stories
- [ ] Documented if API contract changed"""


def load_backlog():
    items = []
    with open(BACKLOG, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append(row)
    return items


def load_deps():
    blocks = defaultdict(list)  # target -> list of sources that block it
    with open(DEPS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Dependency Type"] in ("Blocks", "Requires"):
                blocks[row["Target ID"]].append(row["Source ID"])
    return blocks


def load_tasks(items):
    tasks = defaultdict(list)
    for i in items:
        if i["Work Item Type"] == "Task":
            tasks[i["Parent ID"]].append((i["ID"], i["Title"]))
    return tasks


def fmt_ac(ac_text, item_type):
    if not ac_text:
        return "_See child user stories._"
    parts = [p.strip() for p in ac_text.replace("\n", " ").split(".") if p.strip()]
    return "\n".join(f"- [ ] {p}" for p in parts)


FEATURE_EXTRA_DEPS = {
    "FEAT-01": ["FEAT-INFRA"],
    "FEAT-03": ["FEAT-INFRA", "FEAT-01"],
    "FEAT-16": ["FEAT-INFRA", "FEAT-03"],
    "FEAT-02": ["FEAT-01", "FEAT-03", "FEAT-16"],
    "FEAT-04": ["FEAT-02", "FEAT-03"],
    "FEAT-05": ["FEAT-04", "FEAT-03"],
    "FEAT-06": ["FEAT-05"],
    "FEAT-07": ["FEAT-06"],
    "FEAT-08": ["FEAT-07"],
    "FEAT-09": ["FEAT-08"],
    "FEAT-10": ["FEAT-09"],
    "FEAT-11": ["FEAT-10"],
    "FEAT-14": ["FEAT-11"],
    "FEAT-15": ["FEAT-11"],
    "FEAT-12": ["FEAT-INFRA"],
    "FEAT-13": ["FEAT-03"],
}

EPIC_DEPS = {
    "EPIC-02": ["EPIC-01"],
    "EPIC-03": ["EPIC-01", "EPIC-02"],
    "EPIC-04": ["EPIC-03"],
    "EPIC-05": ["EPIC-04"],
    "EPIC-06": ["EPIC-01"],
}


def fmt_deps(item_id, blocks, item_type, parent, epic):
    deps = sorted(set(blocks.get(item_id, [])))
    if item_type == "Epic":
        for d in EPIC_DEPS.get(item_id, []):
            if d not in deps:
                deps.insert(0, d)
    if item_type == "Feature":
        for d in FEATURE_EXTRA_DEPS.get(item_id, []):
            if d not in deps:
                deps.append(d)
        if parent and parent not in deps:
            deps.insert(0, parent)
    if item_type == "User Story" and parent:
        if parent not in deps:
            deps = [parent] + deps
    lines = []
    for d in deps:
        lines.append(f"- #{d} (must be closed first)")
    return "\n".join(lines) if lines else "_None — can start immediately._"


def github_labels(item):
    labels = ["aimpos-spark", item["Work Item Type"].lower().replace(" ", "-")]
    sprint = item["Sprint"]
    if sprint and sprint != "S1-S5":
        labels.append(f"sprint:{sprint.lower()}")
    if item["Feature ID"]:
        labels.append(f"feature:{item['Feature ID']}")
    if item["Epic ID"]:
        labels.append(f"epic:{item['Epic ID']}")
    labels.append(f"priority:{item['Priority'].lower()}")
    for part in item["Labels"].split(";"):
        p = part.strip()
        if p and p not in labels:
            labels.append(p)
    return ", ".join(f"`{l}`" for l in labels)


def complexity(item):
    t = item["Work Item Type"]
    sp = item.get("Story Points", "")
    if t == "Epic":
        return "XL (multi-sprint)"
    if t == "Feature":
        return "Large (multi-story)"
    return COMPLEXITY_SP.get(sp, "Medium") + (f" ({sp} SP)" if sp else "")


def business_value(item):
    fid = item.get("Feature ID") or item["ID"]
    if item["Work Item Type"] == "User Story":
        return STORY_BV.get(item["ID"], BV.get(fid, item["Description"]))
    return BV.get(item["ID"], BV.get(fid, item["Description"]))


def issue_md(item, blocks, tasks_by_parent, idx):
    iid = item["ID"]
    wtype = item["Work Item Type"]
    title = f"[{iid}] {item['Title']}"
    milestone = item["Sprint"] if item["Sprint"] != "S1-S5" else "Cross-sprint"

    body = [f"## Issue {idx}: {title}\n"]
    body.append(f"**Type:** {wtype}  ")
    body.append(f"**Milestone:** {milestone}  ")
    if item.get("Story Points"):
        body.append(f"**Story Points:** {item['Story Points']}  ")
    if item.get("Parent ID"):
        body.append(f"**Parent:** #{item['Parent ID']}  ")
    if item.get("Epic ID"):
        body.append(f"**Epic:** #{item['Epic ID']}  ")
    if iid in IMPL_ORDER:
        body.append(f"**Implementation Order:** {IMPL_ORDER[iid]}  ")
    body.append("")

    body.append("### Title")
    body.append(f"{title}\n")

    body.append("### Description")
    body.append(item["Description"])
    body.append("")

    body.append("### Business Value")
    body.append(business_value(item))
    body.append("")

    body.append("### Acceptance Criteria")
    body.append(fmt_ac(item["Acceptance Criteria"], wtype))
    body.append("")

    body.append("### Dependencies")
    body.append(fmt_deps(iid, blocks, wtype, item.get("Parent ID", ""), item.get("Epic ID", "")))
    body.append("")

    body.append("### Priority")
    body.append(item["Priority"])
    body.append("")

    body.append("### Labels")
    body.append(github_labels(item))
    body.append("")

    body.append("### Estimated Complexity")
    body.append(complexity(item))
    body.append("")

    body.append("### Definition of Done")
    if wtype == "Epic":
        body.append(DOD_EPIC)
    elif wtype == "Feature":
        body.append(DOD_FEATURE)
    else:
        body.append(DOD_STORY)
    body.append("")

    if wtype == "User Story" and iid in tasks_by_parent:
        body.append("### Implementation Tasks")
        for tid, ttitle in tasks_by_parent[iid]:
            body.append(f"- [ ] `{tid}` — {ttitle}")
        body.append("")

    body.append("---\n")
    return "\n".join(body)


def main():
    items = load_backlog()
    blocks = load_deps()
    tasks = load_tasks(items)

    epics = [i for i in items if i["Work Item Type"] == "Epic"]
    features = [i for i in items if i["Work Item Type"] == "Feature"]
    stories = [i for i in items if i["Work Item Type"] == "User Story"]
    stories.sort(key=lambda s: IMPL_ORDER.get(s["ID"], 99))

    ordered = epics + features + stories

    lines = [
        "# AIMPOS-Spark — GitHub Issues",
        "",
        "**Product:** AIMPOS-Spark MVP  ",
        "**Format:** GitHub Issue Markdown (copy body into issue or use `gh issue create`)  ",
        "**Total Issues:** 50 (6 Epics · 17 Features · 27 User Stories)  ",
        "**Source:** [MVP Backlog.md](./MVP%20Backlog.md) · [MVP Dependency Map.md](./MVP%20Dependency%20Map.md)",
        "",
        "---",
        "",
        "## How to Import",
        "",
        "```bash",
        "# Example: create a user story issue",
        'gh issue create --title "[US-02] Deploy MVP stack on Olares" \\',
        '  --label "aimpos-spark,user-story,sprint:s1,priority:p0,devops" \\',
        '  --milestone "Sprint 1" \\',
        '  --body-file issues/US-02.md',
        "```",
        "",
        "**Recommended GitHub setup:**",
        "- Milestones: `Sprint 1` … `Sprint 5`",
        "- Labels: `epic`, `feature`, `user-story`, `priority:p0`, `priority:p1`, `sprint:s1`–`sprint:s5`",
        "- Parent links: use GitHub Projects v2 sub-issue relationships or `Depends on #N` in descriptions",
        "",
        "---",
        "",
        "## Issue Index",
        "",
        "| # | ID | Title | Priority | Sprint | Complexity |",
        "|---|-----|-------|----------|--------|------------|",
    ]

    idx = 0
    for item in ordered:
        idx += 1
        sp = item.get("Story Points", "—")
        lines.append(
            f"| {idx} | {item['ID']} | {item['Title']} | {item['Priority']} | {item['Sprint']} | {complexity(item)} |"
        )

    lines.extend(["", "---", ""])

    idx = 0
    for item in ordered:
        idx += 1
        lines.append(issue_md(item, blocks, tasks, idx))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({idx} issues)")


if __name__ == "__main__":
    main()
