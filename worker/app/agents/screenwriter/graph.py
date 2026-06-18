"""LangGraph Screenwriter graph builder (T-14-01)."""

from __future__ import annotations

from aimpos_config import Settings
from langgraph.graph import END, START, StateGraph

from app.agents.screenwriter.constants import AGENT_ID
from app.agents.screenwriter.nodes import (
    draft_script_node,
    finalize_script_node,
    load_story_context_node,
)
from app.agents.screenwriter.state import ScreenwriterState


def build_screenwriter_graph(settings: Settings):
    """Compile a linear Screenwriter graph bound to runtime settings."""

    def _draft(state: ScreenwriterState) -> ScreenwriterState:
        return draft_script_node(state, settings)

    graph = StateGraph(ScreenwriterState)
    graph.add_node("load_story", load_story_context_node)
    graph.add_node("draft_script", _draft)
    graph.add_node("finalize", finalize_script_node)
    graph.add_edge(START, "load_story")
    graph.add_edge("load_story", "draft_script")
    graph.add_edge("draft_script", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def run_screenwriter_graph(
    settings: Settings,
    *,
    story_text: str,
    rejection_note: str | None = None,
    scene_count: int = 1,
) -> ScreenwriterState:
    """Execute the Screenwriter graph and return terminal state."""
    compiled = build_screenwriter_graph(settings)
    result: ScreenwriterState = compiled.invoke(
        {
            "story_text": story_text,
            "rejection_note": rejection_note,
            "scene_count": scene_count,
        }
    )
    if result.get("error"):
        raise RuntimeError(f"{AGENT_ID} failed: {result['error']}")
    if not result.get("script_fountain"):
        raise RuntimeError(f"{AGENT_ID} failed: empty script_fountain")
    return result
