"""US-16 cinematography JSON parsing."""

from __future__ import annotations

from app.agents.cinematography.nodes import _parse_shot_plan_json


def test_parse_shot_plan_json_from_fenced_block() -> None:
    raw = """Here is the plan:
```json
{"shots": [
  {"frame_index": 1, "shot_label": "A", "prompt": "one"},
  {"frame_index": 2, "shot_label": "B", "prompt": "two"},
  {"frame_index": 3, "shot_label": "C", "prompt": "three"},
  {"frame_index": 4, "shot_label": "D", "prompt": "four"}
]}
```"""
    shots = _parse_shot_plan_json(raw)
    assert len(shots) == 4
    assert shots[0]["frame_index"] == 1
