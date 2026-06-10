"""US-11 idea domain service tests."""

from __future__ import annotations

import pytest

from app.domain.ideas.service import (
    IdeaValidationError,
    build_idea_text,
    build_metadata_json,
    validate_idea_fields,
)

_PARAGRAPH = "A" * 50


def test_build_idea_text_format() -> None:
    assert build_idea_text("Mars Garden", _PARAGRAPH) == b"Mars Garden\n\n" + _PARAGRAPH.encode()


def test_build_metadata_json_omits_empty_style_note() -> None:
    assert build_metadata_json(None) is None
    assert build_metadata_json("   ") is None


def test_build_metadata_json_includes_trimmed_style_note() -> None:
    assert build_metadata_json("  noir  ") == {"style_note": "noir"}


def test_validate_rejects_short_paragraph() -> None:
    with pytest.raises(IdeaValidationError, match="at least 50"):
        validate_idea_fields(title="Title", paragraph="short", style_note=None)


def test_validate_rejects_multiline_title() -> None:
    with pytest.raises(IdeaValidationError, match="single line"):
        validate_idea_fields(title="Line one\nLine two", paragraph=_PARAGRAPH, style_note=None)
