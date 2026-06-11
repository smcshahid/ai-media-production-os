"""Resolve repo config paths (prompts, model pins) for worker runtime."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from aimpos_config import Settings


def resolve_config_root(settings: Settings) -> Path:
    """Return the config root — container path first, then repo ``configs/`` fallback."""
    configured = Path(settings.config_root)
    if configured.is_dir():
        return configured
    repo_configs = Path(__file__).resolve().parents[3] / "configs"
    if repo_configs.is_dir():
        return repo_configs
    return configured


def load_story_model(settings: Settings) -> str:
    """Pinned Ollama model for story stage (``configs/ollama/models.json``)."""
    models_path = resolve_config_root(settings) / "ollama" / "models.json"
    data = json.loads(models_path.read_text(encoding="utf-8"))
    return str(data.get("stages", {}).get("story") or data.get("default") or "qwen3:14b")


def load_story_prompt(settings: Settings, *, version: str = "v1") -> dict:
    """Load Story Architect prompt template YAML."""
    path = resolve_config_root(settings) / "prompts" / "story_architect" / f"{version}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_script_model(settings: Settings) -> str:
    """Pinned Ollama model for script stage (``configs/ollama/models.json``)."""
    models_path = resolve_config_root(settings) / "ollama" / "models.json"
    data = json.loads(models_path.read_text(encoding="utf-8"))
    return str(data.get("stages", {}).get("script") or data.get("default") or "qwen3:14b")


def load_script_prompt(settings: Settings, *, version: str = "v1") -> dict:
    """Load Screenwriter prompt template YAML."""
    path = resolve_config_root(settings) / "prompts" / "screenwriter" / f"{version}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_storyboard_model(settings: Settings) -> str:
    """Pinned Ollama model for storyboard planning (``configs/ollama/models.json``)."""
    models_path = resolve_config_root(settings) / "ollama" / "models.json"
    data = json.loads(models_path.read_text(encoding="utf-8"))
    return str(
        data.get("stages", {}).get("storyboard") or data.get("default") or "qwen3:14b"
    )


def load_storyboard_prompt(settings: Settings, *, version: str = "v1") -> dict:
    """Load Cinematography prompt template YAML."""
    path = resolve_config_root(settings) / "prompts" / "cinematography" / f"{version}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))
