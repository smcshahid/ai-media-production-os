"""US-16 run_storyboard_agent activity (mocked externals)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import asyncio

from app.agents.cinematography.constants import STORYBOARD_FRAME_COUNT
from app.temporal.activities.storyboard import run_storyboard_agent
from app.tools.assets import ApprovedScriptAsset, StoredStoryboardFrame

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_run_storyboard_agent_happy_path() -> None:
    project_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    script_id = uuid.uuid4()

    shots = [
        {"frame_index": i, "shot_label": f"S{i}", "prompt": f"p{i}"}
        for i in range(1, STORYBOARD_FRAME_COUNT + 1)
    ]
    stored = [
        StoredStoryboardFrame(
            asset_version_id=uuid.uuid4(),
            content_hash=f"hash{i}",
            minio_key=f"k{i}",
            version=1,
            frame_index=i,
        )
        for i in range(1, STORYBOARD_FRAME_COUNT + 1)
    ]

    with patch("app.temporal.activities.storyboard.get_settings", return_value=MagicMock()):
        with patch(
            "app.temporal.activities.storyboard._read_run_scene_count",
            return_value=1,
        ):
            with patch(
                "app.temporal.activities.storyboard.fetch_approved_script",
                return_value=ApprovedScriptAsset(
                    asset_version_id=script_id,
                    script_fountain="INT. LAB - DAY\n\nAction.\n\nELARA\nHello.",
                    minio_key="k",
                    version=1,
                ),
            ):
                with patch(
                    "app.tools.assets.fetch_latest_idea",
                    side_effect=Exception("no idea"),
                ):
                    with patch(
                        "app.temporal.activities.storyboard.fetch_latest_storyboard_rejection_rationale",
                        return_value=None,
                    ):
                        with patch(
                            "app.temporal.activities.storyboard.run_cinematography_graph",
                            return_value={
                                "shots": shots,
                                "model_id": "qwen3:14b",
                                "duration_ms": 100,
                            },
                        ):
                            with patch(
                                "app.temporal.activities.storyboard.unload_ollama_before_comfyui",
                                return_value="qwen3:14b",
                            ):
                                with patch(
                                    "app.temporal.activities.storyboard.generate_storyboard_png",
                                    return_value=PNG,
                                ):
                                    with patch(
                                        "app.temporal.activities.storyboard.store_storyboard_batch",
                                        return_value=stored,
                                    ):
                                        with patch(
                                            "app.temporal.activities.storyboard.append_audit_event"
                                        ):
                                            result = asyncio.run(
                                                run_storyboard_agent(project_id, run_id)
                                            )

    assert len(result.split(",")) == STORYBOARD_FRAME_COUNT
