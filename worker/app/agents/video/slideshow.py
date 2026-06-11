"""FFmpeg slideshow baseline for US-18 phase 1."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.agents.cinematography.validate import validate_storyboard_frame
from app.agents.video.constants import (
    DEFAULT_DURATION_SEC,
    DEFAULT_FPS,
    STORYBOARD_FRAME_COUNT,
)
from app.agents.video.validate import VideoProbeResult, validate_video_mp4


class SlideshowRenderError(RuntimeError):
    """FFmpeg slideshow generation failed."""


def render_slideshow_mp4(
    png_frames: list[bytes],
    *,
    total_duration_sec: float = DEFAULT_DURATION_SEC,
) -> tuple[bytes, VideoProbeResult]:
    """Build H.264 MP4 from exactly 4 PNG frames (D-48 baseline)."""
    if len(png_frames) != STORYBOARD_FRAME_COUNT:
        raise SlideshowRenderError(
            f"expected {STORYBOARD_FRAME_COUNT} frames, got {len(png_frames)}"
        )

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SlideshowRenderError("ffmpeg not available")

    for idx, png in enumerate(png_frames):
        try:
            validate_storyboard_frame(png)
        except ValueError as exc:
            raise SlideshowRenderError(f"frame {idx + 1} invalid: {exc}") from exc

    per_frame = total_duration_sec / STORYBOARD_FRAME_COUNT

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        inputs: list[Path] = []
        for i, png in enumerate(png_frames, start=1):
            path = tmp / f"frame_{i:02d}.png"
            path.write_bytes(png)
            inputs.append(path)

        out_path = tmp / "scene_video.mp4"
        cmd: list[str] = [ffmpeg, "-y"]
        for path in inputs:
            cmd.extend(["-loop", "1", "-framerate", str(DEFAULT_FPS), "-t", str(per_frame), "-i", str(path)])

        concat_inputs = "".join(f"[{i}:v]" for i in range(len(inputs)))
        filter_complex = (
            f"{concat_inputs}concat=n={len(inputs)}:v=1:a=0,"
            "scale=854:480:force_original_aspect_ratio=decrease:flags=lanczos,"
            "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        )
        cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-t",
                str(total_duration_sec),
                str(out_path),
            ]
        )

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SlideshowRenderError(proc.stderr.strip() or "ffmpeg failed")

        mp4_bytes = out_path.read_bytes()
        probe = validate_video_mp4(mp4_bytes)
        return mp4_bytes, probe
