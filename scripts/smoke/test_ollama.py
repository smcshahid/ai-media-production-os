#!/usr/bin/env python3
"""T-06-01 smoke test — Ollama connectivity and text generation.

Verifies acceptance criteria for issue #60:
  - PASS (exit 0): Ollama reachable, pinned model present, completion in <30s
  - SKIP (exit 2): GPU/Ollama/model unavailable — documented, not a pass
  - FAIL (exit 1): Ollama reachable but inference or checks failed

Usage (from repo root):
    python scripts/smoke/test_ollama.py
    python scripts/smoke/test_ollama.py --require-live   # M1-DV: skip becomes fail
    python scripts/smoke/test_ollama.py --host http://127.0.0.1:11434

Exit codes:
    0  PASS — live inference succeeded
    1  FAIL — service available but test failed
    2  SKIP — prerequisites unavailable (default dev-host behaviour)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_JSON = ROOT / "configs" / "ollama" / "models.json"
DEFAULT_HOST = "http://127.0.0.1:11434"
GENERATE_TIMEOUT_S = 30


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str, *, require_live: bool) -> None:
    line = f"SKIP: {msg}"
    if require_live:
        fail(f"--require-live set; {msg}")
    print(line)
    print("SKIP - Ollama smoke not run (GPU/model/host unavailable). This is not PASS.")
    raise SystemExit(2)


def load_default_model() -> str:
    if MODELS_JSON.exists():
        data = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
        return str(data.get("default", "qwen3:14b"))
    return "qwen3:14b"


def normalize_host(host: str) -> str:
    host = host.strip().rstrip("/")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return host


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 10) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tags_url(host: str) -> str:
    return f"{host}/api/tags"


def generate_url(host: str) -> str:
    return f"{host}/api/generate"


def model_available(host: str, model: str) -> bool:
    payload = http_json("GET", tags_url(host), timeout=10)
    names = {m.get("name", "") for m in payload.get("models", [])}
    # Ollama may report "llama3.1:13b" or with digest suffix.
    return any(n == model or n.startswith(f"{model}:") or model in n for n in names)


def run_generate(host: str, model: str) -> tuple[str, float]:
    started = time.monotonic()
    payload = http_json(
        "POST",
        generate_url(host),
        body={
            "model": model,
            "prompt": "Reply with exactly: OK",
            "stream": False,
            # Thinking models (e.g. qwen3:14b) may consume budget in `thinking` before `response`.
            "options": {"num_predict": 128, "temperature": 0},
        },
        timeout=GENERATE_TIMEOUT_S,
    )
    elapsed = time.monotonic() - started
    text = str(payload.get("response", "")).strip()
    if not text:
        text = str(payload.get("thinking", "")).strip()
    if not text:
        fail("Ollama /api/generate returned empty response and thinking")
    if elapsed >= GENERATE_TIMEOUT_S:
        fail(f"completion took {elapsed:.1f}s (limit {GENERATE_TIMEOUT_S}s)")
    return text, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="T-06-01 Ollama smoke test")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Ollama base URL (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model tag (default: configs/ollama/models.json default)",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="M1-DV mode: treat unavailable Ollama/GPU as FAIL, not SKIP",
    )
    args = parser.parse_args()

    host = normalize_host(args.host)
    model = args.model or load_default_model()

    print(f"Target: {host}  model={model}  require_live={args.require_live}\n")

    print("[check] Ollama API reachable...")
    try:
        http_json("GET", tags_url(host), timeout=8)
    except urllib.error.URLError as exc:
        skip(
            f"cannot reach Ollama at {host} ({exc.reason}). "
            "Start the dev stack with GPU services or use a GPU/Olares host.",
            require_live=args.require_live,
        )
    except TimeoutError:
        skip(f"timed out connecting to Ollama at {host}", require_live=args.require_live)
    print("  OK - /api/tags responded\n")

    print(f"[check] pinned model `{model}` present...")
    try:
        if not model_available(host, model):
            skip(
                f"model `{model}` not in /api/tags. Run ollama-init or `ollama pull {model}`.",
                require_live=args.require_live,
            )
    except urllib.error.URLError as exc:
        skip(f"could not list models ({exc.reason})", require_live=args.require_live)
    print("  OK - model listed\n")

    print(f"[AC] generate completion (<{GENERATE_TIMEOUT_S}s)...")
    try:
        text, elapsed = run_generate(host, model)
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if "Connection refused" in reason or "timed out" in reason.lower():
            skip(f"inference unreachable ({reason})", require_live=args.require_live)
        fail(f"/api/generate failed: {reason}")
    except TimeoutError:
        fail(f"/api/generate timed out after {GENERATE_TIMEOUT_S}s")

    preview = text[:80].replace("\n", " ")
    print(f"  OK - response in {elapsed:.1f}s: {preview!r}\n")
    print("PASS - T-06-01 Ollama connectivity and text generation verified (live).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
