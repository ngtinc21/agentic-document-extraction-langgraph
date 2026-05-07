"""LangGraph workflow assembly with a sequential fallback for lightweight demos."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .checkpointing import load_latest_checkpoint, resolve_checkpoint_path, save_checkpoint
from .io import load_job_file
from .nodes import (
    aggregate_results_node,
    apply_human_review_node,
    discover_source_urls_node,
    evaluate_against_ground_truth_node,
    evidence_scout_node,
    extract_values_node,
    human_review_gate_node,
    load_job_node,
    load_sources_node,
    rank_source_urls_node,
    validate_results_node,
    verify_source_urls_node,
)
from .schemas import ExtractionJob, ValidationSummary
from .state import WorkflowState

NODE_ORDER = [
    "load_job",
    "discover_source_urls",
    "rank_source_urls",
    "verify_source_urls",
    "load_sources",
    "evidence_scout",
    "extract_values",
    "validate_results",
    "human_review_gate",
    "apply_human_review",
    "aggregate_results",
    "evaluate_against_ground_truth",
]

NODE_FUNCTIONS = {
    "load_job": load_job_node,
    "discover_source_urls": discover_source_urls_node,
    "rank_source_urls": rank_source_urls_node,
    "verify_source_urls": verify_source_urls_node,
    "load_sources": load_sources_node,
    "evidence_scout": evidence_scout_node,
    "extract_values": extract_values_node,
    "validate_results": validate_results_node,
    "human_review_gate": human_review_gate_node,
    "apply_human_review": apply_human_review_node,
    "aggregate_results": aggregate_results_node,
    "evaluate_against_ground_truth": evaluate_against_ground_truth_node,
}


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
    for node_name, node_fn in NODE_FUNCTIONS.items():
        graph.add_node(node_name, _checkpointed(node_name, node_fn))

    graph.add_edge(START, "load_job")
    graph.add_edge("load_job", "discover_source_urls")
    graph.add_edge("discover_source_urls", "rank_source_urls")
    graph.add_edge("rank_source_urls", "verify_source_urls")
    graph.add_edge("verify_source_urls", "load_sources")
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
    graph.add_edge("human_review_gate", "apply_human_review")
    graph.add_edge("apply_human_review", "aggregate_results")
    graph.add_edge("aggregate_results", "evaluate_against_ground_truth")
    graph.add_edge("evaluate_against_ground_truth", END)
    return graph.compile()


def run_workflow(job_path: str | Path) -> dict[str, Any]:
    """Run the extraction workflow and return the aggregate result payload."""

    initial_state = _initial_state(job_path)
    compiled_graph = build_graph()
    if compiled_graph is not None and not initial_state.get("last_completed_node"):
        final_state = compiled_graph.invoke(initial_state)
    else:
        final_state = _run_from_state(initial_state)
    return final_state["aggregate"]


def _checkpointed(node_name: str, node_fn: Any) -> Any:
    def wrapped(state: WorkflowState) -> WorkflowState:
        next_state = node_fn(state)
        next_state = {**next_state, "last_completed_node": node_name}
        save_checkpoint(node_name, next_state)
        return next_state

    return wrapped


def _initial_state(job_path: str | Path) -> WorkflowState:
    path = Path(job_path)
    job, base_dir = load_job_file(path)
    initial_state: WorkflowState = {"job_path": str(path)}
    if not job.run_options.resume_from_checkpoint:
        return initial_state

    lookup_state: WorkflowState = {
        "job_path": str(path),
        "job": job.model_dump(),
        "job_base_dir": str(base_dir),
    }
    checkpoint_path = resolve_checkpoint_path(lookup_state)
    if checkpoint_path is None:
        return initial_state

    checkpoint_state = load_latest_checkpoint(checkpoint_path)
    return checkpoint_state or initial_state


def _run_from_state(initial_state: WorkflowState) -> WorkflowState:
    """Run or resume the retry-aware workflow without relying on LangGraph replay."""

    state = initial_state
    start_index = _next_node_index(state.get("last_completed_node"))

    for node_name in NODE_ORDER[start_index:]:
        if node_name in {"extract_values", "validate_results"}:
            break
        state = _checkpointed(node_name, NODE_FUNCTIONS[node_name])(state)

    if "validation_summary" not in state or route_after_validation(state) == "retry_extraction":
        while True:
            state = _checkpointed("extract_values", extract_values_node)(state)
            state = _checkpointed("validate_results", validate_results_node)(state)
            if route_after_validation(state) != "retry_extraction":
                break

    for node_name in [
        "human_review_gate",
        "apply_human_review",
        "aggregate_results",
        "evaluate_against_ground_truth",
    ]:
        if _node_already_completed(state, node_name):
            continue
        state = _checkpointed(node_name, NODE_FUNCTIONS[node_name])(state)
    return state


def _next_node_index(last_completed_node: str | None) -> int:
    if not last_completed_node or last_completed_node not in NODE_ORDER:
        return 0
    return NODE_ORDER.index(last_completed_node) + 1


def _node_already_completed(state: WorkflowState, node_name: str) -> bool:
    last_completed_node = state.get("last_completed_node")
    if last_completed_node not in NODE_ORDER:
        return False
    return NODE_ORDER.index(last_completed_node) >= NODE_ORDER.index(node_name)
