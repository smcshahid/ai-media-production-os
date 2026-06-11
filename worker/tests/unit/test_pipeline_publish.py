"""Worker pipeline Redis publish tests (US-21 D-59)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.infrastructure.pipeline_publish import publish_pipeline_status


@patch("redis.from_url")
def test_publish_pipeline_status_success(mock_from_url: MagicMock) -> None:
    client = MagicMock()
    mock_from_url.return_value = client

    publish_pipeline_status(
        project_id="p1",
        run_id="r1",
        status="RUNNING",
        current_stage="STORY",
    )

    client.publish.assert_called_once()
    channel, body = client.publish.call_args[0]
    assert channel == "aimpos:pipeline:p1"
    assert "RUNNING" in body
    client.close.assert_called_once()


@patch("redis.from_url", side_effect=OSError("redis down"))
def test_publish_pipeline_status_non_fatal(_mock_from_url: MagicMock) -> None:
    publish_pipeline_status(
        project_id="p1",
        run_id="r1",
        status="RUNNING",
        current_stage="STORY",
    )
