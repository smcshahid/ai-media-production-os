"""US-16 ComfyUI client (mocked HTTP)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from app.tools.comfyui import generate_storyboard_png, patch_workflow_prompt


def test_patch_workflow_prompt_sets_text_and_seed() -> None:
    workflow = {
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "old", "clip": ["1", 1]}},
        "5": {"class_type": "KSampler", "inputs": {"seed": 1}},
    }
    patched = patch_workflow_prompt(workflow, positive_text="new prompt", seed=99)
    assert patched["2"]["inputs"]["text"] == "new prompt"
    assert patched["5"]["inputs"]["seed"] == 99


def test_generate_storyboard_png_happy_path() -> None:
    settings = MagicMock()
    settings.comfyui_host = "http://comfyui:8188"
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
