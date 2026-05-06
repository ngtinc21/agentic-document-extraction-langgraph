"""Serializable workflow state used by LangGraph nodes."""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class WorkflowState(TypedDict, total=False):
    """Mutable state passed between extraction workflow nodes."""

    job_path: str
    job_base_dir: str
    job: dict[str, Any]
    documents: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    results: list[dict[str, Any]]
    validation_summary: dict[str, Any]
    review_queue: list[dict[str, Any]]
    aggregate: dict[str, Any]
    evaluation_summary: dict[str, Any]
