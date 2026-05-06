from doc_extractor.agents import default_agent_roles


def test_default_agent_roles_include_public_workflow_roles():
    roles = {role.id: role for role in default_agent_roles()}

    assert roles["url_extraction"].execution_mode == "llm"
    assert roles["url_ranking"].execution_mode == "tool"
    assert roles["url_verification"].execution_mode == "llm"
    assert roles["inside_out_extraction"].execution_mode == "llm"
    assert roles["outside_in_extraction"].execution_mode == "llm"
    assert roles["deterministic_orchestrator"].execution_mode == "deterministic"
