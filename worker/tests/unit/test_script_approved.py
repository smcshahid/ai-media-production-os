"""US-15 approved script + D-42 rejection rationale helpers."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.tools.assets import (
    ApprovedScriptNotFoundError,
    ApprovedStoryNotFoundError,
    fetch_approved_script,
    fetch_latest_script_rejection_rationale,
)


def test_fetch_latest_script_rejection_rationale_from_db() -> None:
    settings = MagicMock()
    run_id = uuid.uuid4()

    mock_conn = MagicMock()
    mock_conn.execute.return_value.first.return_value = ("Tighten the dialogue.",)

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with patch("app.tools.assets._engine", return_value=mock_engine):
        note = fetch_latest_script_rejection_rationale(settings, pipeline_run_id=run_id)

    assert note == "Tighten the dialogue."


def test_fetch_latest_script_rejection_rationale_none_when_missing() -> None:
    settings = MagicMock()
    run_id = uuid.uuid4()

    mock_conn = MagicMock()
    mock_conn.execute.return_value.first.return_value = None

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with patch("app.tools.assets._engine", return_value=mock_engine):
        note = fetch_latest_script_rejection_rationale(settings, pipeline_run_id=run_id)

    assert note is None


def test_fetch_approved_script_requires_approval() -> None:
    settings = MagicMock()
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()

    mock_conn = MagicMock()
    mock_conn.execute.return_value.first.return_value = None

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with patch("app.tools.assets._engine", return_value=mock_engine):
        with pytest.raises(ApprovedScriptNotFoundError):
            fetch_approved_script(settings, project_id=project_id, pipeline_run_id=run_id)


def test_approved_story_and_script_errors_are_distinct() -> None:
    assert ApprovedStoryNotFoundError is not ApprovedScriptNotFoundError
