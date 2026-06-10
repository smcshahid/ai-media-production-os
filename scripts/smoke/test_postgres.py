#!/usr/bin/env python3
"""T-02-02 smoke test — PostgreSQL volume and init scripts.

Verifies the four acceptance criteria for issue #45 against an **ephemeral**
compose project (#70 / TD-02): isolated project name, temp env file, teardown
with `down -v`. Does not touch the developer's running stack or `.env`.

  AC1  Named volume persists data across restarts.
  AC2  PostgreSQL is internal-only in the base compose (no host 5432 publish).
  AC3  Init created the database, user, and extensions.
  AC4  psql from the compose network succeeds.

Usage (from repo root):
    python scripts/smoke/test_postgres.py
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from _compose import (
    COMPOSE_FILE,
    compose_args,
    ephemeral_project,
    fail,
    load_env_example,
    run,
    teardown_project,
    write_temp_env,
)

PG_IMAGE = "postgres:16-alpine"
MARKER_TABLE = "aimpos_smoke_marker"
VOLUME_SUFFIX = "aimpos-postgres-data"


def project_network(project: str) -> str:
    return f"{project}_aimpos-spark"


def service_container_id(project: str, env_path: Path, service: str) -> str:
    result = run(compose_args(project, env_path, "ps", "-q", service))
    cid = result.stdout.strip().splitlines()
    if result.returncode != 0 or not cid:
        fail(f"could not resolve container id for service `{service}` in project `{project}`")
    return cid[0]


def psql(project: str, env_path: Path, env: dict[str, str], sql: str) -> str:
    network = project_network(project)
    result = run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            network,
            "-e",
            f"PGPASSWORD={env['POSTGRES_PASSWORD']}",
            PG_IMAGE,
            "psql",
            "-h",
            "postgresql",
            "-U",
            env["POSTGRES_USER"],
            "-d",
            env["POSTGRES_DB"],
            "-tAc",
            sql,
        ]
    )
    if result.returncode != 0:
        fail(f"psql failed for `{sql}`:\n{result.stderr.strip()}")
    return result.stdout.strip()


def wait_healthy(project: str, env_path: Path, timeout: int = 120) -> str:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        cid = service_container_id(project, env_path, "postgresql")
        result = run(["docker", "inspect", "-f", "{{.State.Health.Status}}", cid])
        last = result.stdout.strip()
        if last == "healthy":
            return cid
        time.sleep(3)
    fail(f"postgresql did not become healthy within {timeout}s (last: {last or 'unknown'})")


def main() -> int:
    parser = argparse.ArgumentParser(description="T-02-02 PostgreSQL smoke test (hermetic)")
    args = parser.parse_args()

    if not COMPOSE_FILE.exists():
        fail(f"compose file not found: {COMPOSE_FILE}")
    if run(["docker", "version"]).returncode != 0:
        fail("Docker is not available. Start Docker Desktop and retry.")

    env = load_env_example()
    project = ephemeral_project("aimpos-pg-smoke")
    env_handle = write_temp_env(env)
    env_path = Path(env_handle.name)
    volume_name = f"{project}_{VOLUME_SUFFIX}"

    print(f"Target: {COMPOSE_FILE.name}  project={project}  db={env['POSTGRES_DB']}\n")

    try:
        print("[setup] Starting postgresql in ephemeral project...")
        if run(compose_args(project, env_path, "up", "-d", "postgresql")).returncode != 0:
            fail("`docker compose up -d postgresql` failed")
        wait_healthy(project, env_path)
        print("  OK - container healthy\n")

        print("[AC4] psql connection from the compose network...")
        if psql(project, env_path, env, "SELECT 1") != "1":
            fail("SELECT 1 did not return 1")
        print("  OK - psql connected over the internal network")

        print("[AC3] database, user, and extensions created by init...")
        extensions = set(psql(project, env_path, env, "SELECT extname FROM pg_extension").splitlines())
        missing = {"uuid-ossp", "pgcrypto"} - extensions
        if missing:
            fail(f"missing extensions from 01-extensions.sql: {sorted(missing)}")
        print("  OK - extensions present: uuid-ossp, pgcrypto")

        print("[AC2] PostgreSQL is internal-only (host port 5432 not published)...")
        cid = service_container_id(project, env_path, "postgresql")
        ports = run(["docker", "port", cid]).stdout.strip()
        if "5432" in ports:
            fail(f"host port mapping found (expected none in base compose):\n{ports}")
        print("  OK - no host port binding in base compose")

        print("[AC1] named volume persists data across recreation...")
        psql(
            project,
            env_path,
            env,
            f"CREATE TABLE IF NOT EXISTS {MARKER_TABLE} (id int primary key); "
            f"INSERT INTO {MARKER_TABLE} (id) VALUES (42) ON CONFLICT DO NOTHING;",
        )
        print("  wrote marker row; recreating service (volume retained)...")
        run(compose_args(project, env_path, "rm", "-sf", "postgresql"))
        if run(compose_args(project, env_path, "up", "-d", "postgresql")).returncode != 0:
            fail("restart `up -d postgresql` failed")
        wait_healthy(project, env_path)
        survived = psql(project, env_path, env, f"SELECT id FROM {MARKER_TABLE} WHERE id = 42")
        if survived != "42":
            fail("marker row did not survive recreation - volume did not persist")
        if run(["docker", "volume", "inspect", volume_name]).returncode != 0:
            fail(f"named volume `{volume_name}` not found")
        print(f"  OK - marker survived; volume `{volume_name}` persists\n")

        psql(project, env_path, env, f"DROP TABLE IF EXISTS {MARKER_TABLE}")
        print("\nPASS - all T-02-02 acceptance criteria verified (hermetic project).")
        return 0
    finally:
        print(f"[teardown] Removing ephemeral project `{project}` and volumes...")
        teardown_project(project, env_path)
        env_handle.close()
        if env_path.exists():
            os.unlink(env_path)


if __name__ == "__main__":
    raise SystemExit(main())
