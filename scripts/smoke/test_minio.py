#!/usr/bin/env python3
"""T-02-03 smoke test — MinIO persistent volume and bucket init.

Verifies acceptance criteria for issue #46 against an **ephemeral** compose
project (#70 / TD-08). Does not touch the developer's running stack or `.env`.

Usage (from repo root):
    python scripts/smoke/test_minio.py
"""
from __future__ import annotations

import argparse
import os
import subprocess
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

MC_IMAGE = "minio/mc:RELEASE.2025-08-13T08-35-41Z"
MARKER_OBJECT = "smoke/persistence.txt"
MARKER_VALUE = "aimpos-t0203"
VOLUME_SUFFIX = "aimpos-minio-data"


def project_network(project: str) -> str:
    return f"{project}_aimpos-spark"


def service_container_id(project: str, env_path: Path, service: str, *, all_states: bool = False) -> str:
    ps_args = ["ps", "-a" if all_states else "", "-q", service]
    ps_args = [a for a in ps_args if a]
    result = run(compose_args(project, env_path, *ps_args))
    cid = result.stdout.strip().splitlines()
    if result.returncode != 0 or not cid:
        fail(f"could not resolve container id for service `{service}`")
    return cid[-1]


def mc(project: str, env: dict[str, str], script: str) -> subprocess.CompletedProcess[str]:
    network = project_network(project)
    endpoint = env.get("MINIO_ENDPOINT", "minio:9000")
    prelude = (
        f'mc alias set local "http://{endpoint}" '
        f'"{env["MINIO_ROOT_USER"]}" "{env["MINIO_ROOT_PASSWORD"]}" >/dev/null'
    )
    return run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            network,
            "--entrypoint",
            "sh",
            MC_IMAGE,
            "-c",
            f"{prelude} && {script}",
        ]
    )


def wait_minio_healthy(project: str, env_path: Path, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        cid = service_container_id(project, env_path, "minio")
        last = run(["docker", "inspect", "-f", "{{.State.Health.Status}}", cid]).stdout.strip()
        if last == "healthy":
            return
        time.sleep(3)
    fail(f"minio not healthy within {timeout}s (last: {last or 'unknown'})")


def wait_init_complete(project: str, env_path: Path, timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = run(compose_args(project, env_path, "ps", "-a", "-q", "minio-init"))
        cid_lines = result.stdout.strip().splitlines()
        if not cid_lines:
            time.sleep(2)
            continue
        cid = cid_lines[-1]
        status = run(["docker", "inspect", "-f", "{{.State.Status}}", cid]).stdout.strip()
        if status == "exited":
            code = run(["docker", "inspect", "-f", "{{.State.ExitCode}}", cid]).stdout.strip()
            if code != "0":
                logs = run(["docker", "logs", cid]).stdout.strip()
                fail(f"minio-init exited with code {code}:\n{logs}")
            return
        time.sleep(2)
    fail("minio-init did not complete within timeout")


def main() -> int:
    parser = argparse.ArgumentParser(description="T-02-03 MinIO smoke test (hermetic)")
    args = parser.parse_args()

    if not COMPOSE_FILE.exists():
        fail(f"compose file not found: {COMPOSE_FILE}")
    if run(["docker", "version"]).returncode != 0:
        fail("Docker is not available. Start Docker Desktop and retry.")

    env = load_env_example()
    project = ephemeral_project("aimpos-minio-smoke")
    env_handle = write_temp_env(env)
    env_path = Path(env_handle.name)
    bucket = env["MINIO_BUCKET"]
    volume_name = f"{project}_{VOLUME_SUFFIX}"

    print(f"Target: {COMPOSE_FILE.name}  project={project}  bucket={bucket}\n")

    try:
        print("[setup] Starting minio + minio-init in ephemeral project...")
        if run(compose_args(project, env_path, "up", "-d", "minio", "minio-init")).returncode != 0:
            fail("`docker compose up -d minio minio-init` failed")
        wait_minio_healthy(project, env_path)
        wait_init_complete(project, env_path)
        print("  OK - minio healthy, init completed\n")

        print("[AC3] S3 API reachable from the compose network...")
        if mc(project, env, "mc ls local >/dev/null").returncode != 0:
            fail("could not reach the S3 API from the network")
        print("  OK - S3 API reachable")

        print(f"[AC2] bucket '{bucket}' exists after startup...")
        if mc(project, env, f"mc ls local/{bucket} >/dev/null").returncode != 0:
            fail(f"bucket '{bucket}' not found")
        print("  OK - bucket present")

        print("[AC4] init script is idempotent...")
        if run(compose_args(project, env_path, "up", "-d", "--no-deps", "--force-recreate", "minio-init")).returncode != 0:
            fail("re-running minio-init failed to start")
        wait_init_complete(project, env_path)
        count = mc(project, env, "mc ls local | wc -l").stdout.strip()
        print(f"  OK - init re-ran cleanly; bucket count = {count}")

        print("[AC1] persistent volume across recreation...")
        if mc(project, env, f'printf "{MARKER_VALUE}" | mc pipe local/{bucket}/{MARKER_OBJECT}').returncode != 0:
            fail("could not write marker object")
        print("  wrote marker object; recreating services (volume retained)...")
        run(compose_args(project, env_path, "rm", "-sf", "minio", "minio-init"))
        if run(compose_args(project, env_path, "up", "-d", "minio", "minio-init")).returncode != 0:
            fail("restart failed")
        wait_minio_healthy(project, env_path)
        wait_init_complete(project, env_path)
        survived = mc(project, env, f"mc cat local/{bucket}/{MARKER_OBJECT}").stdout.strip()
        if survived != MARKER_VALUE:
            fail(f"marker object did not survive recreation (got '{survived}')")
        if run(["docker", "volume", "inspect", volume_name]).returncode != 0:
            fail(f"named volume `{volume_name}` not found")
        print(f"  OK - object survived; volume `{volume_name}` persists\n")

        mc(project, env, f"mc rm local/{bucket}/{MARKER_OBJECT} >/dev/null 2>&1 || true")
        print("\nPASS - all T-02-03 acceptance criteria verified (hermetic project).")
        return 0
    finally:
        print(f"[teardown] Removing ephemeral project `{project}` and volumes...")
        teardown_project(project, env_path)
        env_handle.close()
        if env_path.exists():
            os.unlink(env_path)


if __name__ == "__main__":
    raise SystemExit(main())
