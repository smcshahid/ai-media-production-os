"""Unit tests for narration mux (Phase 5)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from app.agents.narration.mux import mux_narration_into_mp4


def _minimal_mp4() -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not available")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "silent.mp4"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=640x360:d=2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        return out.read_bytes()


def _minimal_wav() -> bytes:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak is None:
        pytest.skip("espeak not available")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "narration.wav"
        subprocess.run(
            [espeak, "-w", str(out), "test narration"],
            check=True,
            capture_output=True,
        )
        return out.read_bytes()


def test_mux_narration_into_mp4() -> None:
    video = _minimal_mp4()
    audio = _minimal_wav()
    muxed = mux_narration_into_mp4(video_bytes=video, audio_wav_bytes=audio)
    assert muxed[:4] != b"ftyp"  # may start with null bytes before ftyp
    assert b"ftyp" in muxed[:32]
    assert len(muxed) > len(video)
