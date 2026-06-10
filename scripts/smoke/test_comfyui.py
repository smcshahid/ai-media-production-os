#!/usr/bin/env python3
"""T-06-02 smoke test — ComfyUI SDXL workflow and MinIO PNG upload.

Verifies acceptance criteria for issue #61:
  - PASS (exit 0): workflow runs, valid PNG uploaded to MinIO bucket
  - SKIP (exit 2): ComfyUI/MinIO/GPU unavailable — documented, not a pass
  - FAIL (exit 1): services reachable but workflow/upload failed

Honours D-08: optionally unloads Ollama before ComfyUI when both are reachable.

Usage (from repo root):
    python scripts/smoke/test_comfyui.py
    python scripts/smoke/test_comfyui.py --require-live
    python scripts/smoke/test_comfyui.py --host http://127.0.0.1:8188

Exit codes:
    0  PASS — PNG generated and stored in MinIO
    1  FAIL — service available but test failed
    2  SKIP — prerequisites unavailable
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from _compose import ENV_EXAMPLE, load_env_example

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_JSON = ROOT / "configs" / "comfyui" / "workflows" / "sdxl_storyboard.json"
DEFAULT_COMFY_HOST = "http://127.0.0.1:8188"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MINIO_HOST = "127.0.0.1:9000"
MC_IMAGE = "minio/mc:RELEASE.2025-08-13T08-35-41Z"
GENERATE_TIMEOUT_S = 180
MINIO_OBJECT = "smoke/comfyui/sdxl_storyboard.png"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str, *, require_live: bool) -> None:
    line = f"SKIP: {msg}"
    if require_live:
        fail(f"--require-live set; {msg}")
    print(line)
    print("SKIP - ComfyUI smoke not run (GPU/service unavailable). This is not PASS.")
    raise SystemExit(2)


def normalize_host(host: str) -> str:
    host = host.strip().rstrip("/")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return host


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 15) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def http_bytes(url: str, timeout: float = 30) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def load_workflow() -> dict:
    if not WORKFLOW_JSON.exists():
        fail(f"workflow not found: {WORKFLOW_JSON}")
    return json.loads(WORKFLOW_JSON.read_text(encoding="utf-8"))


def try_unload_ollama(ollama_host: str, model: str) -> None:
    """D-08: best-effort Ollama unload before ComfyUI (no-op if Ollama down)."""
    try:
        http_json(
            "POST",
            f"{ollama_host}/api/generate",
            body={"model": model, "prompt": "", "keep_alive": 0},
            timeout=10,
        )
        print(f"  OK - requested Ollama unload for `{model}`")
    except (urllib.error.URLError, TimeoutError):
        print("  note - Ollama not reachable; skipping unload step")


def queue_prompt(host: str, workflow: dict) -> str:
    payload = http_json("POST", f"{host}/prompt", body={"prompt": workflow}, timeout=30)
    prompt_id = payload.get("prompt_id")
    if not prompt_id:
        fail(f"/prompt did not return prompt_id: {payload}")
    return str(prompt_id)


def wait_for_image(host: str, prompt_id: str, timeout: int) -> tuple[str, str, str]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        history = http_json("GET", f"{host}/history/{prompt_id}", timeout=15)
        entry = history.get(prompt_id)
        if entry and entry.get("outputs"):
            for node_out in entry["outputs"].values():
                images = node_out.get("images") or []
                if images:
                    img = images[0]
                    return (
                        str(img["filename"]),
                        str(img.get("subfolder", "")),
                        str(img.get("type", "output")),
                    )
        time.sleep(2)
    fail(f"no output image within {timeout}s for prompt_id={prompt_id}")
    raise AssertionError("unreachable")


def is_png(data: bytes) -> bool:
    return len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n"


def mc_minio_host(endpoint: str) -> str:
    """Map host-local MinIO to host.docker.internal for mc sidecar containers."""
    host_port = endpoint.replace("http://", "").replace("https://", "")
    host, _, port = host_port.partition(":")
    if host in {"127.0.0.1", "localhost"}:
        return f"host.docker.internal:{port or '9000'}"
    return host_port


def upload_png_to_minio(
    png: bytes,
    *,
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    object_key: str,
) -> None:
    host_port = mc_minio_host(endpoint)
    result = subprocess_run_mc(
        png,
        (
            f'mc alias set local "http://{host_port}" "{access_key}" "{secret_key}" >/dev/null && '
            "cat > /tmp/upload.png && "
            f'mc cp /tmp/upload.png "local/{bucket}/{object_key}"'
        ),
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"MinIO upload failed:\n{stderr}")


def subprocess_run_mc(png: bytes | None, shell_script: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        "docker",
        "run",
        "--rm",
        "--add-host",
        "host.docker.internal:host-gateway",
        "--entrypoint",
        "sh",
        MC_IMAGE,
        "-c",
        shell_script,
    ]
    if png is not None:
        cmd.insert(2, "-i")
    return subprocess.run(cmd, input=png, text=False, capture_output=True)


def verify_minio_object(
    *,
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    object_key: str,
) -> None:
    host_port = mc_minio_host(endpoint)
    result = subprocess_run_mc(
        None,
        (
            f'mc alias set local "http://{host_port}" "{access_key}" "{secret_key}" >/dev/null && '
            f'mc stat "local/{bucket}/{object_key}"'
        ),
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"MinIO object not found after upload:\n{stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description="T-06-02 ComfyUI SDXL smoke test")
    parser.add_argument("--host", default=DEFAULT_COMFY_HOST, help="ComfyUI base URL")
    parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST, help="Ollama base URL (D-08 unload)")
    parser.add_argument("--minio-host", default=DEFAULT_MINIO_HOST, help="MinIO host:port for upload")
    parser.add_argument("--require-live", action="store_true", help="M1-DV mode: no skip")
    parser.add_argument("--no-gpu-sequence", action="store_true", help="Skip D-08 Ollama unload step")
    args = parser.parse_args()

    comfy_host = normalize_host(args.host)
    ollama_host = normalize_host(args.ollama_host)
    minio_endpoint = f"http://{args.minio_host.strip()}"

    if not ENV_EXAMPLE.exists():
        fail(f"{ENV_EXAMPLE} not found")
    env = load_env_example()
    bucket = env["MINIO_BUCKET"]
    model = env.get("OLLAMA_MODEL", "qwen3:14b")

    print(
        f"Target: comfy={comfy_host}  minio={minio_endpoint}  "
        f"workflow={WORKFLOW_JSON.name}  require_live={args.require_live}\n"
    )

    print("[check] ComfyUI API reachable...")
    try:
        http_bytes(f"{comfy_host}/", timeout=8)
    except urllib.error.URLError as exc:
        skip(
            f"cannot reach ComfyUI at {comfy_host} ({exc.reason}). "
            "Start the dev stack with GPU services or use a GPU/Olares host.",
            require_live=args.require_live,
        )
    except TimeoutError:
        skip(f"timed out connecting to ComfyUI at {comfy_host}", require_live=args.require_live)
    print("  OK - ComfyUI responded\n")

    print("[check] MinIO S3 API reachable...")
    try:
        urllib.request.urlopen(f"{minio_endpoint}/minio/health/live", timeout=8)
    except urllib.error.URLError as exc:
        skip(
            f"cannot reach MinIO at {minio_endpoint} ({exc.reason}). Start minio in the dev stack.",
            require_live=args.require_live,
        )
    except TimeoutError:
        skip(f"timed out connecting to MinIO at {minio_endpoint}", require_live=args.require_live)
    print("  OK - MinIO health responded\n")

    workflow = load_workflow()

    if not args.no_gpu_sequence:
        print("[D-08] unload Ollama before ComfyUI (best effort)...")
        try_unload_ollama(ollama_host, model)
        print()

    print(f"[AC] queue workflow `{WORKFLOW_JSON.name}`...")
    try:
        prompt_id = queue_prompt(comfy_host, workflow)
    except urllib.error.URLError as exc:
        skip(f"could not queue prompt ({exc.reason})", require_live=args.require_live)
    print(f"  OK - prompt_id={prompt_id}")

    print(f"[AC] wait for PNG output (<{GENERATE_TIMEOUT_S}s)...")
    try:
        filename, subfolder, img_type = wait_for_image(comfy_host, prompt_id, GENERATE_TIMEOUT_S)
        query = urllib.parse.urlencode(
            {"filename": filename, "subfolder": subfolder, "type": img_type}
        )
        png = http_bytes(f"{comfy_host}/view?{query}", timeout=30)
    except urllib.error.URLError as exc:
        fail(f"workflow execution failed: {exc.reason}")

    if not is_png(png):
        fail(f"output is not a valid PNG ({len(png)} bytes)")
    print(f"  OK - PNG {len(png)} bytes from /view\n")

    minio_user = os.environ.get("MINIO_ROOT_USER") or env["MINIO_ROOT_USER"]
    minio_pass = os.environ.get("MINIO_ROOT_PASSWORD") or env["MINIO_ROOT_PASSWORD"]

    print(f"[AC] upload PNG to MinIO `/{bucket}/{MINIO_OBJECT}`...")
    upload_png_to_minio(
        png,
        endpoint=minio_endpoint,
        access_key=minio_user,
        secret_key=minio_pass,
        bucket=bucket,
        object_key=MINIO_OBJECT,
    )
    verify_minio_object(
        endpoint=minio_endpoint,
        access_key=minio_user,
        secret_key=minio_pass,
        bucket=bucket,
        object_key=MINIO_OBJECT,
    )
    print("  OK - object present in bucket\n")

    print("PASS - T-06-02 ComfyUI workflow and MinIO PNG upload verified (live).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
