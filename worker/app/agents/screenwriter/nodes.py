"""Screenwriter LangGraph nodes (US-14 / Phase 4 multi-scene)."""

from __future__ import annotations

from aimpos_config import Settings
from aimpos_core.scene import MAX_SCENES, MIN_SCENES

from app.agents.screenwriter.constants import MIN_SCRIPT_CHARS, PROMPT_VERSION
from app.agents.screenwriter.state import ScreenwriterState
from app.agents.screenwriter.validate import require_valid_fountain
from app.tools.config_paths import load_script_model, load_script_prompt
from app.tools.ollama import OllamaError, generate_text


def load_story_context_node(state: ScreenwriterState) -> ScreenwriterState:
    """Validate story payload present (loaded by activity before graph invoke)."""
    story = (state.get("story_text") or "").strip()
    if not story:
        return {**state, "error": "story_text is empty"}
    scene_count = int(state.get("scene_count") or 1)
    if scene_count < MIN_SCENES or scene_count > MAX_SCENES:
        return {**state, "error": f"scene_count out of range {MIN_SCENES}-{MAX_SCENES}"}
    return {**state, "scene_count": scene_count}


def draft_script_node(state: ScreenwriterState, settings: Settings) -> ScreenwriterState:
    if state.get("error"):
        return state

    prompt_cfg = load_script_prompt(settings, version=PROMPT_VERSION)
    scene_count = int(state.get("scene_count") or 1)
    scene_word = "ONE SCENE" if scene_count == 1 else f"EXACTLY {scene_count} SCENES"
    scene_rules = (
        "- Exactly one scene heading line starting with INT. or EXT. (e.g. INT. LOCATION - TIME)\n"
        "- Do NOT write a second scene heading"
        if scene_count == 1
        else (
            f"- Exactly {scene_count} scene heading lines (INT. or EXT. …)\n"
            "- Each scene must have action and at least one character cue with dialogue\n"
            "- Separate scenes with blank lines; do not merge scenes"
        )
    )

    user_prompt = prompt_cfg["user_template"].format(
        story_text=state["story_text"].strip(),
        scene_word=scene_word,
        scene_rules=scene_rules,
    )

    rejection_note = (state.get("rejection_note") or "").strip()
    revision_block = ""
    if rejection_note:
        revision_block = (
            "\nRevision notes from reviewer (address these in the new draft):\n"
            f"{rejection_note}\n"
        )

    character_block = ""
    character_bible = (state.get("character_bible") or "").strip()
    if character_bible:
        character_block = f"\n{character_bible}\n"

    full_prompt = f"{prompt_cfg['system'].strip()}\n\n{user_prompt.strip()}{character_block}{revision_block}"

    model_id = load_script_model(settings)
    try:
        script_fountain, duration_s = generate_text(
            settings,
            model=model_id,
            prompt=full_prompt,
            temperature=float(prompt_cfg.get("temperature", 0.7)),
            num_predict=int(prompt_cfg.get("num_predict", 2048)),
        )
    except OllamaError as exc:
        return {**state, "error": str(exc), "model_id": model_id}

    return {
        **state,
        "script_fountain": script_fountain,
        "model_id": model_id,
        "prompt_version": PROMPT_VERSION,
        "duration_ms": int(duration_s * 1000),
    }


def finalize_script_node(state: ScreenwriterState) -> ScreenwriterState:
    if state.get("error"):
        return state

    script = (state.get("script_fountain") or "").strip()
    if len(script) < MIN_SCRIPT_CHARS:
        return {**state, "error": f"script output too short ({len(script)} chars)"}

    scene_count = int(state.get("scene_count") or 1)
    try:
        require_valid_fountain(script, expected_scene_count=scene_count)
    except ValueError as exc:
        return {**state, "error": str(exc)}

    return {**state, "script_fountain": script, "error": None}
