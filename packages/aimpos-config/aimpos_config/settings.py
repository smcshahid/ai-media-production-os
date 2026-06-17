"""Runtime configuration loaded from the environment.

All environment access for the api and worker services flows through this module
(coding-standards.md §settings): no `os.getenv` scattered in application code.
Field names map to UPPER_SNAKE environment variables case-insensitively; the few
that diverge from a clean Python name declare an explicit ``validation_alias``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration sourced from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "aimpos-api"
    environment: str = "local"
    log_level: str = "INFO"

    # --- Auth (US-25) ---
    api_token: str = Field(default="change-me-local-dev-token", validation_alias="AIMPOS_API_TOKEN")

    # --- PostgreSQL (US-04) ---
    database_url: str = "postgresql+psycopg://aimpos:change-me@postgresql:5432/aimpos_spark"

    # --- MinIO (US-05) ---
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = Field(default="aimpos", validation_alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(
        default="change-me-local-dev-password", validation_alias="MINIO_ROOT_PASSWORD"
    )
    minio_bucket: str = "aimpos-hot-assets"
    minio_secure: bool = False

    # --- Redis ---
    redis_url: str = "redis://redis:6379/0"

    # --- Web / CORS (US-26) ---
    # Comma-separated list of allowed browser origins for the SPA.
    cors_origins: str = "http://localhost:5173"

    # --- Temporal (US-07) ---
    temporal_address: str = Field(default="temporal:7233", validation_alias="TEMPORAL_ADDRESS")
    temporal_namespace: str = Field(default="default", validation_alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field(
        default="aimpos-spark-pipeline", validation_alias="TEMPORAL_TASK_QUEUE"
    )

    # --- Ollama (US-12+) ---
    ollama_host: str = Field(default="http://ollama:11434", validation_alias="OLLAMA_HOST")

    # --- ComfyUI (US-16+) ---
    comfyui_host: str = Field(default="http://comfyui:8188", validation_alias="COMFYUI_HOST")

    # --- ComfyUI storyboard image generation (quality upgrade) ---
    # Production workflow JSON (relative to configs/comfyui/workflows/).
    comfyui_workflow: str = Field(
        default="sdxl_storyboard_v2.json", validation_alias="COMFYUI_WORKFLOW"
    )
    # SDXL is trained at ~1MP; 1344x768 is the 16:9 sweet spot for video-bound stills.
    # All shipped engines (SDXL/RealVisXL/Flux/Z-Image) render natively at this size.
    comfyui_width: int = Field(default=1344, validation_alias="COMFYUI_WIDTH")
    comfyui_height: int = Field(default=768, validation_alias="COMFYUI_HEIGHT")
    # Sampler params are OPTIONAL OVERRIDES. When unset (None) the selected
    # workflow JSON's own values are used, so each engine ships correct defaults
    # (e.g. SDXL 28 steps/cfg 7, Flux 20 steps/cfg 1, Z-Image 8 steps/cfg 1).
    # Only set these to force-override a specific workflow's sampler.
    comfyui_steps: int | None = Field(default=None, validation_alias="COMFYUI_STEPS")
    comfyui_cfg: float | None = Field(default=None, validation_alias="COMFYUI_CFG")
    comfyui_sampler: str | None = Field(default=None, validation_alias="COMFYUI_SAMPLER")
    comfyui_scheduler: str | None = Field(default=None, validation_alias="COMFYUI_SCHEDULER")
    # Hi-res fix second pass (only applied when the workflow declares a hires node).
    comfyui_hires_steps: int | None = Field(default=None, validation_alias="COMFYUI_HIRES_STEPS")
    comfyui_generate_timeout_s: float = Field(
        default=180.0, validation_alias="COMFYUI_GENERATE_TIMEOUT_S"
    )

    # --- ComfyUI WAN 2.2 image-to-video (US-18 phase 2) ---
    video_i2v_enabled: bool = Field(default=False, validation_alias="VIDEO_I2V_ENABLED")
    video_i2v_workflow: str = Field(
        default="wan22_i2v.json", validation_alias="VIDEO_I2V_WORKFLOW"
    )
    video_i2v_width: int = Field(default=832, validation_alias="VIDEO_I2V_WIDTH")
    video_i2v_height: int = Field(default=480, validation_alias="VIDEO_I2V_HEIGHT")
    # 81 frames @ 16fps ~= 5s of motion per storyboard frame.
    video_i2v_frames: int = Field(default=81, validation_alias="VIDEO_I2V_FRAMES")
    video_i2v_fps: int = Field(default=16, validation_alias="VIDEO_I2V_FPS")
    video_i2v_steps: int = Field(default=20, validation_alias="VIDEO_I2V_STEPS")
    video_i2v_timeout_s: float = Field(
        default=1200.0, validation_alias="VIDEO_I2V_TIMEOUT_S"
    )

    # --- Config bundle (prompts, model pins) ---
    config_root: str = Field(default="/srv/configs", validation_alias="AIMPOS_CONFIG_ROOT")


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings (cached so the env is read once)."""
    return Settings()
