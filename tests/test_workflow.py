from pathlib import Path

from doc_extractor.graph import run_workflow

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_esg_demo_workflow_runs_end_to_end():
    result = run_workflow(PROJECT_ROOT / "domains" / "esg" / "job.json")

    assert result["job_id"] == "esg-demo-example-solar-2024"
    assert len(result["results"]) == 12
    assert result["validation_summary"]["review_count"] == 0
    assert result["evaluation_summary"]["accuracy"] == 1.0
    assert result["evaluation_summary"]["coverage"] == 1.0
