"""LLM provider abstractions.

The fake provider is deterministic and powers tests/CI. Optional providers can
implement the same interface without changing the LangGraph workflow.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from .schemas import DictionaryEntry, EvidenceRecord, ExtractionResult, SourceDocument


class BaseLLMProvider(ABC):
    """Provider interface used by workflow nodes."""

    @abstractmethod
    def scout_evidence(
        self, entry: DictionaryEntry, documents: Sequence[SourceDocument]
    ) -> list[EvidenceRecord]:
        """Return candidate evidence snippets for one dictionary entry."""

    @abstractmethod
    def extract_value(
        self, entry: DictionaryEntry, evidence: Sequence[EvidenceRecord]
    ) -> ExtractionResult:
        """Extract a structured value from evidence for one dictionary entry."""


class FakeLLMProvider(BaseLLMProvider):
    """Deterministic provider for portfolio demos and CI."""

    def scout_evidence(
        self, entry: DictionaryEntry, documents: Sequence[SourceDocument]
    ) -> list[EvidenceRecord]:
        keywords = entry.evidence_rules.keywords or [entry.label]
        normalized_keywords = [keyword.lower() for keyword in keywords]
        evidence: list[EvidenceRecord] = []

        for document in documents:
            content = document.content or ""
            for line_number, line in enumerate(content.splitlines(), start=1):
                normalized_line = line.lower()
                if any(keyword in normalized_line for keyword in normalized_keywords):
                    evidence.append(
                        EvidenceRecord(
                            evidence_id=f"{entry.id}:{document.source_id}:{line_number}",
                            source_id=document.source_id,
                            dictionary_entry_id=entry.id,
                            snippet=line.strip(),
                            location=f"line {line_number}",
                            confidence="high",
                            rationale="Matched dictionary keyword in source text.",
                        )
                    )
                    break
        return evidence

    def extract_value(
        self, entry: DictionaryEntry, evidence: Sequence[EvidenceRecord]
    ) -> ExtractionResult:
        if not evidence:
            return ExtractionResult(
                id=entry.id,
                value=None,
                unit=entry.expected_unit,
                status="missing",
                confidence="low",
                validation_messages=["no_evidence_found"],
                needs_review=True,
            )

        selected = evidence[0]
        value = self._extract_by_type(entry, selected.snippet)
        if value is None:
            return ExtractionResult(
                id=entry.id,
                value=None,
                unit=entry.expected_unit,
                status="needs_review",
                evidence_id=selected.evidence_id,
                confidence="medium",
                validation_messages=["evidence_found_but_value_not_parsed"],
                needs_review=True,
            )

        return ExtractionResult(
            id=entry.id,
            value=value,
            unit=entry.expected_unit,
            status="extracted",
            evidence_id=selected.evidence_id,
            confidence=selected.confidence,
        )

    def _extract_by_type(self, entry: DictionaryEntry, snippet: str) -> str | bool | None:
        value_segment = snippet.split(":", 1)[1] if ":" in snippet else snippet
        if entry.expected_type == "boolean":
            return self._extract_boolean(entry, snippet)
        if entry.expected_type == "string":
            if ":" in snippet:
                return snippet.split(":", 1)[1].strip().rstrip(".")
            return snippet.strip().rstrip(".")
        if entry.expected_type == "percentage":
            match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", value_segment)
            return match.group(1) if match else None
        if entry.expected_type == "number":
            match = re.search(r"(-?\d[\d,]*(?:\.\d+)?)", value_segment)
            return match.group(1).replace(",", "") if match else None
        return None

    def _extract_boolean(self, entry: DictionaryEntry, snippet: str) -> bool | None:
        normalized = snippet.lower()
        negative_label = any(token in entry.label.lower() for token in ("no ", "not ", "none"))
        if negative_label and any(token in normalized for token in ("no ", "none", "not ")):
            return True
        positive_tokens = ("maintains", "has ", "met ", "published", "covered")
        if any(token in normalized for token in positive_tokens):
            return True
        if any(token in normalized for token in ("does not", "no evidence", "not available")):
            return False
        return None


class GeminiProvider(BaseLLMProvider):
    """Optional Gemini provider placeholder using environment-only configuration."""

    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        model = os.getenv("DOC_EXTRACTOR_GEMINI_MODEL", "gemini-2.5-flash")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is required when DOC_EXTRACTOR_PROVIDER=gemini")
        try:
            from google import genai  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install the 'gemini' extra to use GeminiProvider") from exc
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def scout_evidence(
        self, entry: DictionaryEntry, documents: Sequence[SourceDocument]
    ) -> list[EvidenceRecord]:
        # Keep the public MVP deterministic by using the fake search strategy for
        # evidence selection. Provider-specific generation can be added behind
        # this interface without changing workflow state or schemas.
        return FakeLLMProvider().scout_evidence(entry, documents)

    def extract_value(
        self, entry: DictionaryEntry, evidence: Sequence[EvidenceRecord]
    ) -> ExtractionResult:
        return FakeLLMProvider().extract_value(entry, evidence)


def build_provider(name: str) -> BaseLLMProvider:
    provider_name = (name or os.getenv("DOC_EXTRACTOR_PROVIDER") or "fake").lower()
    if provider_name == "fake":
        return FakeLLMProvider()
    if provider_name == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unsupported provider: {name}")
