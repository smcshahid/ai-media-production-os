"""US-18 run_video_agent activity tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import asyncio

from app.agents.video.constants import SOURCE_SLIDESHOW
from app.agents.video.validate import VideoProbeResult
from app.temporal.activities.video import run_video_agent
from app.tools.assets import ApprovedStoryboardBatch, ApprovedStoryboardFrame, StoredVideoAsset
from app.tools.video_i2v import VideoI2VError

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PROBE = VideoProbeResult(duration_sec=20.0, width=1280, height=720, codec="h264")


def _settings() -> MagicMock:
    settings = MagicMock()
    settings.video_i2v_enabled = False
    return settings


def _batch() -> ApprovedStoryboardBatch:
    frames = tuple(
        ApprovedStoryboardFrame(
            asset_version_id=uuid.uuid4(),
            content_hash=f"h{i}",
            minio_key=f"k{i}",
            frame_index=i,
            png_bytes=PNG,
        )
        for i in range(1, 5)
    )
    return ApprovedStoryboardBatch(batch_version=1, frames=frames)


def test_run_video_agent_happy_path_slideshow() -> None:
    project_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    stored = StoredVideoAsset(
        asset_version_id=uuid.uuid4(),
        content_hash="vh",
        minio_key="vk",
        version=1,
    )

    with patch("app.temporal.activities.video.get_settings", return_value=_settings()):
        with patch(
            "app.temporal.activities.video.fetch_approved_storyboard_batch",
            return_value=_batch(),
        ):
            with patch(
                "app.temporal.activities.video.fetch_latest_video_rejection_rationale",
                return_value=None,
            ):
                with patch(
                    "app.temporal.activities.video.try_comfyui_i2v",
                    side_effect=VideoI2VError("disabled"),
                ):
                    with patch(
                        "app.temporal.activities.video.render_slideshow_mp4",
                        return_value=(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100, PROBE),
                    ):
                        with patch(
                            "app.temporal.activities.video.store_video_asset",
                            return_value=stored,
                        ):
                            with patch("app.temporal.activities.video.append_audit_event"):
                                result = asyncio.run(run_video_agent(project_id, run_id))

    assert result == str(stored.asset_version_id)


def test_run_video_agent_uses_rejection_note_from_db() -> None:
    project_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    stored = StoredVideoAsset(
        asset_version_id=uuid.uuid4(),
        content_hash="vh",
        minio_key="vk",
        version=2,
    )
    store_kwargs: dict = {}

    def capture_store(_settings, **kwargs):  # type: ignore[no-untyped-def]
        store_kwargs.update(kwargs)
        return stored

    with patch("app.temporal.activities.video.get_settings", return_value=_settings()):
        with patch(
            "app.temporal.activities.video.fetch_approved_storyboard_batch",
            return_value=_batch(),
        ):
            with patch(
                "app.temporal.activities.video.fetch_latest_video_rejection_rationale",
                return_value="Sharper contrast please.",
            ):
                with patch("app.temporal.activities.video.try_comfyui_i2v", side_effect=VideoI2VError("x")):
                    with patch(
                        "app.temporal.activities.video.render_slideshow_mp4",
                        return_value=(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100, PROBE),
                    ):
                        with patch(
                            "app.temporal.activities.video.store_video_asset",
                            side_effect=capture_store,
                        ):
                            with patch("app.temporal.activities.video.append_audit_event"):
                                asyncio.run(run_video_agent(project_id, run_id, ""))

    assert store_kwargs["metadata"]["rejection_note_used"] == "Sharper contrast please."
    assert store_kwargs["metadata"]["source"] == SOURCE_SLIDESHOW
