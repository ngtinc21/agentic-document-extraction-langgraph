from pathlib import Path

from doc_extractor.graph import route_after_validation, run_workflow

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_esg_demo_workflow_runs_end_to_end():
    result = run_workflow(PROJECT_ROOT / "domains" / "esg" / "job.json")

    assert result["job_id"] == "esg-demo-example-solar-2024"
    assert len(result["results"]) == 12
    assert result["validation_summary"]["review_count"] == 0
    assert result["evaluation_summary"]["accuracy"] == 1.0
    assert result["evaluation_summary"]["coverage"] == 1.0


def test_procurement_demo_runs_with_source_pipeline_and_checkpoints():
    result = run_workflow(PROJECT_ROOT / "domains" / "procurement" / "job.json")

    assert result["job_id"] == "procurement-demo-northwind-2025"
    assert len(result["results"]) == 6
    assert result["validation_summary"]["review_count"] == 0
    assert result["evaluation_summary"]["accuracy"] == 1.0
    assert result["evaluation_summary"]["coverage"] == 1.0
    assert len([item for item in result["verified_sources"] if item["status"] == "verified"]) == 3


def test_validation_route_retries_until_budget_is_used():
    state = {
        "job": {
            "job_id": "retry-test",
            "domain": "demo",
            "entity": {"name": "Example"},
            "source_documents": [],
            "run_options": {"max_validation_retries": 1},
        },
        "validation_summary": {
            "total_fields": 1,
            "extracted_count": 0,
            "missing_count": 0,
            "review_count": 1,
            "validation_failures": ["demo_field: required_evidence_missing"],
        },
        "extraction_attempts": 1,
    }

    assert route_after_validation(state) == "retry_extraction"

    state["extraction_attempts"] = 2
    assert route_after_validation(state) == "human_review"
