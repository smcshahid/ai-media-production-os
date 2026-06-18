"""Cinematography LangGraph nodes (US-16)."""

from __future__ import annotations

import json
import re

from aimpos_config import Settings

from app.agents.cinematography.constants import PROMPT_VERSION
from app.agents.cinematography.state import CinematographyState, ShotPlan
from app.agents.cinematography.validate import validate_shot_plan
from app.tools.config_paths import load_storyboard_model, load_storyboard_prompt
from app.tools.ollama import OllamaError, generate_text


def load_script_context_node(state: CinematographyState) -> CinematographyState:
    script = (state.get("script_fountain") or "").strip()
    if not script:
        return {**state, "error": "script_fountain is empty"}
    return state


def plan_shots_node(state: CinematographyState, settings: Settings) -> CinematographyState:
    if state.get("error"):
        return state

    prompt_cfg = load_storyboard_prompt(settings, version=PROMPT_VERSION)
    style_note = state.get("style_note")
    style_block = ""
    if style_note:
        style_block = f"Style note: {style_note}\n"

    excerpt = (state.get("script_fountain") or "").strip()
    if len(excerpt) > 6000:
        excerpt = excerpt[:6000] + "\n..."

    rejection_note = (state.get("rejection_note") or "").strip()
    revision_block = ""
    if rejection_note:
        revision_block = (
            "\nRevision notes from reviewer (address these in the new 4-shot storyboard; "
            "do not reference prior frame images):\n"
            f"{rejection_note}\n"
        )

    character_block = ""
    character_bible = (state.get("character_bible") or "").strip()
    if character_bible:
        character_block = f"\n{character_bible}\n"

    user_prompt = prompt_cfg["user_template"].format(
        script_excerpt=excerpt,
        style_note_block=style_block,
    )
    full_prompt = (
        f"{prompt_cfg['system'].strip()}\n\n{user_prompt.strip()}"
        f"{character_block}{revision_block}"
    )

    model_id = load_storyboard_model(settings)
    try:
        raw, duration_s = generate_text(
            settings,
            model=model_id,
            prompt=full_prompt,
            temperature=float(prompt_cfg.get("temperature", 0.6)),
            num_predict=int(prompt_cfg.get("num_predict", 2048)),
        )
    except OllamaError as exc:
        return {**state, "error": str(exc), "model_id": model_id}

    try:
        shots = _parse_shot_plan_json(raw)
        validate_shot_plan(shots)
    except (ValueError, json.JSONDecodeError) as exc:
        return {**state, "error": f"invalid shot plan: {exc}", "model_id": model_id}

    return {
        **state,
        "shots": shots,
        "model_id": model_id,
        "prompt_version": PROMPT_VERSION,
        "duration_ms": int(duration_s * 1000),
        "error": None,
    }


def _parse_shot_plan_json(raw: str) -> list[ShotPlan]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    payload = json.loads(text)
    raw_shots = payload.get("shots") if isinstance(payload, dict) else None
    if not isinstance(raw_shots, list):
        raise ValueError("JSON must contain shots array")

    shots: list[ShotPlan] = []
    for item in raw_shots:
        if not isinstance(item, dict):
            raise ValueError("each shot must be an object")
        shots.append(
            {
                "frame_index": int(item["frame_index"]),
                "shot_label": str(item.get("shot_label") or "").strip() or "Shot",
                "prompt": str(item.get("prompt") or "").strip(),
            }
        )
    return shots
