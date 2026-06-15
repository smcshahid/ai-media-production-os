"""WAN 2.2 i2v tool tests (no live ComfyUI)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.tools.video_i2v import (
    VideoI2VError,
    _build_xfade_filter,
    _patch_i2v_workflow,
    try_comfyui_i2v,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_try_comfyui_i2v_disabled_raises() -> None:
    settings = MagicMock()
    settings.video_i2v_enabled = False
    with pytest.raises(VideoI2VError, match="disabled"):
        try_comfyui_i2v(settings, [PNG])


def test_try_comfyui_i2v_no_frames_raises() -> None:
    settings = MagicMock()
    settings.video_i2v_enabled = True
    with pytest.raises(VideoI2VError, match="no storyboard frames"):
        try_comfyui_i2v(settings, [])


def test_production_workflow_is_valid_and_patchable() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    workflow_path = repo_root / "configs" / "comfyui" / "workflows" / "wan22_i2v.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))

    patched = _patch_i2v_workflow(
        workflow,
        image_name="frame.png",
        seed=5,
        width=832,
        height=480,
        length=81,
        steps=20,
        fps=16,
    )

    load_nodes = [n for n in patched.values() if n.get("class_type") == "LoadImage"]
    assert load_nodes and load_nodes[0]["inputs"]["image"] == "frame.png"

    i2v_nodes = [n for n in patched.values() if n.get("class_type") == "WanImageToVideo"]
    assert i2v_nodes
    assert i2v_nodes[0]["inputs"]["width"] == 832
    assert i2v_nodes[0]["inputs"]["length"] == 81

    samplers = [n for n in patched.values() if n.get("class_type") == "KSamplerAdvanced"]
    assert len(samplers) == 2
    for node in samplers:
        assert node["inputs"]["noise_seed"] == 5
        assert node["inputs"]["steps"] == 20
    # high/low noise split at the midpoint
    high = next(n for n in samplers if n["inputs"]["add_noise"] == "enable")
    low = next(n for n in samplers if n["inputs"]["add_noise"] == "disable")
    assert high["inputs"]["end_at_step"] == 10
    assert low["inputs"]["start_at_step"] == 10


def test_build_xfade_filter_offsets_increase() -> None:
    filt = _build_xfade_filter(4, fps=16, clip_duration=5.0)
    assert filt.count("xfade") == 3
    assert "[outv]" in filt
    # normalised inputs for all four clips
    for i in range(4):
        assert f"[{i}:v]fps=16" in filt
