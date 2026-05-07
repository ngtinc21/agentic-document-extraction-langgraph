from pathlib import Path

from doc_extractor.agents import (
    URLExtractionAgent,
    URLRankingTool,
    URLVerificationAgent,
    default_agent_roles,
)
from doc_extractor.io import load_job_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_default_agent_roles_include_public_workflow_roles():
    roles = {role.id: role for role in default_agent_roles()}

    assert roles["url_extraction"].execution_mode == "llm"
    assert roles["url_ranking"].execution_mode == "tool"
    assert roles["url_verification"].execution_mode == "llm"
    assert roles["inside_out_extraction"].execution_mode == "llm"
    assert roles["outside_in_extraction"].execution_mode == "llm"
    assert roles["deterministic_orchestrator"].execution_mode == "deterministic"


def test_source_agents_rank_and_verify_synthetic_sources():
    job, _ = load_job_file(PROJECT_ROOT / "domains" / "procurement" / "job.json")

    candidates = URLExtractionAgent().propose_sources(job)
    ranked = URLRankingTool().rank_sources(job, candidates)
    verified = URLVerificationAgent().verify_sources(job, ranked)

    assert ranked[0].source_id == "northwind_onboarding_2025"
    assert {item.source_id for item in verified if item.status == "verified"} == {
        "northwind_onboarding_2025",
        "northwind_insurance_2025",
        "northwind_security_2025",
    }
    assert "unrelated_supplier_news_2025" in {
        item.source_id for item in verified if item.status == "rejected"
    }
