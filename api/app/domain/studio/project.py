"""Project domain rules — framework-free (no FastAPI / SQLAlchemy imports).

Only `aimpos-core` (shared domain primitives) is imported here. The identity of
the default project is a business decision (Sprint 0 success criterion 2: a fresh
deployment starts with one "AIMPOS Spark Demo" project), so it lives in the
domain rather than in the seed adapter or the database layer.
"""

from __future__ import annotations

from aimpos_core.enums import ProjectStatus

DEFAULT_PROJECT_NAME = "AIMPOS Spark Demo"
DEFAULT_PROJECT_STATUS = ProjectStatus.ACTIVE
