"""Serializable workflow state used by LangGraph nodes."""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class WorkflowState(TypedDict, total=False):
    """Mutable state passed between extraction workflow nodes."""

    job_path: str
    job_base_dir: str
    job: dict[str, Any]
    source_candidates: list[dict[str, Any]]
    ranked_sources: list[dict[str, Any]]
    verified_sources: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    results: list[dict[str, Any]]
    extraction_attempts: int
    validation_summary: dict[str, Any]
    review_queue: list[dict[str, Any]]
    last_completed_node: str
    aggregate: dict[str, Any]
    evaluation_summary: dict[str, Any]
