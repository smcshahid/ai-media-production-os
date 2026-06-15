"""MP4 validation for US-18 (D-48)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.agents.video.constants import (
    MAX_DURATION_SEC,
    MAX_HEIGHT,
    MAX_WIDTH,
    MIN_DURATION_SEC,
)


class VideoValidationError(ValueError):
    """MP4 bytes failed D-48 validation."""


@dataclass(frozen=True, slots=True)
class VideoProbeResult:
    duration_sec: float
    width: int
    height: int
    codec: str = "h264"


def _probe_file(path: Path) -> VideoProbeResult:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise VideoValidationError("ffprobe not available")

    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,duration,codec_name",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise VideoValidationError(f"ffprobe failed: {proc.stderr.strip()}")

    payload = json.loads(proc.stdout)
    streams = payload.get("streams") or []
    if not streams:
        raise VideoValidationError("no video stream in mp4")

    stream = streams[0]
    duration = float(stream.get("duration") or 0.0)
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    codec = str(stream.get("codec_name") or "h264")

    return VideoProbeResult(
        duration_sec=duration,
        width=width,
        height=height,
        codec=codec,
    )


def validate_video_mp4(mp4_bytes: bytes) -> VideoProbeResult:
    """Validate MP4 magic, duration band, and resolution caps (D-48)."""
    if len(mp4_bytes) < 12 or mp4_bytes[4:8] != b"ftyp":
        raise VideoValidationError("invalid mp4: missing ftyp box")

    # delete=False + manual cleanup so the file can be reopened by ffprobe on
    # Windows (where an open NamedTemporaryFile cannot be reopened).
    fd, tmp_name = tempfile.mkstemp(suffix=".mp4")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(mp4_bytes)
        probe = _probe_file(Path(tmp_name))
    finally:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass

    if not (MIN_DURATION_SEC <= probe.duration_sec <= MAX_DURATION_SEC):
        raise VideoValidationError(
            f"duration {probe.duration_sec}s outside [{MIN_DURATION_SEC}, {MAX_DURATION_SEC}]"
        )
    if probe.width <= 0 or probe.height <= 0:
        raise VideoValidationError("invalid video dimensions")
    if probe.width > MAX_WIDTH or probe.height > MAX_HEIGHT:
        raise VideoValidationError(
            f"resolution {probe.width}x{probe.height} exceeds 480p band"
        )
    return probe
