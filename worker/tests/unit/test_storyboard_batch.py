"""US-16 atomic storyboard batch store (D-44 / D-45)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.agents.cinematography.constants import STORYBOARD_FRAME_COUNT
from app.tools.assets import StoryboardBatchStoreError, StoryboardFrameInput, store_storyboard_batch

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _frames() -> list[StoryboardFrameInput]:
    return [
        StoryboardFrameInput(
            frame_index=i,
            png_bytes=PNG + bytes([i]),
            prompt=f"shot {i}",
            seed=40 + i,
            shot_label=f"S{i}",
        )
        for i in range(1, STORYBOARD_FRAME_COUNT + 1)
    ]


def test_store_storyboard_batch_inserts_four_rows_and_lineage() -> None:
    settings = MagicMock()
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    script_parent = uuid.uuid4()

    mock_conn = MagicMock()
    mock_conn.execute.return_value.scalar_one.return_value = 1

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    mock_client = MagicMock()

    with patch("app.tools.assets._minio_client", return_value=mock_client):
        with patch("app.tools.assets._engine", return_value=mock_engine):
            stored = store_storyboard_batch(
                settings,
                project_id=project_id,
                pipeline_run_id=run_id,
                script_parent_id=script_parent,
                frames=_frames(),
            )

    assert len(stored) == STORYBOARD_FRAME_COUNT
    assert all(s.version == 1 for s in stored)
    assert mock_client.put_object.call_count == STORYBOARD_FRAME_COUNT
    # asset insert + lineage insert per frame
    assert mock_conn.execute.call_count >= STORYBOARD_FRAME_COUNT * 2


def test_store_storyboard_batch_rolls_back_minio_on_db_failure() -> None:
    settings = MagicMock()
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    script_parent = uuid.uuid4()

    version_row = MagicMock()
    version_row.scalar_one.return_value = 1
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = [version_row, RuntimeError("db down")]

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    mock_client = MagicMock()

    with patch("app.tools.assets._minio_client", return_value=mock_client):
        with patch("app.tools.assets._engine", return_value=mock_engine):
            with patch("app.tools.assets._rollback_minio_keys") as rollback:
                with pytest.raises(StoryboardBatchStoreError):
                    store_storyboard_batch(
                        settings,
                        project_id=project_id,
                        pipeline_run_id=run_id,
                        script_parent_id=script_parent,
                        frames=_frames(),
                    )
                rollback.assert_called_once()
