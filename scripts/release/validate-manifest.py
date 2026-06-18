#!/usr/bin/env python3
"""Validate deploy/release/manifest.yaml structure (Phase 8 CI gate)."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("SKIP: PyYAML not installed")
    sys.exit(0)

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "deploy" / "release" / "manifest.yaml"


def main() -> int:
    if not MANIFEST.is_file():
        print(f"FAIL: missing {MANIFEST}")
        return 1

    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    fail = 0

    version = data.get("release", {}).get("version")
    if not version or not str(version).startswith("v"):
        print("FAIL: release.version must be semver tag")
        fail = 1
    else:
        print(f"PASS release.version={version}")

    for svc in ("api", "web", "worker"):
        img = data.get("images", {}).get(svc, {})
        tag = img.get("tag")
        repo = img.get("repository")
        if not tag or not repo:
            print(f"FAIL: images.{svc} incomplete")
            fail = 1
        elif tag != version:
            print(f"FAIL: images.{svc}.tag {tag} != release.version {version}")
            fail = 1
        else:
            print(f"PASS images.{svc}={repo}:{tag}")

    alembic = data.get("database", {}).get("alembic_head")
    if not alembic or not str(alembic).isdigit():
        print(f"FAIL: database.alembic_head must be set (got {alembic!r})")
        fail = 1
    else:
        print(f"PASS alembic_head={alembic}")

    scripts = data.get("verify", {}).get("scripts", [])
    for rel in scripts:
        path = REPO / rel.replace("/", "\\") if sys.platform == "win32" else REPO / rel
        if not path.is_file():
            print(f"FAIL: verify script missing: {rel}")
            fail = 1
    if fail == 0:
        print(f"PASS {len(scripts)} verify scripts exist")

    print(f"DONE fail={fail}")
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
