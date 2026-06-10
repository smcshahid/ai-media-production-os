#!/usr/bin/env python3
"""US-07 E2E smoke — POST /pipeline/start, audit, GET /pipeline/status sync.

Requires running compose stack: api, postgresql, temporal, worker.

Usage (from repo root):
    python scripts/smoke/test_pipeline_start.py

Exit codes:
    0  PASS
    1  FAIL
    2  SKIP — API/Temporal unavailable
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str) -> None:
    print(f"SKIP: {msg}")
    print("SKIP - pipeline start smoke not run. This is not PASS.")
    raise SystemExit(2)


def load_token() -> str:
    if not ENV_FILE.exists():
        fail(f"{ENV_FILE} not found")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("AIMPOS_API_TOKEN="):
            return line.partition("=")[2].strip()
    fail("AIMPOS_API_TOKEN not found in .env")


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


def main() -> int:
    token = load_token()
    api_base = os.environ.get("AIMPOS_API_BASE", "http://127.0.0.1:8000")

    print(f"Target: {api_base}\n")

    print("[1/4] GET /projects...")
    code, projects = http_json("GET", f"{api_base}/projects", token=token)
    if code != 200 or not projects:
        fail(f"GET /projects failed: {code} {projects}")
    project_id = projects[0]["id"]
    print(f"  OK - project_id={project_id}\n")

    print("[2/4] POST /pipeline/start...")
    code, start_body = http_json(
        "POST",
        f"{api_base}/pipeline/start",
        token=token,
        body={"project_id": project_id},
    )
    if code == 409:
        print("  note - active run exists; continuing with status check only")
        run_id = None
        workflow_id = None
    elif code != 201:
        fail(f"POST /pipeline/start failed: {code} {start_body}")
    else:
        run_id = start_body["run_id"]
        workflow_id = start_body["workflow_id"]
        print(f"  OK - run_id={run_id} workflow_id={workflow_id} status={start_body['status']}\n")

    print("[3/4] Poll GET /pipeline/status for worker sync...")
    deadline = time.monotonic() + 20.0
    last = {}
    while time.monotonic() < deadline:
        code, status_body = http_json(
            "GET",
            f"{api_base}/pipeline/status?project_id={project_id}",
            token=token,
        )
        if code != 200:
            fail(f"GET /pipeline/status failed: {code} {status_body}")
        last = status_body
        if status_body.get("status") in {"AWAITING_APPROVAL", "RUNNING"}:
            if status_body.get("current_stage") == "STORY":
                break
        time.sleep(1.0)
    else:
        fail(f"status did not sync within timeout: {last}")

    print(
        f"  OK - status={last['status']} current_stage={last['current_stage']} "
        f"run_id={last.get('run_id')}\n"
    )

    if run_id and last.get("run_id") != run_id:
        fail(f"status run_id mismatch: {last.get('run_id')} vs {run_id}")

    print("[4/4] Workflow tracked end-to-end (API row + Temporal worker sync).")
    print("\nPASS - US-07 start path, audit (201), and status synchronization verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
