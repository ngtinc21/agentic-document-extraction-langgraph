"""LangGraph workflow assembly with a sequential fallback for lightweight demos."""

from __future__ import annotations

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
from .schemas import ExtractionJob, ValidationSummary
from .state import WorkflowState


def route_after_validation(state: WorkflowState) -> str:
    """Route invalid or uncertain results back to extraction until retry budget is used."""

    job = ExtractionJob.model_validate(state["job"])
    summary = ValidationSummary.model_validate(state["validation_summary"])
    attempts = int(state.get("extraction_attempts", 0))
    max_attempts = 1 + job.run_options.max_validation_retries

    if attempts < max_attempts and (summary.review_count > 0 or summary.validation_failures):
        return "retry_extraction"
    return "human_review"


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
    graph.add_conditional_edges(
        "validate_results",
        route_after_validation,
        {
            "retry_extraction": "extract_values",
            "human_review": "human_review_gate",
        },
    )
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
        final_state = _run_sequential_fallback(initial_state)
    return final_state["aggregate"]


def _run_sequential_fallback(initial_state: WorkflowState) -> WorkflowState:
    """Run the same retry-aware workflow when LangGraph is not installed."""

    state = load_job_node(initial_state)
    state = load_sources_node(state)
    state = evidence_scout_node(state)

    while True:
        state = extract_values_node(state)
        state = validate_results_node(state)
        if route_after_validation(state) != "retry_extraction":
            break

    state = human_review_gate_node(state)
    state = aggregate_results_node(state)
    return evaluate_against_ground_truth_node(state)
