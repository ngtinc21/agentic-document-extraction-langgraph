"""LangGraph workflow assembly with a sequential fallback for lightweight demos."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .nodes import (
    aggregate_results_node,
    evaluate_against_ground_truth_node,
    evidence_scout_node,
    extract_values_node,
    human_review_gate_node,
    load_job_node,
    load_sources_node,
    validate_results_node,
)
from .state import WorkflowState

NODE_SEQUENCE: list[Callable[[WorkflowState], WorkflowState]] = [
    load_job_node,
    load_sources_node,
    evidence_scout_node,
    extract_values_node,
    validate_results_node,
    human_review_gate_node,
    aggregate_results_node,
    evaluate_against_ground_truth_node,
]


def build_graph() -> Any:
    """Build a LangGraph graph when the dependency is available."""

    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:  # pragma: no cover - used only for minimal local smoke runs
        return None

    graph = StateGraph(WorkflowState)
    graph.add_node("load_job", load_job_node)
    graph.add_node("load_sources", load_sources_node)
    graph.add_node("evidence_scout", evidence_scout_node)
    graph.add_node("extract_values", extract_values_node)
    graph.add_node("validate_results", validate_results_node)
    graph.add_node("human_review_gate", human_review_gate_node)
    graph.add_node("aggregate_results", aggregate_results_node)
    graph.add_node("evaluate_against_ground_truth", evaluate_against_ground_truth_node)

    graph.add_edge(START, "load_job")
    graph.add_edge("load_job", "load_sources")
    graph.add_edge("load_sources", "evidence_scout")
    graph.add_edge("evidence_scout", "extract_values")
    graph.add_edge("extract_values", "validate_results")
    graph.add_edge("validate_results", "human_review_gate")
    graph.add_edge("human_review_gate", "aggregate_results")
    graph.add_edge("aggregate_results", "evaluate_against_ground_truth")
    graph.add_edge("evaluate_against_ground_truth", END)
    return graph.compile()


def run_workflow(job_path: str | Path) -> dict[str, Any]:
    """Run the extraction workflow and return the aggregate result payload."""

    initial_state: WorkflowState = {"job_path": str(Path(job_path))}
    compiled_graph = build_graph()
    if compiled_graph is not None:
        final_state = compiled_graph.invoke(initial_state)
    else:
        final_state = initial_state
        for node in NODE_SEQUENCE:
            final_state = node(final_state)
    return final_state["aggregate"]
