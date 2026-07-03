import pytest

from app.governance.approvals import action_requires_approval
from app.governance.permissions import (
    ToolPermissionError,
    check_tool_permission,
    invoke_tool_for_agent,
)
from app.models.audit import AuditLogEntry


def test_check_tool_permission_allows_permitted_tool():
    check_tool_permission("developer", "filesystem")  # should not raise


def test_check_tool_permission_denies_unpermitted_tool():
    with pytest.raises(ToolPermissionError):
        check_tool_permission("finance", "terminal")


def test_devops_deploy_requires_approval():
    assert action_requires_approval("devops", "deploy")


def test_developer_normal_action_does_not_require_approval():
    assert not action_requires_approval("developer", "write_code")


def test_invoke_tool_for_agent_denies_and_does_not_call_tool():
    from app.core.metrics import tool_calls_total

    before = tool_calls_total.labels(tool_key="terminal", outcome="denied")._value.get()

    with pytest.raises(ToolPermissionError):
        invoke_tool_for_agent(
            db=None,  # never reached — permission check raises first
            agent_key="finance",
            tool_key="terminal",
            action="exec",
            command="echo hi",
        )

    after = tool_calls_total.labels(tool_key="terminal", outcome="denied")._value.get()
    assert after == before + 1


def test_invoke_tool_for_agent_writes_audit_log(db_session, tmp_path, monkeypatch):
    from app.tools import registry as tool_registry_module
    from app.tools.filesystem_tool import FilesystemTool

    monkeypatch.setitem(
        tool_registry_module.tool_registry._tools, "filesystem", FilesystemTool(root=str(tmp_path))
    )

    result = invoke_tool_for_agent(
        db=db_session,
        agent_key="developer",
        tool_key="filesystem",
        action="write_file",
        path="a.txt",
        content="hi",
    )
    assert result.success

    entries = db_session.query(AuditLogEntry).filter(AuditLogEntry.actor_key == "developer").all()
    assert len(entries) == 1
    assert entries[0].tool_used == "filesystem"
