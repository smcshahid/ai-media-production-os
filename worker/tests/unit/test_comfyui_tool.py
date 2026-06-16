"""US-16 ComfyUI client (mocked HTTP)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tools.comfyui import generate_storyboard_png, patch_workflow_prompt

WORKFLOWS_DIR = Path(__file__).resolve().parents[3] / "configs" / "comfyui" / "workflows"


def test_patch_workflow_prompt_sets_text_and_seed() -> None:
    workflow = {
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "old", "clip": ["1", 1]}},
        "5": {"class_type": "KSampler", "inputs": {"seed": 1}},
    }
    patched = patch_workflow_prompt(workflow, positive_text="new prompt", seed=99)
    assert patched["2"]["inputs"]["text"] == "new prompt"
    assert patched["5"]["inputs"]["seed"] == 99


def test_patch_workflow_prompt_patches_resolution_and_sampler() -> None:
    workflow = {
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "old", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512}},
        "5": {
            "class_type": "KSampler",
            "inputs": {"seed": 1, "steps": 15, "cfg": 6.0, "sampler_name": "euler", "scheduler": "normal"},
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {"seed": 1, "steps": 99, "cfg": 6.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 0.4},
        },
    }
    patched = patch_workflow_prompt(
        workflow,
        positive_text="cinematic",
        seed=7,
        width=1344,
        height=768,
        steps=28,
        cfg=7.0,
        sampler="dpmpp_2m_sde",
        scheduler="karras",
        hires_steps=12,
    )
    assert patched["4"]["inputs"]["width"] == 1344
    assert patched["4"]["inputs"]["height"] == 768
    # base sampler gets the full step count
    assert patched["5"]["inputs"]["steps"] == 28
    assert patched["5"]["inputs"]["cfg"] == 7.0
    assert patched["5"]["inputs"]["sampler_name"] == "dpmpp_2m_sde"
    assert patched["5"]["inputs"]["scheduler"] == "karras"
    assert patched["5"]["inputs"]["seed"] == 7
    # hi-res sampler keeps its own (lower) step count but shares sampler params + seed
    assert patched["9"]["inputs"]["steps"] == 12
    assert patched["9"]["inputs"]["sampler_name"] == "dpmpp_2m_sde"
    assert patched["9"]["inputs"]["seed"] == 7


def test_patch_latent_handles_sd3_latent() -> None:
    # Flux / Z-Image use EmptySD3LatentImage; it must be resized like EmptyLatentImage.
    workflow = {
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}},
        "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 512, "height": 512}},
        "5": {"class_type": "KSampler", "inputs": {"seed": 1}},
    }
    patched = patch_workflow_prompt(
        workflow, positive_text="new", seed=2, width=1344, height=768
    )
    assert patched["4"]["inputs"]["width"] == 1344
    assert patched["4"]["inputs"]["height"] == 768


def test_unset_sampler_overrides_keep_engine_values() -> None:
    # When steps/cfg/sampler are None, the workflow's own (engine-correct) values stay.
    workflow = {
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}},
        "5": {
            "class_type": "KSampler",
            "inputs": {"seed": 1, "steps": 20, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple"},
        },
    }
    patched = patch_workflow_prompt(workflow, positive_text="x", seed=9)
    assert patched["5"]["inputs"]["seed"] == 9
    assert patched["5"]["inputs"]["steps"] == 20
    assert patched["5"]["inputs"]["cfg"] == 1.0
    assert patched["5"]["inputs"]["sampler_name"] == "euler"


@pytest.mark.parametrize(
    "filename,expect_steps,expect_cfg,latent_class",
    [
        ("flux_storyboard.json", 20, 1.0, "EmptySD3LatentImage"),
        ("zimage_storyboard.json", 8, 1.0, "EmptySD3LatentImage"),
        ("sdxl_realvis_storyboard.json", 28, 5.5, "EmptyLatentImage"),
        ("sdxl_storyboard_v2.json", 28, 7.0, "EmptyLatentImage"),
    ],
)
def test_shipped_engine_workflows_patch_cleanly(
    filename: str, expect_steps: int, expect_cfg: float, latent_class: str
) -> None:
    path = WORKFLOWS_DIR / filename
    if not path.is_file():
        pytest.skip(f"workflow bundle not on path: {path}")
    workflow = json.loads(path.read_text(encoding="utf-8"))
    patched = patch_workflow_prompt(
        workflow, positive_text="cinematic test", seed=123, width=1344, height=768
    )
    # Convention: "2" positive prompt, "5" primary KSampler, "4" latent.
    assert patched["2"]["inputs"]["text"] == "cinematic test"
    assert patched["5"]["inputs"]["seed"] == 123
    assert patched["4"]["class_type"] == latent_class
    assert patched["4"]["inputs"]["width"] == 1344
    assert patched["4"]["inputs"]["height"] == 768
    # Sampler overrides unset -> engine-correct values preserved.
    assert patched["5"]["inputs"]["steps"] == expect_steps
    assert patched["5"]["inputs"]["cfg"] == expect_cfg


def test_generate_storyboard_png_happy_path() -> None:
    settings = MagicMock()
    settings.comfyui_host = "http://comfyui:8188"
    settings.comfyui_workflow = "sdxl_storyboard_v2.json"
    settings.comfyui_width = 1344
    settings.comfyui_height = 768
    settings.comfyui_steps = 28
    settings.comfyui_cfg = 7.0
    settings.comfyui_sampler = "dpmpp_2m_sde"
    settings.comfyui_scheduler = "karras"
    settings.comfyui_hires_steps = 12
    settings.comfyui_generate_timeout_s = 180.0
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

    class FakeResponse:
        def __init__(self, payload, content: bytes | None = None):
            self._payload = payload
            self.content = content or b""

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return self._payload

    with patch("app.tools.comfyui.load_production_workflow", return_value={"2": {"inputs": {"text": ""}, "class_type": "x"}, "5": {"inputs": {"seed": 0}, "class_type": "y"}}):
        with patch("httpx.Client") as client_cls:
            client = MagicMock()
            client_cls.return_value.__enter__.return_value = client
            client.post.return_value = FakeResponse({"prompt_id": "pid-1"})
            client.get.side_effect = [
                FakeResponse(
                    {
                        "pid-1": {
                            "outputs": {
                                "7": {
                                    "images": [
                                        {"filename": "out.png", "subfolder": "", "type": "output"}
                                    ]
                                }
                            }
                        }
                    }
                ),
                FakeResponse({}, content=png),
            ]
            result = generate_storyboard_png(settings, positive_prompt="test", seed=42)
    assert result[:8] == b"\x89PNG\r\n\x1a\n"
