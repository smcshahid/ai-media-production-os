"""Character bible pilot constants (Phase 7 / SCR-2026-005)."""

from __future__ import annotations

MAX_CHARACTERS_PER_PROJECT = 3
MAX_CHARACTERS_PER_RUN = 3


def format_character_bible(profiles: list[dict[str, str]]) -> str:
    """Format character profiles for LLM prompt injection."""
    if not profiles:
        return ""
    blocks: list[str] = []
    for profile in profiles:
        name = (profile.get("name") or "").strip()
        if not name:
            continue
        role = (profile.get("role") or "").strip()
        header = f"### {name}" + (f" ({role})" if role else "")
        parts = [header]
        for label, key in (
            ("Description", "description"),
            ("Visual traits", "visual_traits"),
            ("Personality", "personality_notes"),
        ):
            value = (profile.get(key) or "").strip()
            if value:
                parts.append(f"- **{label}:** {value}")
        blocks.append("\n".join(parts))
    if not blocks:
        return ""
    return (
        "## Character Bible (maintain consistency)\n\n"
        + "\n\n".join(blocks)
        + "\n\nMaintain exact character names, roles, visual traits, and personality across "
        "all scenes and episodes. Do not rename, redesign, merge, or omit listed characters. "
        "Reference only the traits documented above."
    )
