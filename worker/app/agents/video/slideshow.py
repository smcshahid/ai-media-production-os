"""Cinematic FFmpeg slideshow fallback for the VIDEO stage (US-18).

When ComfyUI i2v is disabled or fails, we still produce a watchable scene: each
storyboard still gets a slow Ken Burns push (zoompan) and frames are joined with
crossfades, rendered at 720p. This is the always-on quality floor.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.agents.cinematography.validate import validate_storyboard_frame
from app.agents.video.constants import (
    DEFAULT_DURATION_SEC,
    DEFAULT_FPS,
    MAX_HEIGHT,
    MAX_WIDTH,
    STORYBOARD_FRAME_COUNT,
)
from app.agents.video.validate import VideoProbeResult, validate_video_mp4

CROSSFADE_S = 1.0


class SlideshowRenderError(RuntimeError):
    """FFmpeg slideshow generation failed."""


def render_slideshow_mp4(
    png_frames: list[bytes],
    *,
    total_duration_sec: float = DEFAULT_DURATION_SEC,
) -> tuple[bytes, VideoProbeResult]:
    """Build a 720p H.264 MP4 with Ken Burns motion + crossfades from 4 frames."""
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

    count = len(png_frames)
    crossfade = min(CROSSFADE_S, total_duration_sec / (count * 2))
    # Size each segment so that after (count-1) overlapping crossfades the final
    # timeline lands on total_duration_sec.
    per_frame = (total_duration_sec + (count - 1) * crossfade) / count
    seg_frames = max(1, round(per_frame * DEFAULT_FPS))

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
            cmd.extend(["-i", str(path)])

        filter_complex = _build_kenburns_xfade_filter(
            count, seg_frames=seg_frames, crossfade=crossfade, per_frame=per_frame
        )
        cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[outv]",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(out_path),
            ]
        )

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SlideshowRenderError(proc.stderr.strip() or "ffmpeg failed")

        mp4_bytes = out_path.read_bytes()
        probe = validate_video_mp4(mp4_bytes)
        return mp4_bytes, probe


def _build_kenburns_xfade_filter(
    count: int, *, seg_frames: int, crossfade: float, per_frame: float
) -> str:
    """Ken Burns push per still + chained crossfades, output at 720p."""
    w, h = MAX_WIDTH, MAX_HEIGHT
    # Pre-upscale (2x) before zoompan to suppress the well-known pixel jitter.
    up_w, up_h = w * 2, h * 2

    norm = ""
    for i in range(count):
        # Alternate slow push-in / pull-out for visual variety.
        if i % 2 == 0:
            zoom = "min(zoom+0.0012,1.30)"
        else:
            zoom = "if(eq(on,0),1.30,max(zoom-0.0012,1.0))"
        norm += (
            f"[{i}:v]scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
            f"crop={up_w}:{up_h},"
            f"zoompan=z='{zoom}':d={seg_frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={w}x{h}:fps={DEFAULT_FPS},format=yuv420p,setsar=1[v{i}];"
        )

    if count == 1:
        return norm.rstrip(";").replace("[v0]", "[outv]")

    chain = ""
    prev = "v0"
    for k in range(1, count):
        offset = round(k * (per_frame - crossfade), 3)
        out_label = "outv" if k == count - 1 else f"x{k}"
        chain += (
            f"[{prev}][v{k}]xfade=transition=fade:"
            f"duration={crossfade}:offset={offset}[{out_label}];"
        )
        prev = out_label
    return (norm + chain).rstrip(";")
