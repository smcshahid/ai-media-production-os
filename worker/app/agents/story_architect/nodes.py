"""Story Architect LangGraph nodes."""

from __future__ import annotations

from aimpos_config import Settings

from app.agents.story_architect.constants import MIN_STORY_CHARS, PROMPT_VERSION
from app.agents.story_architect.state import StoryArchitectState
from app.tools.config_paths import load_story_model, load_story_prompt
from app.tools.ollama import OllamaError, generate_text


def load_idea_node(state: StoryArchitectState) -> StoryArchitectState:
    """Validate idea payload present (loaded by activity before graph invoke)."""
    idea = (state.get("idea_text") or "").strip()
    if not idea:
        return {**state, "error": "idea_text is empty"}
    return state


def draft_story_node(state: StoryArchitectState, settings: Settings) -> StoryArchitectState:
    if state.get("error"):
        return state

    prompt_cfg = load_story_prompt(settings, version=PROMPT_VERSION)
    style_note = state.get("style_note")
    style_block = ""
    if style_note:
        style_block = f"\nStyle note: {style_note}\n"

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

    user_prompt = prompt_cfg["user_template"].format(
        idea_text=state["idea_text"].strip(),
        style_note_block=style_block,
    )
    full_prompt = (
        f"{prompt_cfg['system'].strip()}\n\n{user_prompt.strip()}"
        f"{character_block}{revision_block}"
    )

    model_id = load_story_model(settings)
    try:
        story_md, duration_s = generate_text(
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
        "story_md": story_md,
        "model_id": model_id,
        "prompt_version": PROMPT_VERSION,
        "duration_ms": int(duration_s * 1000),
    }


def finalize_node(state: StoryArchitectState) -> StoryArchitectState:
    if state.get("error"):
        return state

    story_md = (state.get("story_md") or "").strip()
    if len(story_md) < MIN_STORY_CHARS:
        return {**state, "error": f"story output too short ({len(story_md)} chars)"}
    if not story_md.lstrip().startswith("#"):
        story_md = f"# Story Treatment\n\n{story_md}"
    return {**state, "story_md": story_md, "error": None}
