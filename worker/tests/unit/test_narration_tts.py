"""TTS module import and provider smoke tests."""

from __future__ import annotations

from app.agents.narration.constants import SOURCE_ESPEAK, SOURCE_HTTP
from app.agents.narration.tts import NarrationTTSError, generate_narration_wav


def test_tts_constants_importable() -> None:
    assert SOURCE_ESPEAK == "espeak"
    assert SOURCE_HTTP == "http_tts"


def test_generate_narration_wav_rejects_empty_text() -> None:
    from aimpos_config import Settings

    settings = Settings()
    try:
        generate_narration_wav(settings, "   ")
        raised = False
    except NarrationTTSError:
        raised = True
    assert raised
