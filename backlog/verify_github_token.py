"""Verify GitHub token can access the AIMPOS repo and create issues."""
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "smcshahid/ai-media-production-os"


def api(token: str, path: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "aimpos-verify",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("No token found. In PowerShell run:")
        print('  $env:GITHUB_TOKEN = "ghp_your_token_here"')
        print("Then run this script again.")
        return 1

    try:
        user = api(token, "/user")
        repo = api(token, f"/repos/{REPO}")
        perms = repo.get("permissions", {})
        print(f"OK — logged in as: {user['login']}")
        print(f"OK — repo access: {REPO} ({repo['visibility']})")
        print(f"     admin={perms.get('admin')} push={perms.get('push')} pull={perms.get('pull')}")
        if not perms.get("push"):
            print("WARN — token may lack repo scope; issue import might fail.")
        else:
            print("OK — ready for issue import (Step 2).")
        return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAIL — HTTP {e.code}: {body}")
        if e.code == 401:
            print("Tip: token expired or wrong. Create a new one at:")
            print("  https://github.com/settings/tokens")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
