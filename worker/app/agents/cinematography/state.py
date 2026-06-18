"""Cinematography LangGraph state (US-16)."""

from __future__ import annotations

from typing import TypedDict


class ShotPlan(TypedDict):
    frame_index: int
    shot_label: str
    prompt: str


class CinematographyState(TypedDict, total=False):
    script_fountain: str
    style_note: str | None
    shots: list[ShotPlan]
    model_id: str
    prompt_version: str
    duration_ms: int
    rejection_note: str | None
    character_bible: str | None
    error: str | None
