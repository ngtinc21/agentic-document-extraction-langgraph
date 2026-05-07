"""Run the synthetic procurement demo without requiring an API key."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from doc_extractor.graph import run_workflow  # noqa: E402
from doc_extractor.io import write_json  # noqa: E402


def main() -> None:
    job_path = PROJECT_ROOT / "domains" / "procurement" / "job.json"
    output_path = PROJECT_ROOT / "outputs" / "procurement_demo_result.json"
    result = run_workflow(job_path)
    write_json(output_path, result)

    evaluation = result.get("evaluation_summary", {})
    verified_sources = [
        item for item in result.get("verified_sources", [])
        if item.get("status") == "verified"
    ]
    print("Dictionary-driven procurement demo completed")
    print(f"Verified sources: {len(verified_sources)}")
    print(f"Fields: {evaluation.get('total_fields')}")
    print(f"Accuracy: {evaluation.get('accuracy')}")
    print(f"Coverage: {evaluation.get('coverage')}")
    print(f"Review rate: {evaluation.get('review_rate')}")
    print(f"Output: {output_path}")
    print(json.dumps(result["results"][:3], indent=2))


if __name__ == "__main__":
    main()
