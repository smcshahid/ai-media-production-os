"""LangGraph Story Architect graph builder (T-12-01)."""

from __future__ import annotations

from aimpos_config import Settings
from langgraph.graph import END, START, StateGraph

from app.agents.story_architect.constants import AGENT_ID
from app.agents.story_architect.nodes import draft_story_node, finalize_node, load_idea_node
from app.agents.story_architect.state import StoryArchitectState


def build_story_architect_graph(settings: Settings):
    """Compile a linear Story Architect graph bound to runtime settings."""

    def _draft(state: StoryArchitectState) -> StoryArchitectState:
        return draft_story_node(state, settings)

    graph = StateGraph(StoryArchitectState)
    graph.add_node("load_idea", load_idea_node)
    graph.add_node("draft_story", _draft)
    graph.add_node("finalize", finalize_node)
    graph.add_edge(START, "load_idea")
    graph.add_edge("load_idea", "draft_story")
    graph.add_edge("draft_story", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def run_story_architect_graph(
    settings: Settings,
    *,
    idea_text: str,
    style_note: str | None,
    rejection_note: str | None = None,
) -> StoryArchitectState:
    """Execute the Story Architect graph and return terminal state."""
    compiled = build_story_architect_graph(settings)
    result: StoryArchitectState = compiled.invoke(
        {
            "idea_text": idea_text,
            "style_note": style_note,
            "rejection_note": rejection_note,
        }
    )
    if result.get("error"):
        raise RuntimeError(f"{AGENT_ID} failed: {result['error']}")
    if not result.get("story_md"):
        raise RuntimeError(f"{AGENT_ID} failed: empty story_md")
    return result
