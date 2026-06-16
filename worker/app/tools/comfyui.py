"""ComfyUI HTTP client for storyboard frame generation (US-16)."""

from __future__ import annotations

import copy
import json
import logging
import time

import httpx
from aimpos_config import Settings

from app.tools.config_paths import resolve_config_root
from app.tools.ollama import normalize_host

logger = logging.getLogger("aimpos.worker.comfyui")

# Default workflow used when settings.comfyui_workflow is unset.
PRODUCTION_WORKFLOW = "sdxl_storyboard_v2.json"
PROMPT_NODE_ID = "2"
SEED_NODE_ID = "5"
# Optional hi-res-fix second sampler; absent in the legacy single-pass workflow.
HIRES_SAMPLER_NODE_ID = "9"
DEFAULT_GENERATE_TIMEOUT_S = 180.0


class ComfyUIError(Exception):
    """ComfyUI request or workflow execution failed."""


def load_production_workflow(settings: Settings) -> dict:
    workflow_name = getattr(settings, "comfyui_workflow", None) or PRODUCTION_WORKFLOW
    path = resolve_config_root(settings) / "comfyui" / "workflows" / workflow_name
    if not path.is_file():
        raise ComfyUIError(f"workflow not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# Latent-source nodes whose width/height we patch. SDXL uses EmptyLatentImage;
# Flux and Z-Image (SD3-style 16ch latents) use EmptySD3LatentImage.
LATENT_NODE_CLASSES = {"EmptyLatentImage", "EmptySD3LatentImage"}


def _patch_latent_dims(node: dict, *, width: int | None, height: int | None) -> None:
    if node.get("class_type") not in LATENT_NODE_CLASSES:
        return
    if width:
        node["inputs"]["width"] = int(width)
    if height:
        node["inputs"]["height"] = int(height)


def _patch_sampler(
    node: dict,
    *,
    seed: int,
    steps: int | None,
    cfg: float | None,
    sampler: str | None,
    scheduler: str | None,
) -> None:
    if node.get("class_type") != "KSampler":
        return
    node["inputs"]["seed"] = int(seed)
    if steps:
        node["inputs"]["steps"] = int(steps)
    if cfg is not None:
        node["inputs"]["cfg"] = float(cfg)
    if sampler:
        node["inputs"]["sampler_name"] = sampler
    if scheduler:
        node["inputs"]["scheduler"] = scheduler


def patch_workflow_prompt(
    workflow: dict,
    *,
    positive_text: str,
    seed: int,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    sampler: str | None = None,
    scheduler: str | None = None,
    hires_steps: int | None = None,
) -> dict:
    """Patch prompt, seed, and (when provided) resolution + sampler params.

    Resolution is applied to every latent-source node (``EmptyLatentImage`` for
    SDXL, ``EmptySD3LatentImage`` for Flux/Z-Image) and sampler params to every
    ``KSampler`` node. All shipped engine workflows follow the convention
    ``"2"`` = positive prompt, ``"5"`` = primary KSampler, ``"4"`` = latent.

    Sampler params (``steps``/``cfg``/``sampler``/``scheduler``) are optional
    overrides: when ``None`` the workflow JSON's own (engine-correct) values are
    kept, so switching engines via ``COMFYUI_WORKFLOW`` requires no other config.
    The hi-res sampler keeps its own (lower) step count unless ``hires_steps``
    is provided.
    """
    patched = copy.deepcopy(workflow)
    if PROMPT_NODE_ID not in patched or SEED_NODE_ID not in patched:
        raise ComfyUIError("production workflow missing prompt or seed nodes")
    patched[PROMPT_NODE_ID]["inputs"]["text"] = positive_text

    for node_id, node in patched.items():
        if not isinstance(node, dict):
            continue
        _patch_latent_dims(node, width=width, height=height)
        if node.get("class_type") == "KSampler":
            node_steps = steps
            if node_id == HIRES_SAMPLER_NODE_ID:
                node_steps = hires_steps if hires_steps else None
            _patch_sampler(
                node,
                seed=seed,
                steps=node_steps,
                cfg=cfg,
                sampler=sampler,
                scheduler=scheduler,
            )
    return patched


def generate_storyboard_png(
    settings: Settings,
    *,
    positive_prompt: str,
    seed: int,
    timeout_s: float | None = None,
) -> bytes:
    """Queue production workflow and return PNG bytes for one frame."""
    host = normalize_host(settings.comfyui_host)
    workflow = patch_workflow_prompt(
        load_production_workflow(settings),
        positive_text=positive_prompt,
        seed=seed,
        width=getattr(settings, "comfyui_width", None),
        height=getattr(settings, "comfyui_height", None),
        steps=getattr(settings, "comfyui_steps", None),
        cfg=getattr(settings, "comfyui_cfg", None),
        sampler=getattr(settings, "comfyui_sampler", None),
        scheduler=getattr(settings, "comfyui_scheduler", None),
        hires_steps=getattr(settings, "comfyui_hires_steps", None),
    )
    effective_timeout = (
        timeout_s
        if timeout_s is not None
        else getattr(settings, "comfyui_generate_timeout_s", DEFAULT_GENERATE_TIMEOUT_S)
    )
    logger.info("comfyui_queued", extra={"seed": seed})
    prompt_id = _queue_prompt(host, workflow)
    filename, subfolder, image_type = _wait_for_image(
        host, prompt_id, timeout_s=effective_timeout
    )
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
