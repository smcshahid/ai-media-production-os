"""Shared runtime configuration for AIMPOS-Spark services."""

from aimpos_config.logging import configure_logging
from aimpos_config.settings import Settings, get_settings

__all__ = ["Settings", "configure_logging", "get_settings"]
