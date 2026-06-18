"""Character profile fetch for worker activities (Phase 7)."""

from __future__ import annotations

import json
import uuid

from aimpos_config import Settings
from aimpos_core.character import format_character_bible
from sqlalchemy import create_engine, text


def fetch_run_character_profiles(
    settings: Settings, *, pipeline_run_id: uuid.UUID
) -> tuple[list[dict[str, str]], str]:
    """Return profile dicts and formatted bible text for a pipeline run."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT r.character_ids, r.project_id
                    FROM pipeline_runs r
                    WHERE r.id = :run_id
                    """
                ),
                {"run_id": str(pipeline_run_id)},
            ).first()
            if row is None or not row[0]:
                return [], ""
            raw_ids = row[0]
            project_id = row[1]
            if isinstance(raw_ids, str):
                id_list = json.loads(raw_ids)
            else:
                id_list = list(raw_ids)
            if not id_list:
                return [], ""
            placeholders = ", ".join(f":cid{i}" for i in range(len(id_list)))
            params: dict[str, str] = {"project_id": str(project_id)}
            for i, cid in enumerate(id_list):
                params[f"cid{i}"] = str(cid)
            result = conn.execute(
                text(
                    f"""
                    SELECT id, name, description, role, visual_traits, personality_notes
                    FROM characters
                    WHERE project_id = :project_id
                      AND id IN ({placeholders})
                    ORDER BY name ASC
                    """
                ),
                params,
            )
            profiles: list[dict[str, str]] = []
            for crow in result:
                profiles.append(
                    {
                        "id": str(crow[0]),
                        "name": crow[1] or "",
                        "description": crow[2] or "",
                        "role": crow[3] or "",
                        "visual_traits": crow[4] or "",
                        "personality_notes": crow[5] or "",
                    }
                )
    finally:
        engine.dispose()
    bible = format_character_bible(profiles)
    return profiles, bible
