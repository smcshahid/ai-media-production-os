"""Orchestrate scene narration: TTS → store → mux (Phase 5)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from aimpos_config import Settings
from aimpos_core.narration import narration_text_for_scene

from app.agents.narration.constants import SOURCE_NONE
from app.agents.narration.mux import mux_narration_into_mp4
from app.agents.narration.tts import generate_narration_wav
from app.tools.assets import (
    fetch_approved_script,
    store_narration_asset,
)


@dataclass(frozen=True, slots=True)
class NarrationResult:
    mp4_bytes: bytes
    narration_applied: bool
    narration_source: str
    narration_text: str
    narration_duration_sec: float | None
    narration_asset_id: str | None


def apply_scene_narration(
    settings: Settings,
    *,
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID,
    scene_index: int,
    scene_count: int,
    silent_mp4_bytes: bytes,
) -> NarrationResult:
    """Generate narration when enabled; fall back to silent video on any failure."""
    if not getattr(settings, "narration_enabled", True):
        return NarrationResult(
            mp4_bytes=silent_mp4_bytes,
            narration_applied=False,
            narration_source=SOURCE_NONE,
            narration_text="",
            narration_duration_sec=None,
            narration_asset_id=None,
        )

    try:
        script = fetch_approved_script(
            settings, project_id=project_id, pipeline_run_id=pipeline_run_id
        )
        narration_text = narration_text_for_scene(script.script_fountain, scene_index)
        if not narration_text.strip():
            return NarrationResult(
                mp4_bytes=silent_mp4_bytes,
                narration_applied=False,
                narration_source=SOURCE_NONE,
                narration_text="",
                narration_duration_sec=None,
                narration_asset_id=None,
            )

        wav_bytes, tts_source = generate_narration_wav(settings, narration_text)
        stored = store_narration_asset(
            settings,
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            wav_bytes=wav_bytes,
            metadata={
                "tts_source": tts_source,
                "narration_text_length": len(narration_text),
                "logical_filename": f"scene_{scene_index:02d}_narration.wav",
            },
            scene_index=scene_index,
            scene_count=scene_count,
            script_parent_id=script.asset_version_id,
        )
        muxed = mux_narration_into_mp4(
            video_bytes=silent_mp4_bytes, audio_wav_bytes=wav_bytes
        )

        return NarrationResult(
            mp4_bytes=muxed,
            narration_applied=True,
            narration_source=tts_source,
            narration_text=narration_text[:500],
            narration_duration_sec=stored.duration_sec,
            narration_asset_id=str(stored.asset_version_id),
        )
    except Exception:
        return NarrationResult(
            mp4_bytes=silent_mp4_bytes,
            narration_applied=False,
            narration_source=SOURCE_NONE,
            narration_text="",
            narration_duration_sec=None,
            narration_asset_id=None,
        )
