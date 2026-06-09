#!/usr/bin/env python3
"""T-02-02 smoke test — PostgreSQL volume and init scripts.

Verifies the four acceptance criteria for issue #45 against the Sprint-0
compose stack, using only the standard library and the Docker CLI:

  AC1  Named volume `aimpos-postgres-data` persists data across restarts.
  AC2  PostgreSQL is reachable on the internal network, not published by
       the base compose file (host port 5432 is NOT bound).
  AC3  Init created the database and user matching `.env.example`, and the
       `uuid-ossp` / `pgcrypto` extensions are present.
  AC4  A `psql` connection from the `aimpos-spark` (api) network succeeds.

Usage (from repo root):
    python scripts/smoke/test_postgres.py
    python scripts/smoke/test_postgres.py --down   # tear stack down at the end

Requires Docker (Docker Desktop on Windows). Exits non-zero on any failure.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "deploy" / "compose" / "docker-compose.yml"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

NETWORK = "aimpos-spark"
CONTAINER = "aimpos-postgresql"
VOLUME = "aimpos-postgres-data"
PG_IMAGE = "postgres:16-alpine"
MARKER_TABLE = "aimpos_smoke_marker"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def compose(*args: str) -> list[str]:
    return [
        "docker", "compose",
        "-f", str(COMPOSE_FILE),
        "--env-file", str(ENV_FILE),
        *args,
    ]


def load_env() -> dict[str, str]:
    """Read POSTGRES_* from .env, creating it from .env.example if absent."""
    if not ENV_FILE.exists():
        if not ENV_EXAMPLE.exists():
            fail(f"Neither {ENV_FILE} nor {ENV_EXAMPLE} exists.")
        ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  note: created {ENV_FILE.name} from {ENV_EXAMPLE.name}")
    env: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    for required in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
        if not env.get(required):
            fail(f"{required} missing from {ENV_FILE}")
    return env


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def psql(env: dict[str, str], sql: str) -> str:
    """Run a SQL command from a one-off client container on the api network."""
    result = run([
        "docker", "run", "--rm",
        "--network", NETWORK,
        "-e", f"PGPASSWORD={env['POSTGRES_PASSWORD']}",
        PG_IMAGE,
        "psql", "-h", "postgresql", "-U", env["POSTGRES_USER"],
        "-d", env["POSTGRES_DB"], "-tAc", sql,
    ])
    if result.returncode != 0:
        fail(f"psql failed for `{sql}`:\n{result.stderr.strip()}")
    return result.stdout.strip()


def wait_healthy(timeout: int = 120) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        result = run(["docker", "inspect", "-f", "{{.State.Health.Status}}", CONTAINER])
        last = result.stdout.strip()
        if last == "healthy":
            return
        time.sleep(3)
    fail(f"{CONTAINER} did not become healthy within {timeout}s (last status: {last or 'unknown'})")


def main() -> int:
    parser = argparse.ArgumentParser(description="T-02-02 PostgreSQL smoke test")
    parser.add_argument("--down", action="store_true", help="docker compose down at the end")
    args = parser.parse_args()

    if not COMPOSE_FILE.exists():
        fail(f"compose file not found: {COMPOSE_FILE}")
    if run(["docker", "version"]).returncode != 0:
        fail("Docker is not available. Start Docker Desktop and retry.")

    env = load_env()
    print(f"Target: {COMPOSE_FILE.relative_to(ROOT)}  (db={env['POSTGRES_DB']}, user={env['POSTGRES_USER']})\n")

    print("[setup] Starting postgresql service...")
    if run(compose("up", "-d", "postgresql")).returncode != 0:
        fail("`docker compose up -d postgresql` failed")
    wait_healthy()
    print("  OK - container healthy\n")

    # AC4 + AC3: psql connects from the api network; db/user/extensions exist.
    print("[AC4] psql connection from the aimpos-spark (api) network...")
    if psql(env, "SELECT 1") != "1":
        fail("SELECT 1 did not return 1")
    print("  OK - psql connected over the internal network")

    print("[AC3] database, user, and extensions created by init...")
    extensions = set(psql(env, "SELECT extname FROM pg_extension").splitlines())
    missing = {"uuid-ossp", "pgcrypto"} - extensions
    if missing:
        fail(f"missing extensions from 01-extensions.sql: {sorted(missing)}")
    print(f"  OK - extensions present: uuid-ossp, pgcrypto")

    # AC2: base compose must not publish 5432 to the host.
    print("[AC2] PostgreSQL is internal-only (host port 5432 not published)...")
    ports = run(["docker", "port", CONTAINER]).stdout.strip()
    if "5432" in ports:
        fail(f"host port mapping found (expected none in base compose):\n{ports}")
    print("  OK - no host port binding in base compose")

    # AC1: data survives container recreation on the named volume.
    print("[AC1] named volume persists data across recreation...")
    psql(env, f"CREATE TABLE IF NOT EXISTS {MARKER_TABLE} (id int primary key); "
              f"INSERT INTO {MARKER_TABLE} (id) VALUES (42) ON CONFLICT DO NOTHING;")
    print("  wrote marker row; recreating containers (volume retained)...")
    run(compose("down"))  # no -v: keeps the named volume
    if run(compose("up", "-d", "postgresql")).returncode != 0:
        fail("restart `up -d postgresql` failed")
    wait_healthy()
    survived = psql(env, f"SELECT id FROM {MARKER_TABLE} WHERE id = 42")
    if survived != "42":
        fail("marker row did not survive recreation - volume did not persist")
    vol = run(["docker", "volume", "inspect", VOLUME])
    if vol.returncode != 0:
        fail(f"named volume `{VOLUME}` not found")
    print(f"  OK - marker survived; named volume `{VOLUME}` persists\n")

    # Cleanup the marker so reruns stay clean; keep the stack up by default.
    psql(env, f"DROP TABLE IF EXISTS {MARKER_TABLE}")
    if args.down:
        run(compose("down"))
        print("[teardown] stack stopped (--down).")
    else:
        print("[done] stack left running. Stop it with: make down")

    print("\nPASS - all T-02-02 acceptance criteria verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
