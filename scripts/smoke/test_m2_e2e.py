#!/usr/bin/env python3
"""M2 / US-10 E2E — stub pipeline start → review gates → COMPLETED.

Validates DB-backed status transitions that the dashboard polls via
`GET /pipeline/status` (D-32). Presentation labels (GENERATING/REVIEW) are
dashboard-only; this script logs raw API status + stage.

Requires running compose: api, postgresql, temporal, worker.

Usage (from repo root):
    python scripts/smoke/test_m2_e2e.py

Exit codes:
    0  PASS
    1  FAIL
    2  SKIP
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
STAGES = ("STORY", "SCRIPT", "STORYBOARD")

DISPLAY = {
    "IDLE": "IDLE",
    "PENDING": "GENERATING",
    "RUNNING": "GENERATING",
    "AWAITING_APPROVAL": "REVIEW",
    "COMPLETED": "COMPLETED",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str) -> None:
    print(f"SKIP: {msg}")
    print("SKIP - M2 E2E smoke not run. This is not PASS.")
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
    timeout: float = 45,
) -> dict:
    deadline = time.monotonic() + timeout
    last: dict = {}
    while time.monotonic() < deadline:
        code, payload = http_json(
            "GET",
            f"{api_base}/pipeline/status?project_id={project_id}",
            token=token,
        )
        if code != 200:
            fail(f"status poll HTTP {code}: {payload}")
        last = payload
        if want_status and payload.get("status") != want_status:
            time.sleep(0.5)
            continue
        if want_stage and payload.get("current_stage") != want_stage:
            time.sleep(0.5)
            continue
        return payload
    fail(f"timeout waiting for status={want_status} stage={want_stage}; last={last}")


def log_dashboard_view(payload: dict) -> None:
    api_status = payload.get("status", "IDLE")
    display = DISPLAY.get(api_status, api_status)
    stage = payload.get("current_stage")
    print(
        f"  dashboard view: badge={display} stage={stage} run_id={payload.get('run_id')}",
    )


def main() -> None:
    api_base = "http://127.0.0.1:8000"
    token = load_token()
    print(f"Target: {api_base}\n")

    print("[1] resolve project")
    code, projects = http_json("GET", f"{api_base}/projects", token=token)
    if code != 200 or not projects:
        fail(f"GET /projects HTTP {code}")
    project_id = projects[0]["id"]
    print(f"  OK - project_id={project_id}")

    print("\n[2] dashboard start flow (POST /pipeline/start)")
    code, start = http_json(
        "POST",
        f"{api_base}/pipeline/start",
        token=token,
        body={"project_id": project_id},
    )
    if code == 409:
        print("  active run exists — polling current status instead")
        start = wait_status(api_base, token, project_id, want_status="AWAITING_APPROVAL")
    elif code != 201:
        fail(f"POST /pipeline/start HTTP {code}: {start}")
    else:
        print(f"  OK - run_id={start.get('run_id')} workflow_id={start.get('workflow_id')}")
        start = wait_status(
            api_base,
            token,
            project_id,
            want_status="AWAITING_APPROVAL",
            want_stage="STORY",
        )
    log_dashboard_view(start)
    assert start["status"] == "AWAITING_APPROVAL"
    print("  OK - live poll would show REVIEW + Go to Review CTA")

    print("\n[3] review workflow — approve STORY, SCRIPT, STORYBOARD")
    for stage in STAGES:
        wait_status(
            api_base,
            token,
            project_id,
            want_status="AWAITING_APPROVAL",
            want_stage=stage,
        )
        log_dashboard_view(wait_status(api_base, token, project_id))
        code, approved = http_json(
            "POST",
            f"{api_base}/pipeline/approve",
            token=token,
            body={"project_id": project_id, "stage": stage, "decision": "GRANT"},
        )
        if code != 200:
            fail(f"approve {stage} HTTP {code}: {approved}")
        print(f"  OK - approved {stage}")

    print("\n[4] completed pipeline visualization")
    final = wait_status(api_base, token, project_id, want_status="COMPLETED", timeout=30)
    log_dashboard_view(final)
    if final.get("status") != "COMPLETED":
        fail(f"expected COMPLETED, got {final}")
    print("  OK - stepper all-done; Start Pipeline re-enabled; badge COMPLETED")

    print("\nPASS - M2 stub pipeline E2E (US-07 + US-08 + US-10 dashboard contract).")


if __name__ == "__main__":
    main()
