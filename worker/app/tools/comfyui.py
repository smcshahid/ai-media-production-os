"""ComfyUI HTTP client for storyboard frame generation (US-16)."""

from __future__ import annotations

import copy
import json
import logging
import time
from pathlib import Path

import httpx
from aimpos_config import Settings

from app.tools.config_paths import resolve_config_root
from app.tools.ollama import normalize_host

logger = logging.getLogger("aimpos.worker.comfyui")

PRODUCTION_WORKFLOW = "sdxl_storyboard_production.json"
PROMPT_NODE_ID = "2"
SEED_NODE_ID = "5"
GENERATE_TIMEOUT_S = 180


class ComfyUIError(Exception):
    """ComfyUI request or workflow execution failed."""


def load_production_workflow(settings: Settings) -> dict:
    path = resolve_config_root(settings) / "comfyui" / "workflows" / PRODUCTION_WORKFLOW
    if not path.is_file():
        raise ComfyUIError(f"workflow not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def patch_workflow_prompt(workflow: dict, *, positive_text: str, seed: int) -> dict:
    patched = copy.deepcopy(workflow)
    if PROMPT_NODE_ID not in patched or SEED_NODE_ID not in patched:
        raise ComfyUIError("production workflow missing prompt or seed nodes")
    patched[PROMPT_NODE_ID]["inputs"]["text"] = positive_text
    patched[SEED_NODE_ID]["inputs"]["seed"] = int(seed)
    return patched


def generate_storyboard_png(
    settings: Settings,
    *,
    positive_prompt: str,
    seed: int,
    timeout_s: float = GENERATE_TIMEOUT_S,
) -> bytes:
    """Queue production workflow and return PNG bytes for one frame."""
    host = normalize_host(settings.comfyui_host)
    workflow = patch_workflow_prompt(
        load_production_workflow(settings),
        positive_text=positive_prompt,
        seed=seed,
    )
    logger.info("comfyui_queued", extra={"seed": seed})
    prompt_id = _queue_prompt(host, workflow)
    filename, subfolder, image_type = _wait_for_image(host, prompt_id, timeout_s=timeout_s)
    png = _fetch_image_bytes(host, filename, subfolder, image_type)
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ComfyUIError("comfyui output is not a PNG")
    return png


def _queue_prompt(host: str, workflow: dict) -> str:
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{host}/prompt", json={"prompt": workflow})
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise ComfyUIError(f"comfyui /prompt failed: {exc}") from exc
    prompt_id = payload.get("prompt_id")
    if not prompt_id:
        raise ComfyUIError(f"comfyui /prompt missing prompt_id: {payload}")
    return str(prompt_id)


def _wait_for_image(
    host: str, prompt_id: str, *, timeout_s: float
) -> tuple[str, str, str]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(f"{host}/history/{prompt_id}")
                response.raise_for_status()
                history = response.json()
        except httpx.HTTPError as exc:
            raise ComfyUIError(f"comfyui /history failed: {exc}") from exc

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
    raise ComfyUIError(f"comfyui timed out after {timeout_s}s for prompt_id={prompt_id}")


def _fetch_image_bytes(host: str, filename: str, subfolder: str, image_type: str) -> bytes:
    params = f"filename={filename}&subfolder={subfolder}&type={image_type}"
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(f"{host}/view?{params}")
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as exc:
        raise ComfyUIError(f"comfyui /view failed: {exc}") from exc
