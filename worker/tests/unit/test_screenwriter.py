"""Unit tests for Screenwriter graph nodes (US-14)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from aimpos_config import Settings

from app.agents.screenwriter.nodes import (
    draft_script_node,
    finalize_script_node,
    load_story_context_node,
)
VALID_SCRIPT = """INT. LAB - DAY

A scientist works quietly.

DR. CHEN
The sample is ready.
"""


def test_load_story_context_requires_text() -> None:
    result = load_story_context_node({})
    assert result.get("error") == "story_text is empty"


def test_finalize_script_rejects_invalid_fountain() -> None:
    result = finalize_script_node({"script_fountain": "not fountain"})
    assert result.get("error")


def test_finalize_script_accepts_valid_fountain() -> None:
    result = finalize_script_node({"script_fountain": VALID_SCRIPT})
    assert result.get("error") is None
    assert "INT. LAB" in result["script_fountain"]


@patch("app.agents.screenwriter.nodes.generate_text")
@patch("app.agents.screenwriter.nodes.load_script_prompt")
@patch("app.agents.screenwriter.nodes.load_script_model")
def test_draft_script_node_success(
    mock_model: object,
    mock_prompt: object,
    mock_generate: object,
) -> None:
    mock_model.return_value = "qwen3:14b"
    mock_prompt.return_value = {
        "system": "system",
        "user_template": "story={story_text}",
        "temperature": 0.7,
        "num_predict": 1024,
    }
    mock_generate.return_value = (VALID_SCRIPT, 1.5)

    settings = Settings()
    result = draft_script_node({"story_text": "A hero finds a garden."}, settings)
    assert result.get("error") is None
    assert result.get("model_id") == "qwen3:14b"
    assert "INT. LAB" in result.get("script_fountain", "")
