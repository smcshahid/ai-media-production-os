"""FFmpeg audio/video mux for narrated exports (Phase 5 / D-81)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class NarrationMuxError(Exception):
    """Audio/video mux failed."""


def mux_narration_into_mp4(*, video_bytes: bytes, audio_wav_bytes: bytes) -> bytes:
    """Mux narration WAV into MP4; video stream copied, AAC audio added."""
    if not video_bytes:
        raise NarrationMuxError("video bytes empty")
    if not audio_wav_bytes:
        raise NarrationMuxError("audio bytes empty")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        video_path = tmp_path / "input.mp4"
        audio_path = tmp_path / "narration.wav"
        output_path = tmp_path / "output.mp4"
        video_path.write_bytes(video_bytes)
        audio_path.write_bytes(audio_wav_bytes)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode("utf-8", errors="replace")[:500]
            raise NarrationMuxError(f"ffmpeg mux failed: {stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise NarrationMuxError("ffmpeg mux timed out") from exc

        if not output_path.is_file():
            raise NarrationMuxError("ffmpeg produced no output")
        return output_path.read_bytes()
