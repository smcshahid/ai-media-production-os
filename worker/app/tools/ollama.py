"""Ollama HTTP client for worker activities (US-12)."""

from __future__ import annotations

import httpx
from aimpos_config import Settings


class OllamaError(Exception):
    """Ollama request failed."""


class OllamaModelMissingError(OllamaError):
    """Requested model is not available locally."""


def normalize_host(host: str) -> str:
    host = host.strip().rstrip("/")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return host


def generate_text(
    settings: Settings,
    *,
    model: str,
    prompt: str,
    temperature: float = 0.7,
    num_predict: int = 2048,
    timeout_s: float = 600.0,
) -> tuple[str, float]:
    """Call ``POST /api/generate`` and return ``(text, duration_seconds)``."""
    import time

    base = normalize_host(settings.ollama_host)
    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(
                f"{base}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": num_predict},
                },
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise OllamaModelMissingError(f"model not found: {model}") from exc
        raise OllamaError(f"ollama generate failed: {exc}") from exc
    except httpx.HTTPError as exc:
        raise OllamaError(f"ollama unreachable at {base}: {exc}") from exc

    text = str(payload.get("response", "")).strip()
    if not text:
        text = str(payload.get("thinking", "")).strip()
    if not text:
        raise OllamaError("ollama returned empty response and thinking")
    return text, time.monotonic() - t0
