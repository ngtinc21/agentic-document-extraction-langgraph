from doc_extractor.schemas import DictionaryEntry, ExtractionResult
from doc_extractor.validation import validate_result


def test_invalid_numeric_value_routes_to_review():
    entry = DictionaryEntry(
        id="water",
        label="Water",
        definition="Water value",
        expected_type="number",
        expected_unit="cubic meters",
    )
    result = ExtractionResult(
        id="water",
        value="not a number",
        unit="cubic meters",
        status="extracted",
        evidence_id="ev1",
        confidence="high",
    )

    validated = validate_result(entry, result)

    assert validated.status == "invalid"
    assert validated.needs_review is True
    assert "value_is_not_numeric" in validated.validation_messages


def test_unit_mismatch_routes_to_review():
    entry = DictionaryEntry(
        id="emissions",
        label="Emissions",
        definition="Emissions value",
        expected_type="number",
        expected_unit="tCO2e",
    )
    result = ExtractionResult(
        id="emissions",
        value="100",
        unit="kgCO2e",
        status="extracted",
        evidence_id="ev1",
        confidence="high",
    )

    validated = validate_result(entry, result)

    assert validated.status == "needs_review"
    assert "unit_mismatch" in validated.validation_messages
