import pytest

from app.agents.registry import agent_registry

EXPECTED_KEYS = {"ceo", "cto", "developer", "devops", "qa", "finance", "legal", "operations"}


def test_registry_has_exactly_the_8_core_agents():
    assert {spec.key for spec in agent_registry.list_specs()} == EXPECTED_KEYS


def test_each_agent_has_a_system_prompt_and_responsibility():
    for spec in agent_registry.list_specs():
        assert spec.system_prompt.strip()
        assert spec.responsibility.strip()


def test_get_unknown_agent_raises():
    with pytest.raises(KeyError):
        agent_registry.get("not-a-real-agent")


def test_cto_can_delegate_to_developer_devops_qa():
    assert agent_registry.can_delegate("cto", "developer")
    assert agent_registry.can_delegate("cto", "devops")
    assert agent_registry.can_delegate("cto", "qa")
    assert not agent_registry.can_delegate("cto", "finance")


def test_devops_requires_approval_for_deploy():
    devops = agent_registry.get("devops")
    assert "deploy" in devops.requires_approval_for


def test_finance_and_legal_escalate_to_ceo():
    assert agent_registry.get("finance").escalates_to == "ceo"
    assert agent_registry.get("legal").escalates_to == "ceo"


def test_tools_for_developer_includes_filesystem_and_git():
    tools = set(agent_registry.tools_for("developer"))
    assert {"filesystem", "git", "terminal"} <= tools


def test_developer_has_coding_worker_and_github_tools():
    tools = set(agent_registry.tools_for("developer"))
    assert {"coding_worker", "github"} <= tools


def test_developer_requires_approval_for_github_pr_create():
    developer = agent_registry.get("developer")
    assert "github_pr_create" in developer.requires_approval_for


def test_qa_has_test_runner_tool():
    assert "qa_test_runner" in agent_registry.tools_for("qa")


def test_devops_has_github_tool():
    assert "github" in agent_registry.tools_for("devops")
