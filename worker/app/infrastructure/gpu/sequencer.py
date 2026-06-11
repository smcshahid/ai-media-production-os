"""GPU workload sequencing (D-08 / US-16 T-16-04)."""

from __future__ import annotations

import logging

import httpx
from aimpos_config import Settings

from app.tools.config_paths import load_storyboard_model
from app.tools.ollama import normalize_host

logger = logging.getLogger("aimpos.worker.gpu")


class GpuSequencerError(Exception):
    """GPU handoff step failed."""


def unload_ollama_before_comfyui(settings: Settings) -> str:
    """Evict the pinned storyboard Ollama model before ComfyUI inference."""
    model = load_storyboard_model(settings)
    base = normalize_host(settings.ollama_host)
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{base}/api/generate",
                json={"model": model, "prompt": "", "keep_alive": 0},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GpuSequencerError(f"ollama unload failed for {model}: {exc}") from exc

    logger.info("ollama_unloaded", extra={"model": model})
    return model
