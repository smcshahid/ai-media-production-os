"""LangGraph state for Story Architect (US-12)."""

from __future__ import annotations

from typing import TypedDict


class StoryArchitectState(TypedDict, total=False):
    idea_text: str
    style_note: str | None
    rejection_note: str | None
    character_bible: str | None
    story_md: str
    model_id: str
    prompt_version: str
    duration_ms: int
    error: str | None
