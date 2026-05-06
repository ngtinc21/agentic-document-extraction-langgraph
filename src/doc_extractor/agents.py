"""Clean-room agent role contracts for the public extraction workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

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
