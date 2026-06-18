"""Local sovereign TTS providers (Phase 5 / D-80)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx
from aimpos_config import Settings

from app.agents.narration.constants import SOURCE_ESPEAK, SOURCE_HTTP


class NarrationTTSError(Exception):
    """TTS generation failed."""


def generate_narration_wav(settings: Settings, text: str) -> tuple[bytes, str]:
    """Return WAV bytes and provider source label."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise NarrationTTSError("narration text is empty")

    provider = (settings.narration_tts_provider or "espeak").strip().lower()
    if provider == "http":
        return _generate_http_tts(settings, cleaned), SOURCE_HTTP
    return _generate_espeak_wav(settings, cleaned), SOURCE_ESPEAK


def _generate_espeak_wav(settings: Settings, text: str) -> bytes:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak is None:
        raise NarrationTTSError("espeak-ng not installed in worker image")

    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "narration.wav"
        cmd = [
            espeak,
            "-w",
            str(out_path),
            "-s",
            str(settings.narration_espeak_rate),
            "-v",
            settings.narration_tts_voice,
            text,
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=float(settings.narration_tts_timeout_s),
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode("utf-8", errors="replace")[:500]
            raise NarrationTTSError(f"espeak failed: {stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise NarrationTTSError("espeak timed out") from exc

        if not out_path.is_file():
            raise NarrationTTSError("espeak produced no output file")
        return out_path.read_bytes()


def _generate_http_tts(settings: Settings, text: str) -> bytes:
    """Call Olares-hosted HTTP TTS (e.g. speaches OpenAI-compatible API)."""
    base = settings.narration_tts_host.rstrip("/")
    url = f"{base}/v1/audio/speech"
    payload = {
        "model": "tts-1",
        "input": text,
        "voice": settings.narration_tts_voice,
        "response_format": "wav",
    }
    try:
        with httpx.Client(timeout=settings.narration_tts_timeout_s) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.content
    except Exception as exc:
        raise NarrationTTSError(f"http tts failed: {exc}") from exc

    if not data:
        raise NarrationTTSError("http tts returned empty body")
    return data
