"""Resolve GitHub API token from env or gh CLI keyring."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


def resolve_token() -> str | None:
    """Return token from GITHUB_TOKEN, GH_TOKEN, or `gh auth token`."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()
    if not shutil.which("gh"):
        return None
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None
    token = result.stdout.strip()
    return token or None


def require_token() -> str:
    token = resolve_token()
    if token:
        return token
    print(
        "No GitHub token found. Run once:\n"
        "  gh auth login -h github.com -p ssh -w\n"
        "Or set GITHUB_TOKEN / GH_TOKEN.",
        file=sys.stderr,
    )
    raise SystemExit(1)
