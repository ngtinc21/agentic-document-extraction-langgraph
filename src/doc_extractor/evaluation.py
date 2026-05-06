"""Evaluation helpers for comparing results against optional ground truth."""

from __future__ import annotations

from typing import Any

from .schemas import EvaluationSummary, ExtractionResult


def normalize_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "na"
    return str(value).replace(",", "").strip().lower()


def evaluate_results(
    results: list[ExtractionResult],
    expected_results: list[dict[str, Any]],
) -> EvaluationSummary:
    expected_by_id = {item["id"]: item for item in expected_results}
    results_by_id = {item.id: item for item in results}

    exact_matches = 0
    mismatches = 0
    missing_expected = 0

    for field_id, expected in expected_by_id.items():
        actual = results_by_id.get(field_id)
        if actual is None or actual.value is None:
            missing_expected += 1
            continue
        value_matches = normalize_value(actual.value) == normalize_value(expected.get("value"))
        unit_matches = normalize_value(actual.unit) == normalize_value(expected.get("unit"))
        if value_matches and unit_matches:
            exact_matches += 1
        else:
            mismatches += 1

    total = len(expected_by_id)
    extracted_count = sum(1 for result in results if result.value is not None)
    review_count = sum(1 for result in results if result.needs_review)

    return EvaluationSummary(
        total_fields=total,
        exact_matches=exact_matches,
        mismatches=mismatches,
        missing_expected=missing_expected,
        accuracy=exact_matches / total if total else 0.0,
        coverage=extracted_count / total if total else 0.0,
        review_rate=review_count / total if total else 0.0,
    )
