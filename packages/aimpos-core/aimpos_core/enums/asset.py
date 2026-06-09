"""Asset stage enum — the producing stage recorded on an ``asset_versions`` row."""

from enum import StrEnum


class AssetStage(StrEnum):
    """Stage that produced an asset version.

    Mirrors :class:`~aimpos_core.enums.pipeline.PipelineStage` for the Visual
    MVP but is a distinct type: pipeline stages describe workflow progress,
    asset stages classify stored bytes.
    """

    IDEA = "IDEA"
    STORY = "STORY"
    SCRIPT = "SCRIPT"
    STORYBOARD = "STORYBOARD"
