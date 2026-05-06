"""Workflow node implementations."""

from __future__ import annotations

from pathlib import Path

from .evaluation import evaluate_results
from .io import load_job_file, load_source_documents, read_json
from .providers import build_provider
from .schemas import (
    DictionaryEntry,
    EvidenceRecord,
    ExtractionJob,
    ExtractionResult,
    SourceDocument,
)
from .state import WorkflowState
from .validation import summarize_validation, validate_result


def load_job_node(state: WorkflowState) -> WorkflowState:
    job, base_dir = load_job_file(state["job_path"])
    return {**state, "job": job.model_dump(), "job_base_dir": str(base_dir)}


def load_sources_node(state: WorkflowState) -> WorkflowState:
    job = ExtractionJob.model_validate(state["job"])
    documents = load_source_documents(job, Path(state["job_base_dir"]))
    return {**state, "documents": [document.model_dump() for document in documents]}


def evidence_scout_node(state: WorkflowState) -> WorkflowState:
    job = ExtractionJob.model_validate(state["job"])
    documents = [SourceDocument.model_validate(item) for item in state["documents"]]
    provider = build_provider(job.run_options.provider)

    evidence: list[EvidenceRecord] = []
    for entry in job.dictionary:
        evidence.extend(provider.scout_evidence(entry, documents))

    return {**state, "evidence": [item.model_dump() for item in evidence]}


def extract_values_node(state: WorkflowState) -> WorkflowState:
    job = ExtractionJob.model_validate(state["job"])
    evidence = [EvidenceRecord.model_validate(item) for item in state.get("evidence", [])]
    prior_result_items = map(ExtractionResult.model_validate, state.get("results", []))
    previous_results = {
        result.id: result
        for result in prior_result_items
    }
    provider = build_provider(job.run_options.provider)

    results: list[ExtractionResult] = []
    for entry in job.dictionary:
        entry_evidence = [item for item in evidence if item.dictionary_entry_id == entry.id]
        results.append(
            provider.extract_value(
                entry,
                entry_evidence,
                previous_result=previous_results.get(entry.id),
            )
        )

    return {
        **state,
        "results": [item.model_dump() for item in results],
        "extraction_attempts": int(state.get("extraction_attempts", 0)) + 1,
    }


def validate_results_node(state: WorkflowState) -> WorkflowState:
    job = ExtractionJob.model_validate(state["job"])
    entries_by_id: dict[str, DictionaryEntry] = {entry.id: entry for entry in job.dictionary}
    results = [ExtractionResult.model_validate(item) for item in state.get("results", [])]

    validated = [
        validate_result(
            entries_by_id[result.id],
            result,
            require_evidence=job.run_options.require_evidence,
            review_threshold=job.run_options.review_confidence_threshold,
        )
        for result in results
    ]
    summary = summarize_validation(validated)
    return {
        **state,
        "results": [item.model_dump() for item in validated],
        "validation_summary": summary.model_dump(),
    }


def human_review_gate_node(state: WorkflowState) -> WorkflowState:
    review_queue = [
        result
        for result in state.get("results", [])
        if result.get("needs_review") or result.get("status") in {"needs_review", "invalid"}
    ]
    return {**state, "review_queue": review_queue}


def aggregate_results_node(state: WorkflowState) -> WorkflowState:
    job = ExtractionJob.model_validate(state["job"])
    aggregate = {
        "job_id": job.job_id,
        "domain": job.domain,
        "entity": job.entity.model_dump(),
        "results": state.get("results", []),
        "validation_summary": state.get("validation_summary", {}),
        "review_queue": state.get("review_queue", []),
    }
    return {**state, "aggregate": aggregate}


def evaluate_against_ground_truth_node(state: WorkflowState) -> WorkflowState:
    job = ExtractionJob.model_validate(state["job"])
    if not job.ground_truth_path:
        return state

    ground_truth_path = Path(state["job_base_dir"]) / job.ground_truth_path
    expected_results = read_json(ground_truth_path)["expected_results"]
    results = [ExtractionResult.model_validate(item) for item in state.get("results", [])]
    evaluation = evaluate_results(results, expected_results)
    aggregate = dict(state.get("aggregate", {}))
    aggregate["evaluation_summary"] = evaluation.model_dump()
    return {
        **state,
        "evaluation_summary": evaluation.model_dump(),
        "aggregate": aggregate,
    }
