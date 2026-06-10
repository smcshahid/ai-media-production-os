"""Unit tests for Story Architect graph nodes (US-12)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from aimpos_config import Settings

from app.agents.story_architect.nodes import draft_story_node, finalize_node, load_idea_node


def test_load_idea_node_requires_text() -> None:
    result = load_idea_node({})
    assert result.get("error") == "idea_text is empty"


def test_finalize_node_adds_title_when_missing() -> None:
    result = finalize_node({"story_md": "A" * 100})
    assert result["story_md"].startswith("# Story Treatment")
    assert result.get("error") is None


def test_finalize_node_rejects_short_output() -> None:
    result = finalize_node({"story_md": "short"})
    assert "too short" in (result.get("error") or "")


@patch("app.agents.story_architect.nodes.generate_text")
@patch("app.agents.story_architect.nodes.load_story_prompt")
@patch("app.agents.story_architect.nodes.load_story_model")
def test_draft_story_node_success(
    mock_model: object,
    mock_prompt: object,
    mock_generate: object,
) -> None:
    mock_model.return_value = "qwen3:14b"
    mock_prompt.return_value = {
        "system": "system",
        "user_template": "idea={idea_text}{style_note_block}",
        "temperature": 0.5,
        "num_predict": 512,
    }
    mock_generate.return_value = ("# Title\n\nLogline.\n\nAct I.", 1.2)

    settings = Settings(ollama_host="http://127.0.0.1:11434", config_root="configs")
    result = draft_story_node(
        {"idea_text": "A creator wants a heist film.", "style_note": None},
        settings,
    )
    assert result["model_id"] == "qwen3:14b"
    assert "Title" in result["story_md"]
    assert result.get("error") is None
