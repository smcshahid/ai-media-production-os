#!/usr/bin/env python3
"""US-12 verification — idea → pipeline start → run_story_agent → STORY asset + audit.

Requires compose: api, worker, temporal, postgresql, minio, ollama (qwen3:14b).

Usage:
    python scripts/smoke/test_us12_story.py

Exit codes:
    0  PASS
    1  FAIL
    2  SKIP
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
EVIDENCE_DIR = ROOT / "evidence" / "us-12-verification"
_PARAGRAPH = (
    "A lone astronaut discovers a hidden garden on Mars and must decide "
    "whether to share it with Earth before the colony council arrives."
)

DISPLAY = {
    "RUNNING": "GENERATING",
    "AWAITING_APPROVAL": "REVIEW",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str) -> None:
    print(f"SKIP: {msg}")
    raise SystemExit(2)


def load_token() -> str:
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("AIMPOS_API_TOKEN="):
            return line.partition("=")[2].strip()
    fail("AIMPOS_API_TOKEN not found in .env")


def http_json(method: str, url: str, *, token: str, body: dict | None = None, timeout: float = 30):
    data = None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, {"detail": raw}
    except urllib.error.URLError as exc:
        skip(f"API unreachable ({exc.reason})")


def psql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "aimpos-spark-postgresql-1",
        "psql",
        "-U",
        "aimpos",
        "-d",
        "aimpos_spark",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        fail(f"psql failed: {result.stderr.strip()}")
    return result.stdout.strip()


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    api = "http://127.0.0.1:8000"
    token = load_token()
    log_lines: list[str] = []

    def record(label: str, payload: object) -> None:
        line = f"{label}: {json.dumps(payload, default=str)}"
        print(line)
        log_lines.append(line)

    print("=== US-12 verification ===\n")

    code, projects = http_json("GET", f"{api}/projects", token=token)
    if code != 200 or not projects:
        fail(f"GET /projects HTTP {code}")
    project_id = projects[0]["id"]
    record("project_id", project_id)

    code, idea = http_json(
        "POST",
        f"{api}/ideas",
        token=token,
        body={
            "project_id": project_id,
            "title": "Mars Garden US-12",
            "paragraph": _PARAGRAPH,
            "style_note": "cinematic sci-fi",
        },
    )
    if code != 201:
        fail(f"POST /ideas HTTP {code}: {idea}")
    record("idea_asset", idea)

    code, start = http_json(
        "POST",
        f"{api}/pipeline/start",
        token=token,
        body={"project_id": project_id},
    )
    if code != 201:
        fail(f"POST /pipeline/start HTTP {code}: {start}")
    run_id = start["run_id"]
    record("pipeline_start", start)

    deadline = time.monotonic() + 300
    status_payload = None
    while time.monotonic() < deadline:
        code, status_payload = http_json(
            "GET",
            f"{api}/pipeline/status?project_id={project_id}",
            token=token,
        )
        if code != 200:
            fail(f"GET /pipeline/status HTTP {code}")
        st = status_payload["status"]
        stage = status_payload.get("current_stage")
        display = DISPLAY.get(st, st)
        print(f"  poll status={st} stage={stage} display={display}")
        if st == "AWAITING_APPROVAL" and stage == "STORY":
            break
        if st == "FAILED":
            fail(f"pipeline FAILED at stage {stage}")
        time.sleep(3)
    else:
        fail("timed out waiting for AWAITING_APPROVAL/STORY")

    record("pipeline_status_final", status_payload)
    record(
        "dashboard_presentation",
        {
            "api_status": status_payload["status"],
            "api_stage": status_payload["current_stage"],
            "ui_label": DISPLAY.get(status_payload["status"], status_payload["status"]),
        },
    )

    story_rows = psql(
        f"SELECT id, stage, version, branch, is_ai_generated, content_hash, minio_key "
        f"FROM asset_versions WHERE project_id='{project_id}' AND stage='STORY' "
        f"ORDER BY version DESC LIMIT 1;"
    )
    if not story_rows:
        fail("no STORY asset_versions row")
    parts = story_rows.split("|")
    record(
        "asset_versions_story",
        {
            "id": parts[0],
            "stage": parts[1],
            "version": parts[2],
            "branch": parts[3],
            "is_ai_generated": parts[4],
            "content_hash": parts[5],
            "minio_key": parts[6],
        },
    )
    if parts[3] != "ai-draft" or parts[4] != "t":
        fail(f"STORY asset branch/is_ai_generated mismatch: {story_rows}")

    audit_rows = psql(
        f"SELECT event_type, model_id, payload::text FROM audit_events "
        f"WHERE pipeline_run_id='{run_id}' ORDER BY created_at;"
    )
    record("audit_events", audit_rows)
    if "AGENT_TASK_COMPLETED" not in audit_rows:
        fail("AGENT_TASK_COMPLETED audit missing")
    if "qwen3:14b" not in audit_rows:
        fail("model_id qwen3:14b not in audit trail")

    worker_log = subprocess.run(
        ["docker", "logs", "aimpos-spark-worker-1", "--tail", "40"],
        capture_output=True,
        text=True,
        check=False,
    )
    record("worker_log_tail", worker_log.stdout[-2000:] if worker_log.stdout else "")

    (EVIDENCE_DIR / "us-12-verification.log").write_text("\n".join(log_lines), encoding="utf-8")
    print("\nPASS - US-12 story agent E2E verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
