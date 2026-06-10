"""Idea capture service — builds ``idea.txt`` and stores via ``store_asset`` (US-11)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import AssetStage

from app.domain.assets.service import AssetVersionStore, BlobStore, StoredAsset, store_asset

_TITLE_MAX = 200
_PARAGRAPH_MIN = 50
_PARAGRAPH_MAX = 2000
_STYLE_NOTE_MAX = 500


class IdeaValidationError(ValueError):
    """Raised when idea fields fail US-11 validation rules."""


def build_idea_text(title: str, paragraph: str) -> bytes:
    """Canonical ``idea.txt`` layout: title, blank line, paragraph (UTF-8)."""
    return f"{title}\n\n{paragraph}".encode()


def validate_idea_fields(*, title: str, paragraph: str, style_note: str | None) -> None:
    """Validate trimmed idea fields; raises ``IdeaValidationError`` on failure."""
    trimmed_title = title.strip()
    trimmed_paragraph = paragraph.strip()
    trimmed_style = style_note.strip() if style_note is not None else None

    if not trimmed_title:
        raise IdeaValidationError("title is required")
    if "\n" in trimmed_title or "\r" in trimmed_title:
        raise IdeaValidationError("title must be a single line")
    if len(trimmed_title) > _TITLE_MAX:
        raise IdeaValidationError(f"title must be at most {_TITLE_MAX} characters")
    if not trimmed_paragraph:
        raise IdeaValidationError("paragraph is required")
    if len(trimmed_paragraph) < _PARAGRAPH_MIN:
        raise IdeaValidationError(f"paragraph must be at least {_PARAGRAPH_MIN} characters")
    if len(trimmed_paragraph) > _PARAGRAPH_MAX:
        raise IdeaValidationError(f"paragraph must be at most {_PARAGRAPH_MAX} characters")
    if trimmed_style is not None and len(trimmed_style) > _STYLE_NOTE_MAX:
        raise IdeaValidationError(f"style_note must be at most {_STYLE_NOTE_MAX} characters")


def build_metadata_json(style_note: str | None) -> dict | None:
    """Return metadata payload when a style note is present."""
    if style_note is None:
        return None
    trimmed = style_note.strip()
    if not trimmed:
        return None
    return {"style_note": trimmed}


async def capture_idea(
    *,
    project_id: uuid.UUID,
    title: str,
    paragraph: str,
    style_note: str | None,
    blobs: BlobStore,
    versions: AssetVersionStore,
) -> StoredAsset:
    """Validate, serialize ``idea.txt``, and persist as ``stage=IDEA``."""
    validate_idea_fields(title=title, paragraph=paragraph, style_note=style_note)
    trimmed_title = title.strip()
    trimmed_paragraph = paragraph.strip()
    data = build_idea_text(trimmed_title, trimmed_paragraph)
    metadata_json = build_metadata_json(style_note)

    return await store_asset(
        data=data,
        stage=AssetStage.IDEA,
        project_id=project_id,
        blobs=blobs,
        versions=versions,
        content_type="text/plain",
        metadata_json=metadata_json,
    )
