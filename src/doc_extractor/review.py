"""Human review import/export helpers."""

from __future__ import annotations

from pathlib import Path

from .io import read_json, write_json
from .schemas import ExtractionResult


def export_review_queue(
    output_path: Path,
    *,
    job_id: str,
    review_queue: list[dict],
) -> None:
    """Write review queue records to a JSON file for manual editing."""

    if not review_queue:
        return

    write_json(
        output_path,
        {
            "job_id": job_id,
            "instructions": (
                "Edit reviewed_results with corrected ExtractionResult objects, then set "
                "run_options.review_input_path to this file or another reviewed JSON file."
            ),
            "review_queue": review_queue,
            "reviewed_results": review_queue,
        },
    )


def apply_review_overrides(
    results: list[ExtractionResult],
    review_input_path: Path | None,
) -> list[ExtractionResult]:
    """Apply reviewed result overrides when a review JSON file is provided."""

    if not review_input_path or not review_input_path.exists():
        return results

    payload = read_json(review_input_path)
    overrides = {
        item.id: item
        for item in (
            ExtractionResult.model_validate(raw)
            for raw in payload.get("reviewed_results", [])
        )
    }
    if not overrides:
        return results

    return [overrides.get(result.id, result) for result in results]
