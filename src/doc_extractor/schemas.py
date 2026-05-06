"""Public Pydantic schemas for dictionary-driven extraction jobs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ExpectedType = Literal["number", "percentage", "boolean", "string"]
Confidence = Literal["high", "medium", "low"]
ExtractionStatus = Literal["extracted", "missing", "needs_review", "invalid"]


class EntityMetadata(BaseModel):
    """Entity being analyzed, such as a company, fund, product, or policy owner."""

    name: str
    fiscal_year: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class EvidenceRules(BaseModel):
    """Hints that guide evidence collection for one dictionary entry."""

    required: bool = True
    keywords: list[str] = Field(default_factory=list)
    source_priority: list[str] = Field(default_factory=list)


class ValidationRules(BaseModel):
    """Lightweight validation hints for extracted values."""

    min_value: float | None = None
    max_value: float | None = None
    allowed_units: list[str] = Field(default_factory=list)


class DictionaryEntry(BaseModel):
    """One field definition that drives evidence search, extraction, and validation."""

    id: str
    label: str
    definition: str
    expected_type: ExpectedType
    expected_unit: str | None = None
    extraction_guidance: str | None = None
    evidence_rules: EvidenceRules = Field(default_factory=EvidenceRules)
    validation_rules: ValidationRules = Field(default_factory=ValidationRules)

    @field_validator("id")
    @classmethod
    def id_must_be_machine_readable(cls, value: str) -> str:
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("dictionary entry id must contain only letters, numbers, '_' or '-'")
        return value


class SourceDocument(BaseModel):
    """A source document to be searched for evidence."""

    source_id: str
    title: str
    path: str
    source_type: str = "markdown"
    fiscal_year: int | None = None
    content: str | None = None


class RunOptions(BaseModel):
    """Execution options for a job."""

    provider: str = "fake"
    require_evidence: bool = True
    review_confidence_threshold: Confidence = "medium"
    max_validation_retries: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Number of times to retry extraction after validation flags a result.",
    )


class ExtractionJob(BaseModel):
    """Complete extraction job contract."""

    job_id: str
    domain: str
    entity: EntityMetadata
    source_documents: list[SourceDocument]
    dictionary: list[DictionaryEntry] = Field(default_factory=list)
    dictionary_path: str | None = None
    ground_truth_path: str | None = None
    run_options: RunOptions = Field(default_factory=RunOptions)


class EvidenceRecord(BaseModel):
    """Evidence identified for a dictionary entry."""

    evidence_id: str
    source_id: str
    dictionary_entry_id: str
    snippet: str
    location: str = "unknown"
    confidence: Confidence = "medium"
    rationale: str = ""


class ExtractionResult(BaseModel):
    """Structured result for one dictionary entry."""

    id: str
    value: str | float | bool | None
    unit: str | None = None
    status: ExtractionStatus
    evidence_id: str | None = None
    confidence: Confidence = "low"
    validation_messages: list[str] = Field(default_factory=list)
    needs_review: bool = False


class ValidationSummary(BaseModel):
    """Aggregate validation status for one workflow run."""

    total_fields: int
    extracted_count: int
    missing_count: int
    review_count: int
    validation_failures: list[str] = Field(default_factory=list)


class EvaluationSummary(BaseModel):
    """Comparison of extraction results against optional ground truth."""

    total_fields: int
    exact_matches: int
    mismatches: int
    missing_expected: int
    accuracy: float
    coverage: float
    review_rate: float
