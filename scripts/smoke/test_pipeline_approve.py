#!/usr/bin/env python3
"""US-08 E2E — approve/reject signals, approvals, audit, multi-stage progression.

Requires running compose: api, postgresql, temporal, worker.

Usage (from repo root):
    python scripts/smoke/test_pipeline_approve.py

Exit codes:
    0  PASS
    1  FAIL
    2  SKIP
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
STAGES = ("STORY", "SCRIPT", "STORYBOARD")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str) -> None:
    print(f"SKIP: {msg}")
    print("SKIP - pipeline approve smoke not run. This is not PASS.")
    raise SystemExit(2)


def load_token() -> str:
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("AIMPOS_API_TOKEN="):
            return line.partition("=")[2].strip()
    fail("AIMPOS_API_TOKEN not found")


def http_json(
    method: str,
    url: str,
    *,
    token: str,
    body: dict | None = None,
    timeout: float = 15,
) -> tuple[int, dict]:
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
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload
    except urllib.error.URLError as exc:
        skip(f"cannot reach API ({exc.reason})")


def wait_status(
    api_base: str,
    token: str,
    project_id: str,
    *,
    want_status: str | None = None,
    want_stage: str | None = None,
    timeout: float = 25.0,
) -> dict:
    deadline = time.monotonic() + timeout
    last: dict = {}
    while time.monotonic() < deadline:
        code, body = http_json(
            "GET",
            f"{api_base}/pipeline/status?project_id={project_id}",
            token=token,
        )
        if code != 200:
            fail(f"GET /pipeline/status failed: {code} {body}")
        last = body
        if want_status and body.get("status") != want_status:
            time.sleep(0.5)
            continue
        if want_stage and body.get("current_stage") != want_stage:
            time.sleep(0.5)
            continue
        return body
    fail(f"status timeout: wanted status={want_status} stage={want_stage}, got {last}")
    raise AssertionError("unreachable")


def psql(query: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "aimpos-spark-postgresql-1",
            "psql",
            "-U",
            "aimpos",
            "-d",
            "aimpos_spark",
            "-tAc",
            query,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        fail(f"psql failed: {result.stderr.strip()}")
    return result.stdout.strip()


def cancel_stale_active_runs() -> None:
    """Clear orphaned DB rows so a fresh workflow can start (smoke-only)."""
    psql(
        "UPDATE pipeline_runs SET status = 'CANCELLED' "
        "WHERE status IN ('PENDING', 'RUNNING', 'AWAITING_APPROVAL')"
    )


def ensure_awaiting_story(api_base: str, token: str, project_id: str) -> str:
    cancel_stale_active_runs()
    code, status_body = http_json(
        "GET",
        f"{api_base}/pipeline/status?project_id={project_id}",
        token=token,
    )
    if code != 200:
        fail(f"status check failed: {code}")

    if status_body.get("status") in {"IDLE", "COMPLETED", "CANCELLED"} or status_body.get("run_id") is None:
        code, start = http_json(
            "POST",
            f"{api_base}/pipeline/start",
            token=token,
            body={"project_id": project_id},
        )
        if code != 201:
            fail(f"start failed: {code} {start}")
        wait_status(api_base, token, project_id, want_status="AWAITING_APPROVAL", want_stage="STORY")
    elif status_body.get("status") != "AWAITING_APPROVAL":
        wait_status(api_base, token, project_id, want_status="AWAITING_APPROVAL", want_stage="STORY")

    run_id = wait_status(
        api_base, token, project_id, want_status="AWAITING_APPROVAL", want_stage="STORY"
    )["run_id"]
    if not run_id:
        fail("no run_id while awaiting STORY approval")
    return run_id


def main() -> int:
    if not ENV_FILE.exists():
        fail(f"{ENV_FILE} not found")
    token = load_token()
    api_base = os.environ.get("AIMPOS_API_BASE", "http://127.0.0.1:8000")

    print(f"Target: {api_base}\n")

    print("[setup] resolve project...")
    code, projects = http_json("GET", f"{api_base}/projects", token=token)
    if code != 200 or not projects:
        fail(f"GET /projects failed: {code}")
    project_id = projects[0]["id"]
    print(f"  OK - project_id={project_id}\n")

    print("[reject path] reject STORY then approve...")
    run_id = ensure_awaiting_story(api_base, token, project_id)
    code, reject_body = http_json(
        "POST",
        f"{api_base}/pipeline/approve",
        token=token,
        body={
            "project_id": project_id,
            "stage": "STORY",
            "decision": "REJECT",
            "note": "smoke reject — revise story",
        },
    )
    if code != 200:
        fail(f"reject failed: {code} {reject_body}")
    after_reject = wait_status(
        api_base, token, project_id, want_status="AWAITING_APPROVAL", want_stage="STORY"
    )
    print(f"  OK - still AWAITING_APPROVAL/STORY run_id={after_reject['run_id']}\n")

    print("[approval path] approve STORY, SCRIPT, STORYBOARD...")
    for stage in STAGES:
        wait_status(
            api_base,
            token,
            project_id,
            want_status="AWAITING_APPROVAL",
            want_stage=stage,
        )
        code, approve_body = http_json(
            "POST",
            f"{api_base}/pipeline/approve",
            token=token,
            body={"project_id": project_id, "stage": stage, "decision": "GRANT"},
        )
        if code != 200:
            fail(f"approve {stage} failed: {code} {approve_body}")
        print(f"  OK - approved {stage} approval_id={approve_body['approval_id']}")

    completed = wait_status(api_base, token, project_id, want_status="COMPLETED", timeout=30.0)
    print(f"\n  OK - pipeline COMPLETED run_id={completed['run_id']}\n")

    print("[audit trail] verify approvals + audit_events in DB...")
    approval_count = psql(
        f"SELECT COUNT(*) FROM approvals WHERE pipeline_run_id = '{completed['run_id']}'::uuid"
    )
    # 1 reject + 3 grants on final run (reject row also on same run)
    if int(approval_count) < 4:
        fail(f"expected >=4 approval rows on run, got {approval_count}")

    audit_count = psql(
        "SELECT COUNT(*) FROM audit_events WHERE event_type = 'APPROVAL_RECORDED' "
        f"AND pipeline_run_id = '{completed['run_id']}'::uuid"
    )
    if int(audit_count) < 4:
        fail(f"expected >=4 APPROVAL_RECORDED events, got {audit_count}")

    latest_audit = psql(
        "SELECT payload->>'decision' FROM audit_events "
        f"WHERE pipeline_run_id = '{completed['run_id']}'::uuid "
        "AND event_type = 'APPROVAL_RECORDED' ORDER BY created_at DESC LIMIT 1"
    )
    print(f"  OK - approvals={approval_count} audit_events={audit_count} latest={latest_audit}\n")

    print("PASS - US-08 approval/reject, signals, immutable records, audit, multi-stage E2E.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
