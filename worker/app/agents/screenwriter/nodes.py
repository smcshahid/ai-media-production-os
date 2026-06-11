"""Screenwriter LangGraph nodes (US-14)."""

from __future__ import annotations

from aimpos_config import Settings

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
    return state


def draft_script_node(state: ScreenwriterState, settings: Settings) -> ScreenwriterState:
    if state.get("error"):
        return state

    prompt_cfg = load_script_prompt(settings, version=PROMPT_VERSION)
    user_prompt = prompt_cfg["user_template"].format(story_text=state["story_text"].strip())
    full_prompt = f"{prompt_cfg['system'].strip()}\n\n{user_prompt.strip()}"

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

    try:
        require_valid_fountain(script)
    except ValueError as exc:
        return {**state, "error": str(exc)}

    return {**state, "script_fountain": script, "error": None}
