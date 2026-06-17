"""ComfyUI WAN 2.2 image-to-video enhancement path (US-18 phase 2).

Generates one short motion clip per storyboard frame on the (remote, 24GB)
ComfyUI host, then stitches the clips into a single widescreen MP4 with
crossfade transitions. Any failure raises :class:`VideoI2VError` so the caller
falls back to the FFmpeg slideshow — i2v is strictly additive.
"""

from __future__ import annotations

import copy
import json
import logging
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx
from aimpos_config import Settings

from app.tools.config_paths import resolve_config_root
from app.tools.ollama import normalize_host

logger = logging.getLogger("aimpos.worker.video_i2v")

DEFAULT_WORKFLOW = "wan22_i2v.json"
DEFAULT_TIMEOUT_S = 1200.0
CROSSFADE_S = 0.5
MP4_FTYP = b"ftyp"


class VideoI2VError(Exception):
    """ComfyUI i2v unavailable or failed — caller must fall back to slideshow."""


def try_comfyui_i2v(settings: Settings, png_frames: list[bytes]) -> bytes:
    """Attempt WAN 2.2 i2v across all frames; raise VideoI2VError on any failure."""
    if not getattr(settings, "video_i2v_enabled", False):
        raise VideoI2VError("comfyui i2v disabled (video_i2v_enabled=false)")
    if not png_frames:
        raise VideoI2VError("no storyboard frames supplied to i2v")

    host = normalize_host(settings.comfyui_host)
    workflow = _load_i2v_workflow(settings)
    fps = int(getattr(settings, "video_i2v_fps", 16) or 16)
    length = int(getattr(settings, "video_i2v_frames", 81) or 81)
    timeout_s = float(getattr(settings, "video_i2v_timeout_s", DEFAULT_TIMEOUT_S))
    clip_duration = length / float(fps)

    clips: list[bytes] = []
    for idx, png in enumerate(png_frames):
        seed = 42 + idx
        try:
            clip = _generate_clip(
                settings,
                host,
                workflow,
                png=png,
                index=idx,
                seed=seed,
                fps=fps,
                timeout_s=timeout_s,
            )
        except (httpx.HTTPError, OSError, ValueError, KeyError) as exc:
            raise VideoI2VError(f"i2v clip {idx + 1} failed: {exc}") from exc
        clips.append(clip)

    return _stitch_clips(clips, fps=fps, clip_duration=clip_duration)


