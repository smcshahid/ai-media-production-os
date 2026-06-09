"""Generate GitHub Issues for AIMPOS-Spark Visual MVP (Idea → Storyboard)."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKLOG = Path(__file__).parent / "aimpos-spark-backlog.csv"
DEPS = Path(__file__).parent / "aimpos-spark-dependencies.csv"
OUT = ROOT / "GitHub Issues - Visual MVP.md"

CODENAME = "AIMPOS-Spark Visual"
SCOPE = "Idea → Story → Script → Storyboard"

# Included work items (43 total)
INCLUDED_IDS = {
    "EPIC-01", "EPIC-02", "EPIC-03", "EPIC-04", "EPIC-06",
    "FEAT-INFRA", "FEAT-01", "FEAT-03", "FEAT-16", "FEAT-02",
    "FEAT-04", "FEAT-05", "FEAT-06", "FEAT-07", "FEAT-08",
    "FEAT-09", "FEAT-12", "FEAT-13", "FEAT-14",
    "US-01", "US-02", "US-03", "US-04", "US-05", "US-06",
    "US-07", "US-08", "US-09", "US-10", "US-11", "US-12",
    "US-13", "US-14", "US-15", "US-16", "US-17", "US-20",
    "US-22", "US-23", "US-24", "US-25", "US-26",
    "US-V01",
}

# Dependency-ordered flat list (epics/features placed at wave start)
FLAT_ORDER = [
    "EPIC-01", "FEAT-INFRA",
    "US-02", "US-04", "US-03", "US-05", "US-06", "US-01",
    "EPIC-02", "FEAT-03", "FEAT-16",
    "US-26", "US-07", "US-08", "US-09", "US-24", "US-25", "US-10",
    "EPIC-03", "FEAT-01", "FEAT-02", "FEAT-04", "FEAT-05", "FEAT-06", "FEAT-07", "FEAT-13",
    "US-11", "US-12", "US-13", "US-14", "US-15", "US-23",
    "EPIC-04", "FEAT-08", "FEAT-09", "FEAT-12", "FEAT-14",
    "US-16", "US-17", "US-20", "US-22",
    "EPIC-06", "US-V01",
]

EXCLUDED = {
    "EPIC-05", "FEAT-10", "FEAT-11", "FEAT-15",
    "US-18", "US-19", "US-21", "US-27",
}

BV = {
    "EPIC-01": "Runnable local-AI platform on Olares. Prerequisite for Ollama (text) and ComfyUI (images).",
    "EPIC-02": "4-stage workflow with human approval gates. Proves Temporal + human-in-the-loop without video complexity.",
    "EPIC-03": "Text pipeline via local Ollama — Story Architect and Screenwriter agents.",
    "EPIC-04": "**Terminal delivery epic for Visual MVP.** Approved storyboard frames = MVP complete.",
    "EPIC-06": "Governance, audit, asset history, and creator UX across the 4-stage pipeline.",
    "F-INFRA": "Shared infrastructure for all stages.",
    "F-01": "Zero-setup project for solo creator.",
    "F-02": "Captures idea as first versioned asset.",
    "F-03": "Starts 4-stage Temporal workflow (Idea→Story→Script→Storyboard).",
    "F-04": "Local LLM story generation — first AI value.",
    "F-05": "Human approval over AI story.",
    "F-06": "Local LLM one-scene screenplay.",
    "F-07": "Human approval before GPU storyboard work.",
    "F-08": "Local ComfyUI storyboard frames — visual MVP climax.",
    "F-09": "Human curation of frame set; pipeline completes on approval.",
    "F-12": "Version history for text and image assets.",
    "F-13": "Audit trail for local model invocations.",
    "F-14": "Lineage chain Idea→Story→Script→Frames (no video node).",
    "F-16": "4-stage progress dashboard.",
    "FEAT-14": "Lineage chain Idea→Story→Script→Frames (no video node).",
    "FEAT-08": "Local ComfyUI storyboard frames — visual MVP climax.",
    "FEAT-09": "Human curation of frame set; pipeline completes on approval.",
}

STORY_BV = {
    "US-01": "Immediate project context — no setup.",
    "US-02": "One-command Olares deployment.",
    "US-03": "Integration health visibility.",
    "US-04": "PostgreSQL system of record.",
    "US-05": "Versioned assets in MinIO.",
    "US-06": "Validates Ollama + ComfyUI image path early.",
    "US-07": "4-stage governed pipeline automation.",
    "US-08": "4 human gates enforced (SC-03 adapted).",
    "US-09": "Regenerate without restart.",
    "US-10": "4-step progress UI.",
    "US-11": "MVP entry — creator's idea.",
    "US-12": "Ollama Story Architect output.",
    "US-13": "Edit and approve treatment.",
    "US-14": "Ollama Screenwriter output.",
    "US-15": "Approve script before ComfyUI.",
    "US-16": "ComfyUI generates 4–6 frames locally.",
    "US-17": "Approve frames → pipeline COMPLETED.",
    "US-20": "Traceability Idea→Frames without Neo4j.",
    "US-22": "Browse drafts and approvals.",
    "US-23": "Verify 100% local AI calls logged.",
    "US-24": "ComfyUI jobs survive worker restart.",
    "US-25": "LAN token auth on mutating APIs.",
    "US-26": "Nav: Dashboard, Review, Assets, Audit.",
    "US-V01": "Proves Visual MVP: Idea→approved storyboard E2E on Olares.",
}

OVERRIDES = {
    "EPIC-02": {
        "desc": "Temporal 4-stage workflow: Idea → Story → Script → Storyboard. Start, status, approve/reject, regenerate, audit.",
        "ac": "User starts pipeline and sees 4-stage status. Workflow pauses at each review gate. Approve on storyboard sets COMPLETED. All transitions in audit_events.",
    },
    "EPIC-04": {
        "desc": "ComfyUI storyboard from approved script. Gallery review. **Pipeline completes when frames are approved.**",
        "ac": "4–6 frames generated locally via ComfyUI. Gallery approve/reject/regenerate. GPU sequenced without OOM. Approved frames = Visual MVP complete.",
    },
    "EPIC-05": None,
    "F-03": {"desc": "Start 4-stage Temporal workflow after idea capture. F-03 (Visual MVP scope)."},
    "F-08": {"desc": "Cinematography agent + ComfyUI frames. **Terminal AI stage for Visual MVP.** F-08."},
    "F-09": {"desc": "Gallery review; approve-all sets pipeline COMPLETED. F-09."},
    "FEAT-14": {
        "desc": "Lineage chain: idea → story → script → frames (video deferred). F-14.",
        "parent_epic": "EPIC-04",
        "sprint": "S4",
    },
    "F-16": {"desc": "Dashboard with 4-stage progress. F-16."},
    "US-07": {
        "desc": "As a creator, I want to start the 4-stage production pipeline after entering my idea.",
        "ac": "POST /pipeline/start creates SparkPipelineWorkflow (4 stages). Status shows STORY_GENERATING or STORY_REVIEW. Workflow ends at COMPLETED after storyboard approval (no video stage). PipelineStarted audit event recorded.",
    },
    "US-10": {
        "ac": "Dashboard shows 4-stage progress (Idea, Story, Script, Storyboard). REVIEW shows Go to Review CTA. GENERATING polls every 5s.",
    },
    "US-17": {
        "ac": "Grid of 4–6 images. Lightbox preview. Approve-all sets pipeline COMPLETED. Reject triggers regenerate. AI badge on frames.",
    },
    "US-20": {
        "desc": "As a creator, I want to see the chain from idea to storyboard frames.",
        "ac": "Ordered chain: idea → story → script → frames. Click node shows metadata. Data from lineage_edges in PostgreSQL. No video node.",
        "sprint": "S4",
        "parent_epic": "EPIC-04",
    },
    "US-26": {
        "ac": "Nav bar: Dashboard, Review, Assets, Audit (Export deferred). Empty states when pipeline not started. Usable at >=768px.",
    },
}

US_V01 = {
    "Work Item Type": "User Story",
    "ID": "US-V01",
    "Title": "Visual MVP demo acceptance validation",
    "Description": "As a product owner, I want the Visual MVP demo script executable end-to-end on Olares.",
    "Parent ID": "FEAT-09",
    "Epic ID": "EPIC-04",
    "Feature ID": "F-09",
    "Priority": "P0",
    "Story Points": "2",
    "Sprint": "S4",
    "Labels": "user-story;qa;visual-mvp",
    "Acceptance Criteria": (
        "1. Enter idea on fresh project. 2. Start pipeline. 3. Approve story with one edit. "
        "4. Reject script once, regenerate, approve. 5. Approve all storyboard frames. "
        "6. Pipeline status COMPLETED. 7. Audit log shows 4 approvals and 3+ local model invocations. "
        "8. Lineage shows idea to frames. 9. Restart worker — state unchanged. "
        "Pass: all steps without manual DB intervention. 100% local inference (SC-02)."
    ),
}

TASKS_V01 = [
    ("T-V01-01", "Execute Visual MVP demo script on Olares"),
    ("T-V01-02", "Verify SC-02 SC-03 SC-04 SC-05 SC-06 SC-07 SC-08 for 4-stage scope"),
    ("T-V01-03", "Document deferred items (video, export) in release notes"),
    ("T-V01-04", "Stakeholder sign-off on Visual MVP"),
]

COMPLEXITY_SP = {"2": "Low", "3": "Low", "5": "Medium", "8": "High", "": "Medium"}

FEATURE_DEPS = {
    "FEAT-INFRA": ["EPIC-01"],
    "FEAT-01": ["FEAT-INFRA"],
    "FEAT-03": ["FEAT-INFRA", "FEAT-01"],
    "FEAT-16": ["FEAT-INFRA", "FEAT-03"],
    "FEAT-02": ["FEAT-01", "FEAT-03"],
    "FEAT-04": ["FEAT-02", "FEAT-03"],
    "FEAT-05": ["FEAT-04"],
    "FEAT-06": ["FEAT-05"],
    "FEAT-07": ["FEAT-06"],
    "FEAT-08": ["FEAT-07"],
    "FEAT-09": ["FEAT-08"],
    "FEAT-12": ["FEAT-INFRA"],
    "FEAT-13": ["FEAT-03"],
    "FEAT-14": ["FEAT-09", "EPIC-04"],
}

EPIC_DEPS = {
    "EPIC-02": ["EPIC-01"],
    "EPIC-03": ["EPIC-02"],
    "EPIC-04": ["EPIC-03"],
    "EPIC-06": ["EPIC-01"],
}

STORY_DEPS_EXTRA = {
    "US-V01": ["US-17", "US-20", "US-23"],
}

DOD = {
    "Epic": "- [ ] All child P0 features and stories closed\n- [ ] Epic AC verified on Olares\n- [ ] No P0 defects",
    "Feature": "- [ ] All child stories closed\n- [ ] Traced to F-xx in release notes\n- [ ] PO acceptance",
    "User Story": "- [ ] Tasks complete\n- [ ] AC verified\n- [ ] Merged to main\n- [ ] Dependencies regression-free",
}


def load_backlog():
    by_id = {}
    with open(BACKLOG, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["ID"] in INCLUDED_IDS:
                by_id[row["ID"]] = row
    by_id["US-V01"] = US_V01
    return by_id


def load_blocks():
    blocks = defaultdict(list)
    with open(DEPS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Target ID"] in INCLUDED_IDS and row["Source ID"] in INCLUDED_IDS:
                if row["Dependency Type"] in ("Blocks", "Requires"):
                    blocks[row["Target ID"]].append(row["Source ID"])
    return blocks


def load_tasks():
    tasks = defaultdict(list)
    with open(BACKLOG, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Work Item Type"] == "Task" and row["Parent ID"] in INCLUDED_IDS:
                tasks[row["Parent ID"]].append((row["ID"], row["Title"]))
    tasks["US-V01"] = TASKS_V01
    return tasks


def fmt_ac(text):
    if not text:
        return "_See child user stories._"
    parts = [p.strip() for p in text.split(".") if p.strip()]
    return "\n".join(f"- [ ] {p}" for p in parts)


def fmt_deps(iid, wtype, parent, blocks):
    deps = list(blocks.get(iid, []))
    if wtype == "Epic":
        deps = EPIC_DEPS.get(iid, []) + deps
    elif wtype == "Feature":
        deps = FEATURE_DEPS.get(iid, []) + deps
        if parent and parent not in deps:
            deps.insert(0, parent)
    elif wtype == "User Story":
        deps = STORY_DEPS_EXTRA.get(iid, []) + deps
        if parent and parent not in deps:
            deps.insert(0, parent)
    seen = []
    for d in deps:
        if d not in seen:
            seen.append(d)
    return "\n".join(f"- #{d} (must be closed first)" for d in seen) or "_None._"


def labels(item):
    parts = ["aimpos-spark", "visual-mvp", item["Work Item Type"].lower().replace(" ", "-")]
    if item["Sprint"] not in ("", "S1-S5"):
        parts.append(f"sprint:{item['Sprint'].lower()}")
    if item["Feature ID"]:
        parts.append(f"feature:{item['Feature ID']}")
    if item["Epic ID"]:
        parts.append(f"epic:{item['Epic ID']}")
    parts.append(f"priority:{item['Priority'].lower()}")
    for p in item["Labels"].split(";"):
        p = p.strip()
        if p:
            parts.append(p)
    return ", ".join(f"`{x}`" for x in parts)


def complexity(item):
    t = item["Work Item Type"]
    if t == "Epic":
        return "XL"
    if t == "Feature":
        return "Large"
    sp = item.get("Story Points", "")
    return f"{COMPLEXITY_SP.get(sp, 'Medium')}" + (f" ({sp} SP)" if sp else "")


def issue_body(item, idx, blocks, tasks):
    iid = item["ID"]
    wtype = item["Work Item Type"]
    ov = OVERRIDES.get(iid, {})
    item = dict(item)
    if ov.get("parent_epic"):
        item["Epic ID"] = ov["parent_epic"]
    if ov.get("sprint"):
        item["Sprint"] = ov["sprint"]
    desc = ov.get("desc", item["Description"])
    ac = ov.get("ac", item["Acceptance Criteria"])

    lines = [
        f"## Issue {idx}: [{iid}] {item['Title']}\n",
        f"**Type:** {wtype}  ",
        f"**Milestone:** {item['Sprint']}  ",
        f"**Implementation Order:** {idx}  ",
    ]
    if item.get("Story Points"):
        lines.append(f"**Story Points:** {item['Story Points']}  ")
    if item.get("Parent ID"):
        lines.append(f"**Parent:** #{item['Parent ID']}  ")
    if item.get("Epic ID"):
        lines.append(f"**Epic:** #{item['Epic ID']}  ")
    lines.append("")

    for section, content in [
        ("Title", f"[{iid}] {item['Title']}"),
        ("Description", desc),
        ("Business Value", BV.get(iid) or STORY_BV.get(iid, desc)),
        ("Acceptance Criteria", fmt_ac(ac)),
        ("Dependencies", fmt_deps(iid, wtype, item.get("Parent ID", ""), blocks)),
        ("Priority", item["Priority"]),
        ("Labels", labels(item)),
        ("Estimated Complexity", complexity(item)),
        ("Definition of Done", DOD[wtype]),
    ]:
        lines += [f"### {section}", content, ""]

    if iid in tasks:
        lines.append("### Implementation Tasks")
        for tid, title in tasks[iid]:
            lines.append(f"- [ ] `{tid}` — {title}")
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def main():
    by_id = load_backlog()
    blocks = load_blocks()
    tasks = load_tasks()

    header = [
        f"# {CODENAME} — GitHub Issues",
        "",
        f"**Scope:** {SCOPE} · **Local AI only** (Ollama + ComfyUI)  ",
        f"**Total Issues:** {len(FLAT_ORDER)}  ",
        "**Codename:** `AIMPOS-Spark-Visual`  ",
        "",
        "## What This MVP Delivers",
        "",
        "| Stage | Human | Local AI | Output |",
        "|-------|-------|----------|--------|",
        "| Idea | Write paragraph | — | `idea.txt` |",
        "| Story | Approve / edit | Ollama Story Architect | `story.md` |",
        "| Script | Approve / edit | Ollama Screenwriter | `script.fountain` |",
        "| Storyboard | Approve frames | ComfyUI + Ollama planning | `frame_*.png` |",
        "",
        "**Pipeline completes** when storyboard frames are approved (`COMPLETED`).",
        "",
        "## Explicitly Deferred (Post–Visual MVP)",
        "",
        "| Excluded | IDs |",
        "|----------|-----|",
        "| Short video generation | F-10, US-18 |",
        "| Video review | F-11, US-19 |",
        "| Export bundle | F-15, US-21 |",
        "| Full 5-stage demo | US-27, EPIC-05 |",
        "",
        "## Sprint Plan (8 weeks)",
        "",
        "| Sprint | Weeks | Deliverable |",
        "|--------|-------|-------------|",
        "| S1 | 1–2 | Platform running on Olares |",
        "| S2 | 3–4 | 4-stage workflow + dashboard |",
        "| S3 | 5–6 | Idea → approved script |",
        "| S4 | 7–8 | Storyboard + lineage + **Visual MVP sign-off** |",
        "",
        "## Import",
        "",
        "```bash",
        'gh issue create --title "[US-02] Deploy MVP stack on Olares" \\',
        '  --label "aimpos-spark,visual-mvp,user-story,sprint:s1,priority:p0" \\',
        '  --milestone "Sprint 1"',
        "```",
        "",
        "---",
        "",
        "## Issue Index (Dependency Order)",
        "",
        "| Order | ID | Type | Title | Priority | Sprint |",
        "|------:|-----|------|-------|----------|--------|",
    ]

    for idx, iid in enumerate(FLAT_ORDER, 1):
        item = dict(by_id[iid])
        ov = OVERRIDES.get(iid, {})
        if ov.get("sprint"):
            item["Sprint"] = ov["sprint"]
        if ov.get("parent_epic"):
            item["Epic ID"] = ov["parent_epic"]
        header.append(
            f"| {idx} | {iid} | {item['Work Item Type']} | {item['Title']} | {item['Priority']} | {item['Sprint']} |"
        )

    header += ["", "---", ""]

    bodies = []
    for idx, iid in enumerate(FLAT_ORDER, 1):
        bodies.append(issue_body(by_id[iid], idx, blocks, tasks))

    OUT.write_text("\n".join(header) + "\n".join(bodies), encoding="utf-8")
    print(f"Wrote {OUT} ({len(FLAT_ORDER)} issues)")
    print(f"Excluded: {sorted(EXCLUDED)}")


if __name__ == "__main__":
    main()
