# packages/ — Shared Python Libraries

Installed editable into `api/` and `worker/`. Prevents API/worker drift.

| Package | Consumers | Contents |
|---------|-----------|----------|
| `aimpos-core` | api, worker | `enums/` (PipelineStage, AssetStage), `models/` (Pydantic DTOs), `events/`, `exceptions/` |
| `aimpos-config` | api, worker | `settings.py` (Pydantic Settings), `logging.py` (structured JSON) |

**Rule:** enums and DTOs live here; SQLAlchemy models stay in `api/infrastructure/db/` (persistence ≠ domain). `pyproject.toml` files land with US-04 / US-03.
