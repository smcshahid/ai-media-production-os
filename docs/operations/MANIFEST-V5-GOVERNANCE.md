# Manifest v5 Governance Notes (Phase 7.5)

**Authority:** Product Architect / Release Manager  
**Baseline:** D-92 (Phase 7) + D-93 (Phase 7.5 snapshot)

---

## Version ladder

| Version | Trigger | New fields | Legacy preserved |
|---------|---------|------------|------------------|
| **v1** | Default single-scene, no narration | — | Yes |
| **v2** | `scene_count >= 2` | `scene_count`, scene paths | v1 runs unchanged |
| **v3** | NARRATION assets present | narration paths | v1/v2 unchanged |
| **v4** | Run has `episode_id` | `episode_id`, `episode_number`, `episodes/episode_XX/` layout | v1–v3 unchanged |
| **v5** | Run has resolvable character payload | `characters[]` profile mirror | v1–v4 unchanged |

**Phase 7.5 change:** v5 resolution uses `pipeline_runs.character_snapshot` when present; legacy runs without snapshot still resolve from live `characters` rows at export time.

---

## `characters[]` schema (v5)

Each entry mirrors the character profile at pipeline start:

| Field | Type | Required |
|-------|------|----------|
| `id` | string (UUID) | yes |
| `name` | string | yes |
| `description` | string \| null | no |
| `role` | string \| null | no |
| `visual_traits` | string \| null | no |
| `personality_notes` | string \| null | no |

No additional fields are permitted in v5 pilot scope.

---

## Coexistence rules

- v5 may include episode fields (v4 layout) and narration paths (v3) simultaneously.
- Absence of `characters[]` does **not** downgrade episode or narration metadata.
- Empty `character_ids` with null snapshot → not v5.

---

## Backward compatibility verification

Automated: `api/tests/unit/test_character_export.py`, `test_episode_export.py`, `test_narration_export.py`, `test_multi_scene_export.py`.

Olares: US-V08B **PATH F** samples legacy runs for v2/v3/v4 and attests v5 on character runs.

---

## Consumer guidance

1. Read `manifest_version` first.
2. For v5+, treat `characters[]` as **run-bound snapshot**, not live project state.
3. Do not infer character continuity from export alone across runs — compare snapshots explicitly.
