"""LangGraph Cinematography graph builder (US-16)."""

from __future__ import annotations

from aimpos_config import Settings
from langgraph.graph import END, START, StateGraph

from app.agents.cinematography.constants import AGENT_ID
from app.agents.cinematography.nodes import load_script_context_node, plan_shots_node
from app.agents.cinematography.state import CinematographyState


def build_cinematography_graph(settings: Settings):
    def _plan(state: CinematographyState) -> CinematographyState:
        return plan_shots_node(state, settings)

    graph = StateGraph(CinematographyState)
    graph.add_node("load_script", load_script_context_node)
    graph.add_node("plan_shots", _plan)
    graph.add_edge(START, "load_script")
    graph.add_edge("load_script", "plan_shots")
    graph.add_edge("plan_shots", END)
    return graph.compile()


def run_cinematography_graph(
    settings: Settings,
    *,
    script_fountain: str,
    style_note: str | None = None,
    rejection_note: str | None = None,
) -> CinematographyState:
    compiled = build_cinematography_graph(settings)
    result: CinematographyState = compiled.invoke(
        {
            "script_fountain": script_fountain,
            "style_note": style_note,
            "rejection_note": rejection_note,
        }
    )
    if result.get("error"):
        raise RuntimeError(f"{AGENT_ID} failed: {result['error']}")
    if not result.get("shots"):
        raise RuntimeError(f"{AGENT_ID} failed: empty shots")
    return result
