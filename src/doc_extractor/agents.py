"""Clean-room agent role contracts for the public extraction workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .schemas import ExtractionJob, SourceDocument, SourceReference

AgentExecutionMode = Literal["llm", "tool", "deterministic"]


class AgentRole(BaseModel):
    """Public-safe description of one workflow agent or deterministic tool."""

    id: str
    label: str
    execution_mode: AgentExecutionMode
    responsibility: str
    inputs: list[str]
    outputs: list[str]


def default_agent_roles() -> list[AgentRole]:
    """Return the clean-room role map used in docs and interviews."""

    return [
        AgentRole(
            id="deterministic_orchestrator",
            label="Deterministic orchestration agent",
            execution_mode="deterministic",
            responsibility=(
                "Controls LangGraph state, routing, retry budgets, aggregation, "
                "and human review handoff."
            ),
            inputs=["ExtractionJob", "workflow state", "validation summary"],
            outputs=["next node", "aggregate payload", "review queue"],
        ),
        AgentRole(
            id="url_extraction",
            label="URL extraction agent",
            execution_mode="llm",
            responsibility=(
                "Proposes candidate public source URLs that may contain relevant "
                "disclosure evidence for the target entity and dictionary."
            ),
            inputs=["entity metadata", "domain", "dictionary summary"],
            outputs=["candidate source references", "source rationale"],
        ),
        AgentRole(
            id="url_ranking",
            label="URL ranking tool",
            execution_mode="tool",
            responsibility=(
                "Ranks candidate URLs with deterministic signals such as source type, "
                "recency, document relevance, and duplicate handling."
            ),
            inputs=["candidate source references", "ranking configuration"],
            outputs=["ranked source references", "ranking reasons"],
        ),
        AgentRole(
            id="url_verification",
            label="URL verification agent",
            execution_mode="llm",
            responsibility=(
                "Checks whether ranked sources appear relevant, public, and aligned "
                "with the requested entity, period, and extraction domain."
            ),
            inputs=["ranked source references", "entity metadata", "domain"],
            outputs=["verified source references", "verification notes"],
        ),
        AgentRole(
            id="inside_out_extraction",
            label="Inside-out extraction agent",
            execution_mode="llm",
            responsibility=(
                "Extracts dictionary fields from entity-authored or entity-published "
                "documents, with evidence snippets and confidence."
            ),
            inputs=["dictionary entries", "verified entity sources", "validation feedback"],
            outputs=["extraction results", "evidence records"],
        ),
        AgentRole(
            id="outside_in_extraction",
            label="Outside-in extraction agent",
            execution_mode="llm",
            responsibility=(
                "Extracts or corroborates dictionary fields from independent public "
                "sources, with evidence snippets and confidence."
            ),
            inputs=["dictionary entries", "verified external sources", "validation feedback"],
            outputs=["extraction results", "evidence records"],
        ),
    ]


class URLExtractionAgent:
    """Clean-room URL discovery contract with deterministic demo behavior."""

    def propose_sources(self, job: ExtractionJob) -> list[SourceReference]:
        if job.source_references:
            return [
                reference.model_copy(
                    update={
                        "status": "candidate",
                        "rationale": reference.rationale
                        or "Provided as a candidate public source reference.",
                    }
                )
                for reference in job.source_references
            ]

        return [
            SourceReference(
                source_id=document.source_id,
                title=document.title,
                url=f"local://{document.source_id}",
                source_type=document.source_type,
                fiscal_year=document.fiscal_year,
                status="candidate",
                is_entity_authored=True,
                rationale="Derived from local synthetic demo document metadata.",
            )
            for document in job.source_documents
        ]


class URLRankingTool:
    """Deterministic source ranking using generic, public-safe signals."""

    def rank_sources(
        self, job: ExtractionJob, candidates: list[SourceReference]
    ) -> list[SourceReference]:
        ranked: list[SourceReference] = []
        entity_name = job.entity.name.lower()

        for reference in candidates:
            title = reference.title.lower()
            score = 0.0
            reasons: list[str] = []

            if entity_name in title:
                score += 40
                reasons.append("entity_name_match")
            if job.entity.fiscal_year and reference.fiscal_year == job.entity.fiscal_year:
                score += 25
                reasons.append("fiscal_year_match")
            if reference.is_entity_authored:
                score += 15
                reasons.append("entity_authored_source")
            if reference.source_type in {"synthetic_markdown", "annual_report", "policy"}:
                score += 10
                reasons.append("preferred_source_type")
            if reference.url.startswith("local://") or reference.url.startswith("https://"):
                score += 10
                reasons.append("supported_url_scheme")

            ranked.append(
                reference.model_copy(
                    update={
                        "status": "ranked",
                        "ranking_score": score,
                        "rationale": ", ".join(reasons) or "no_positive_ranking_signals",
                    }
                )
            )

        return sorted(ranked, key=lambda item: item.ranking_score, reverse=True)


class URLVerificationAgent:
    """Clean-room source verification contract with deterministic demo behavior."""

    def verify_sources(
        self, job: ExtractionJob, ranked_sources: list[SourceReference]
    ) -> list[SourceReference]:
        verified: list[SourceReference] = []
        document_ids = {document.source_id for document in job.source_documents}

        for reference in ranked_sources:
            has_matching_document = reference.source_id in document_ids
            has_relevance_signal = reference.ranking_score >= 35
            is_verified = has_matching_document and has_relevance_signal
            verified.append(
                reference.model_copy(
                    update={
                        "status": "verified" if is_verified else "rejected",
                        "confidence": "high" if is_verified else "low",
                        "rationale": (
                            f"{reference.rationale}, verified_against_demo_document"
                            if is_verified
                            else f"{reference.rationale}, rejected_by_public_safe_checks"
                        ),
                    }
                )
            )

        return verified


class InsideOutExtractionAgent:
    """Classify entity-authored sources for inside-out extraction."""

    def select_documents(
        self,
        documents: list[SourceDocument],
        verified_sources: list[SourceReference],
    ) -> list[SourceDocument]:
        inside_out_ids = {
            source.source_id
            for source in verified_sources
            if source.status == "verified" and source.is_entity_authored
        }
        if not verified_sources:
            return documents
        return [document for document in documents if document.source_id in inside_out_ids]


class OutsideInExtractionAgent:
    """Classify independent sources for outside-in extraction."""

    def select_documents(
        self,
        documents: list[SourceDocument],
        verified_sources: list[SourceReference],
    ) -> list[SourceDocument]:
        outside_in_ids = {
            source.source_id
            for source in verified_sources
            if source.status == "verified" and not source.is_entity_authored
        }
        return [document for document in documents if document.source_id in outside_in_ids]