def _load_i2v_workflow(settings: Settings) -> dict:
    name = getattr(settings, "video_i2v_workflow", None) or DEFAULT_WORKFLOW
    path = resolve_config_root(settings) / "comfyui" / "workflows" / name
    if not path.is_file():
        raise VideoI2VError(f"i2v workflow not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VideoI2VError(f"i2v workflow invalid JSON: {exc}") from exc


def _generate_clip(
    settings: Settings,
    host: str,
    workflow: dict,
    *,
    png: bytes,
    index: int,
    seed: int,
    fps: int,
    timeout_s: float,
) -> bytes:
    image_name = _upload_image(host, f"aimpos_i2v_{index:02d}_{uuid.uuid4().hex[:8]}.png", png)
    patched = _patch_i2v_workflow(
        workflow,
        image_name=image_name,
        seed=seed,
        width=int(getattr(settings, "video_i2v_width", 832) or 832),
        height=int(getattr(settings, "video_i2v_height", 480) or 480),
        length=int(getattr(settings, "video_i2v_frames", 81) or 81),
        steps=int(getattr(settings, "video_i2v_steps", 20) or 20),
        fps=fps,
    )
    prompt_id = _queue_prompt(host, patched)
    filename, subfolder, file_type = _wait_for_video(host, prompt_id, timeout_s=timeout_s)
    data = _fetch_bytes(host, filename, subfolder, file_type)
    if len(data) < 12 or data[4:8] != MP4_FTYP:
        raise VideoI2VError(f"i2v output for frame {index + 1} is not an mp4")
    return data


def _upload_image(host: str, name: str, png: bytes) -> str:
    files = {"image": (name, png, "image/png")}
    data = {"overwrite": "true"}
    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{host}/upload/image", files=files, data=data)
        response.raise_for_status()
        payload = response.json()
    uploaded = str(payload.get("name") or name)
    subfolder = str(payload.get("subfolder") or "")
    return f"{subfolder}/{uploaded}" if subfolder else uploaded


def _patch_i2v_workflow(
    workflow: dict,
    *,
    image_name: str,
    seed: int,
    width: int,
    height: int,
    length: int,
    steps: int,
    fps: int,
) -> dict:
    patched = copy.deepcopy(workflow)
    boundary = max(1, steps // 2)
    for node in patched.values():
        if not isinstance(node, dict):
            continue
        cls = node.get("class_type")
        inputs = node.get("inputs", {})
        if cls == "LoadImage":
            inputs["image"] = image_name
        elif cls == "WanImageToVideo":
            inputs["width"] = width
            inputs["height"] = height
            inputs["length"] = length
        elif cls == "KSamplerAdvanced":
            inputs["noise_seed"] = int(seed)
            inputs["steps"] = steps
            if inputs.get("add_noise") == "disable":
                inputs["start_at_step"] = boundary
            else:
                inputs["end_at_step"] = boundary
        elif cls == "CreateVideo":
            inputs["fps"] = fps
    return patched


def _queue_prompt(host: str, workflow: dict) -> str:
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{host}/prompt", json={"prompt": workflow})
        response.raise_for_status()
        payload = response.json()
    prompt_id = payload.get("prompt_id")
    if not prompt_id:
        raise VideoI2VError(f"comfyui /prompt missing prompt_id: {payload}")
    return str(prompt_id)


def _wait_for_video(host: str, prompt_id: str, *, timeout_s: float) -> tuple[str, str, str]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{host}/history/{prompt_id}")
            response.raise_for_status()
            history = response.json()
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status") or {}
            outputs = entry.get("outputs") or {}
            if status.get("completed") and not outputs:
                raise VideoI2VError(
                    "comfyui i2v finished with empty outputs "
                    f"(prompt_id={prompt_id}; likely stale execution cache — retry)"
                )
            if outputs:
                found = _extract_video_output(outputs)
                if found:
                    return found
        time.sleep(3)
    raise VideoI2VError(f"comfyui i2v timed out after {timeout_s}s (prompt_id={prompt_id})")


def _extract_video_output(outputs: dict) -> tuple[str, str, str] | None:
    """Find the produced video file across known ComfyUI output keys."""
    for node_out in outputs.values():
        if not isinstance(node_out, dict):
            continue
        for key in ("images", "gifs", "videos"):
            items = node_out.get(key) or []
            for item in items:
                filename = item.get("filename")
                if filename and str(filename).lower().endswith((".mp4", ".webm", ".mov")):
                    return (
                        str(filename),
                        str(item.get("subfolder", "")),
                        str(item.get("type", "output")),
                    )
    return None


def _fetch_bytes(host: str, filename: str, subfolder: str, file_type: str) -> bytes:
    params = {"filename": filename, "subfolder": subfolder, "type": file_type}
    with httpx.Client(timeout=120.0) as client:
        response = client.get(f"{host}/view", params=params)
        response.raise_for_status()
        return response.content


def _stitch_clips(clips: list[bytes], *, fps: int, clip_duration: float) -> bytes:
    """Concatenate per-frame clips with crossfades, re-encoding to H.264."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise VideoI2VError("ffmpeg not available for i2v stitching")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        paths: list[Path] = []
        for i, clip in enumerate(clips):
            path = tmp / f"clip_{i:02d}.mp4"
            path.write_bytes(clip)
            paths.append(path)

        out_path = tmp / "scene_video.mp4"
        cmd: list[str] = [ffmpeg, "-y"]
        for path in paths:
            cmd.extend(["-i", str(path)])

        if len(paths) == 1:
            cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(out_path),
                ]
            )
        else:
            filter_complex = _build_xfade_filter(
                len(paths), fps=fps, clip_duration=clip_duration
            )
            cmd.extend(
                [
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    "[outv]",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(out_path),
                ]
            )

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise VideoI2VError(proc.stderr.strip() or "ffmpeg i2v stitch failed")
        return out_path.read_bytes()


def _build_xfade_filter(count: int, *, fps: int, clip_duration: float) -> str:
    """Chained xfade across `count` equal-length clips.

    Each clip duration D = frames/fps; crossfade T shortens the timeline so the
    kth xfade offset is k*(D - T). Inputs are normalised to a constant fps and
    yuv420p so xfade accepts them.
    """
    duration = max(CROSSFADE_S * 2, clip_duration)
    transition = min(CROSSFADE_S, duration / 4.0)

    norm = "".join(
        f"[{i}:v]fps={fps},format=yuv420p,settb=AVTB[v{i}];" for i in range(count)
    )
    chain = ""
    prev = "v0"
    for k in range(1, count):
        offset = round(k * (duration - transition), 3)
        out_label = "outv" if k == count - 1 else f"x{k}"
        chain += (
            f"[{prev}][v{k}]xfade=transition=fade:"
            f"duration={transition}:offset={offset}[{out_label}];"
        )
        prev = out_label
    return (norm + chain).rstrip(";")
