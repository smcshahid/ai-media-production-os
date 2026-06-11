"""US-16 GPU sequencing (D-08)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.infrastructure.gpu.sequencer import unload_ollama_before_comfyui


def test_unload_ollama_before_comfyui_posts_keep_alive_zero() -> None:
    settings = MagicMock()
    settings.ollama_host = "http://ollama:11434"

    with patch("app.infrastructure.gpu.sequencer.load_storyboard_model", return_value="qwen3:14b"):
        with patch("httpx.Client") as client_cls:
            client = MagicMock()
            client_cls.return_value.__enter__.return_value = client
            client.post.return_value.raise_for_status.return_value = None
            model = unload_ollama_before_comfyui(settings)

    assert model == "qwen3:14b"
    client.post.assert_called_once()
    payload = client.post.call_args.kwargs["json"]
    assert payload["keep_alive"] == 0
