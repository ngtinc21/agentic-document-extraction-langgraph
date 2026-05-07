"""Public-safe prompt builders for optional LLM providers."""

from __future__ import annotations

import json
from collections.abc import Sequence

from .schemas import DictionaryEntry, EvidenceRecord, ExtractionResult, SourceDocument


def build_evidence_prompt(entry: DictionaryEntry, documents: Sequence[SourceDocument]) -> str:
    """Build a generic evidence-scout prompt without private examples or methodology."""

    payload = {
        "task": "Find evidence snippets for one dictionary-defined field.",
        "dictionary_entry": entry.model_dump(),
        "documents": [
            {
                "source_id": document.source_id,
                "title": document.title,
                "fiscal_year": document.fiscal_year,
                "content": document.content,
            }
            for document in documents
        ],
        "output_schema": [
            {
                "evidence_id": "field_id:source_id:location",
                "source_id": "source identifier",
                "dictionary_entry_id": entry.id,
                "snippet": "short quote or concise excerpt",
                "location": "page, line, section, or unknown",
                "confidence": "high | medium | low",
                "rationale": "why this evidence supports the field",
            }
        ],
        "rules": [
            "Return JSON only.",
            "Do not infer values during evidence scouting.",
            "Return an empty list when no relevant evidence is present.",
        ],
    }
    return json.dumps(payload, indent=2)


def build_extraction_prompt(
    entry: DictionaryEntry,
    evidence: Sequence[EvidenceRecord],
    previous_result: ExtractionResult | None,
) -> str:
    """Build a generic extraction prompt with validation-feedback support."""

    payload = {
        "task": "Extract one structured value from evidence for a dictionary-defined field.",
        "dictionary_entry": entry.model_dump(),
        "evidence": [item.model_dump() for item in evidence],
        "previous_result": previous_result.model_dump() if previous_result else None,
        "output_schema": {
            "id": entry.id,
            "value": "string, number, boolean, or null",
            "unit": entry.expected_unit,
            "status": "extracted | missing | needs_review | invalid",
            "evidence_id": "evidence id used for the value, or null",
            "confidence": "high | medium | low",
            "validation_messages": [],
            "needs_review": False,
        },
        "rules": [
            "Return JSON only.",
            "Use the requested output schema exactly.",
            "Use null and status=missing when evidence is absent.",
            "Use status=needs_review when evidence is ambiguous.",
            "On retry, address the previous validation messages.",
        ],
    }
    return json.dumps(payload, indent=2)
