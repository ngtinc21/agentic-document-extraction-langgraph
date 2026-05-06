"""Validation helpers for extraction results."""

from __future__ import annotations

from .schemas import DictionaryEntry, ExtractionResult, ValidationSummary

CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def validate_result(
    entry: DictionaryEntry,
    result: ExtractionResult,
    *,
    require_evidence: bool = True,
    review_threshold: str = "medium",
) -> ExtractionResult:
    messages = list(result.validation_messages)
    needs_review = result.needs_review
    status = result.status

    if require_evidence and entry.evidence_rules.required and not result.evidence_id:
        messages.append("required_evidence_missing")
        needs_review = True

    if result.value is None:
        status = "missing" if status != "invalid" else status
        needs_review = True
    elif entry.expected_type in {"number", "percentage"}:
        try:
            numeric_value = float(str(result.value).replace(",", ""))
        except ValueError:
            messages.append("value_is_not_numeric")
            status = "invalid"
            needs_review = True
        else:
            if (
                entry.validation_rules.min_value is not None
                and numeric_value < entry.validation_rules.min_value
            ):
                messages.append("value_below_minimum")
                needs_review = True
            if (
                entry.validation_rules.max_value is not None
                and numeric_value > entry.validation_rules.max_value
            ):
                messages.append("value_above_maximum")
                needs_review = True
    elif entry.expected_type == "boolean" and not isinstance(result.value, bool):
        messages.append("value_is_not_boolean")
        status = "invalid"
        needs_review = True
    elif entry.expected_type == "string" and not str(result.value).strip():
        messages.append("value_is_empty")
        status = "invalid"
        needs_review = True

    allowed_units = entry.validation_rules.allowed_units
    if allowed_units and result.unit not in allowed_units:
        messages.append("unit_not_allowed")
        needs_review = True
    elif entry.expected_unit and result.unit != entry.expected_unit:
        messages.append("unit_mismatch")
        needs_review = True

    if CONFIDENCE_ORDER[result.confidence] < CONFIDENCE_ORDER[review_threshold]:
        messages.append("confidence_below_review_threshold")
        needs_review = True

    if needs_review and status == "extracted":
        status = "needs_review"

    return result.model_copy(
        update={
            "status": status,
            "validation_messages": sorted(set(messages)),
            "needs_review": needs_review,
        }
    )


def summarize_validation(results: list[ExtractionResult]) -> ValidationSummary:
    failures: list[str] = []
    for result in results:
        for message in result.validation_messages:
            failures.append(f"{result.id}: {message}")

    return ValidationSummary(
        total_fields=len(results),
        extracted_count=sum(1 for item in results if item.status == "extracted"),
        missing_count=sum(1 for item in results if item.status == "missing"),
        review_count=sum(1 for item in results if item.needs_review),
        validation_failures=failures,
    )
