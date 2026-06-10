#!/usr/bin/env python3
"""US-11 E2E — POST /ideas stores idea.txt v1 and lists under stage IDEA.

Requires running compose: api, postgresql, minio.

Usage (from repo root):
    python scripts/smoke/test_ideas.py

Exit codes:
    0  PASS
    1  FAIL
    2  SKIP
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
_PARAGRAPH = (
    "A lone astronaut discovers a hidden garden on Mars and must decide "
    "whether to share it with Earth."
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str) -> None:
    print(f"SKIP: {msg}")
    print("SKIP - ideas smoke not run. This is not PASS.")
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
) -> tuple[int, dict | list]:
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

    print("\n[2] POST /ideas")
    code, created = http_json(
        "POST",
        f"{api_base}/ideas",
        token=token,
        body={
            "project_id": project_id,
            "title": "Mars Garden",
            "paragraph": _PARAGRAPH,
            "style_note": "cinematic sci-fi",
        },
    )
    if code != 201:
        fail(f"POST /ideas HTTP {code}: {created}")
    assert isinstance(created, dict)
    print(f"  OK - stage={created.get('stage')} version={created.get('version')}")
    if created.get("metadata_json") != {"style_note": "cinematic sci-fi"}:
        fail(f"unexpected metadata_json: {created.get('metadata_json')}")

    print("\n[3] GET /assets lists IDEA")
    code, assets = http_json(
        "GET",
        f"{api_base}/assets?project_id={project_id}",
        token=token,
    )
    if code != 200:
        fail(f"GET /assets HTTP {code}")
    assert isinstance(assets, list)
    idea_rows = [row for row in assets if row.get("stage") == "IDEA"]
    if not idea_rows:
        fail("no IDEA assets listed")
    print(f"  OK - IDEA versions={len(idea_rows)} latest=v{idea_rows[0].get('version')}")

    print("\n[4] validation — short paragraph returns 422")
    code, _ = http_json(
        "POST",
        f"{api_base}/ideas",
        token=token,
        body={
            "project_id": project_id,
            "title": "Too Short",
            "paragraph": "nope",
        },
    )
    if code != 422:
        fail(f"expected 422 for short paragraph, got {code}")
    print("  OK - 422 on short paragraph")

    print("\nPASS - US-11 idea capture E2E.")


if __name__ == "__main__":
    main()
