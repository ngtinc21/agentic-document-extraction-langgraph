from doc_extractor.checkpointing import load_latest_checkpoint, save_checkpoint
from doc_extractor.review import apply_review_overrides
from doc_extractor.schemas import ExtractionResult


def test_checkpoint_round_trip(tmp_path):
    checkpoint_path = tmp_path / "workflow.sqlite"
    state = {
        "job_base_dir": str(tmp_path),
        "job": {
            "job_id": "checkpoint-test",
            "domain": "demo",
            "entity": {"name": "Example"},
            "source_documents": [],
            "run_options": {
                "enable_checkpoints": True,
                "checkpoint_path": str(checkpoint_path),
            },
        },
        "results": [],
    }

    save_checkpoint("load_job", state)
    restored = load_latest_checkpoint(checkpoint_path)

    assert restored is not None
    assert restored["last_completed_node"] == "load_job"
    assert restored["job"]["job_id"] == "checkpoint-test"


def test_review_overrides_replace_matching_result(tmp_path):
    result = ExtractionResult(
        id="demo_field",
        value=None,
        status="needs_review",
        confidence="low",
        needs_review=True,
    )
    review_path = tmp_path / "review.json"
    review_path.write_text(
        """
        {
          "reviewed_results": [
            {
              "id": "demo_field",
              "value": "Reviewed value",
              "unit": null,
              "status": "extracted",
              "evidence_id": "manual-review",
              "confidence": "high",
              "validation_messages": [],
              "needs_review": false
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    reviewed = apply_review_overrides([result], review_path)

    assert reviewed[0].value == "Reviewed value"
    assert reviewed[0].needs_review is False
