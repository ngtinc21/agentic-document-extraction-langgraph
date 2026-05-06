from doc_extractor.evaluation import evaluate_results
from doc_extractor.schemas import ExtractionResult


def test_evaluation_counts_exact_matches_and_mismatches():
    results = [
        ExtractionResult(id="a", value="100", unit="tCO2e", status="extracted", confidence="high"),
        ExtractionResult(id="b", value="20", unit="%", status="extracted", confidence="high"),
    ]
    expected = [
        {"id": "a", "value": "100", "unit": "tCO2e"},
        {"id": "b", "value": "25", "unit": "%"},
    ]

    summary = evaluate_results(results, expected)

    assert summary.exact_matches == 1
    assert summary.mismatches == 1
    assert summary.accuracy == 0.5
