"""Screenwriter LangGraph state (US-14)."""

from __future__ import annotations

from typing import TypedDict


class ScreenwriterState(TypedDict, total=False):
    story_text: str
    rejection_note: str | None
    scene_count: int
    character_bible: str | None
    script_fountain: str
    model_id: str | None
    prompt_version: str | None
    duration_ms: int | None
    error: str | None
