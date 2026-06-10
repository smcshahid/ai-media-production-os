"""Shared helpers for hermetic compose smoke tests (TD-02 / #70).

Smoke tests use an ephemeral Compose project name and a temporary env file so
they never touch the developer's running stack or working-tree `.env`.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "deploy" / "compose" / "docker-compose.yml"
ENV_EXAMPLE = ROOT / ".env.example"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def ephemeral_project(prefix: str = "aimpos-smoke") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def compose_args(project: str, env_file: Path, *args: str) -> list[str]:
    return [
        "docker",
        "compose",
        "-p",
        project,
        "-f",
        str(COMPOSE_FILE),
        "--env-file",
        str(env_file),
        *args,
    ]


def load_env_example() -> dict[str, str]:
    if not ENV_EXAMPLE.exists():
        fail(f"{ENV_EXAMPLE} not found")
    env: dict[str, str] = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def write_temp_env(env: dict[str, str]) -> tempfile.NamedTemporaryFile[str]:
    """Return a NamedTemporaryFile (caller must close/delete)."""
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".env",
        prefix="aimpos-smoke-",
        delete=False,
        encoding="utf-8",
    )
    for key, value in env.items():
        handle.write(f"{key}={value}\n")
    handle.flush()
    return handle


def teardown_project(project: str, env_path: Path) -> None:
    run(compose_args(project, env_path, "down", "-v"))
