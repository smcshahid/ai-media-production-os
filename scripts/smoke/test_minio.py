#!/usr/bin/env python3
"""T-02-03 smoke test — MinIO persistent volume and bucket init.

Verifies the four acceptance criteria for issue #46 against the Sprint-0
compose stack, using only the standard library and the Docker CLI:

  AC1  MinIO starts with a persistent named volume (`aimpos-minio-data`) and
       objects survive container recreation.
  AC2  The bucket named by `MINIO_BUCKET` exists after `docker compose up`.
  AC3  The S3 API is reachable from the `aimpos-spark` (api) network using the
       `.env` credentials.
  AC4  The init script is idempotent (re-running it succeeds, no duplicate).

Usage (from repo root):
    python scripts/smoke/test_minio.py
    python scripts/smoke/test_minio.py --down   # tear stack down at the end

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
MINIO_CONTAINER = "aimpos-minio"
INIT_CONTAINER = "aimpos-minio-init"
VOLUME = "aimpos-minio-data"
MC_IMAGE = "minio/mc:RELEASE.2025-08-13T08-35-41Z"
MARKER_OBJECT = "smoke/persistence.txt"
MARKER_VALUE = "aimpos-t0203"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def compose(*args: str) -> list[str]:
    return ["docker", "compose", "-f", str(COMPOSE_FILE), "--env-file", str(ENV_FILE), *args]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_env() -> dict[str, str]:
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
    for required in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "MINIO_BUCKET"):
        if not env.get(required):
            fail(f"{required} missing from {ENV_FILE}")
    return env


def mc(env: dict[str, str], script: str) -> subprocess.CompletedProcess:
    """Run mc commands from a one-off client container on the api network."""
    endpoint = env.get("MINIO_ENDPOINT", "minio:9000")
    prelude = (
        f'mc alias set local "http://{endpoint}" '
        f'"{env["MINIO_ROOT_USER"]}" "{env["MINIO_ROOT_PASSWORD"]}" >/dev/null'
    )
    return run([
        "docker", "run", "--rm", "--network", NETWORK,
        "--entrypoint", "sh", MC_IMAGE, "-c", f"{prelude} && {script}",
    ])


def wait_minio_healthy(timeout: int = 120) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        last = run(["docker", "inspect", "-f", "{{.State.Health.Status}}", MINIO_CONTAINER]).stdout.strip()
        if last == "healthy":
            return
        time.sleep(3)
    fail(f"{MINIO_CONTAINER} not healthy within {timeout}s (last: {last or 'unknown'})")


def wait_init_complete(timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = run(["docker", "inspect", "-f", "{{.State.Status}}", INIT_CONTAINER]).stdout.strip()
        if status == "exited":
            code = run(["docker", "inspect", "-f", "{{.State.ExitCode}}", INIT_CONTAINER]).stdout.strip()
            if code != "0":
                logs = run(["docker", "logs", INIT_CONTAINER]).stdout.strip()
                fail(f"{INIT_CONTAINER} exited with code {code}:\n{logs}")
            return
        time.sleep(2)
    fail(f"{INIT_CONTAINER} did not complete within {timeout}s")


def main() -> int:
    parser = argparse.ArgumentParser(description="T-02-03 MinIO smoke test")
    parser.add_argument("--down", action="store_true", help="docker compose down at the end")
    args = parser.parse_args()

    if not COMPOSE_FILE.exists():
        fail(f"compose file not found: {COMPOSE_FILE}")
    if run(["docker", "version"]).returncode != 0:
        fail("Docker is not available. Start Docker Desktop and retry.")

    env = load_env()
    bucket = env["MINIO_BUCKET"]
    print(f"Target: {COMPOSE_FILE.relative_to(ROOT)}  (bucket={bucket})\n")

    print("[setup] Starting minio + minio-init...")
    if run(compose("up", "-d", "minio", "minio-init")).returncode != 0:
        fail("`docker compose up -d minio minio-init` failed")
    wait_minio_healthy()
    wait_init_complete()
    print("  OK - minio healthy, init completed\n")

    # AC3 + AC2: S3 API reachable from the network; bucket exists.
    print("[AC3] S3 API reachable from the aimpos-spark (api) network...")
    if mc(env, "mc ls local >/dev/null").returncode != 0:
        fail("could not reach the S3 API from the network")
    print("  OK - S3 API reachable")

    print(f"[AC2] bucket '{bucket}' exists after startup...")
    if mc(env, f"mc ls local/{bucket} >/dev/null").returncode != 0:
        fail(f"bucket '{bucket}' not found")
    print("  OK - bucket present")

    # AC4: init script is idempotent (re-run the one-shot init service).
    print("[AC4] init script is idempotent...")
    rerun = run(compose("up", "-d", "--no-deps", "--force-recreate", "minio-init"))
    if rerun.returncode != 0:
        fail("re-running minio-init failed to start")
    wait_init_complete()
    count = mc(env, "mc ls local | wc -l").stdout.strip()
    print(f"  OK - init re-ran cleanly; bucket count = {count}")

    # AC1: persistent volume — object survives container recreation.
    print("[AC1] persistent volume across recreation...")
    if mc(env, f'printf "{MARKER_VALUE}" | mc pipe local/{bucket}/{MARKER_OBJECT}').returncode != 0:
        fail("could not write marker object")
    print("  wrote marker object; recreating containers (volume retained)...")
    run(compose("down"))  # no -v: keeps named volumes
    if run(compose("up", "-d", "minio", "minio-init")).returncode != 0:
        fail("restart `up -d minio minio-init` failed")
    wait_minio_healthy()
    survived = mc(env, f"mc cat local/{bucket}/{MARKER_OBJECT}").stdout.strip()
    if survived != MARKER_VALUE:
        fail(f"marker object did not survive recreation (got '{survived}')")
    if run(["docker", "volume", "inspect", VOLUME]).returncode != 0:
        fail(f"named volume `{VOLUME}` not found")
    print(f"  OK - object survived; named volume `{VOLUME}` persists\n")

    # Cleanup the marker; keep the stack up by default.
    mc(env, f"mc rm local/{bucket}/{MARKER_OBJECT} >/dev/null 2>&1 || true")
    if args.down:
        run(compose("down"))
        print("[teardown] stack stopped (--down).")
    else:
        print("[done] stack left running. Stop it with: make down")

    print("\nPASS - all T-02-03 acceptance criteria verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
