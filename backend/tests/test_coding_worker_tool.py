import pytest

from app.tools.coding_worker_tool import CodingWorkerTool


def test_unknown_backend_raises_at_construction():
    with pytest.raises(ValueError):
        CodingWorkerTool(backend="not-a-real-backend")


def test_unknown_action_fails_without_touching_worker(tmp_path):
    tool = CodingWorkerTool(backend="claude_code")
    result = tool.run("not_run_task", prompt="x", cwd=str(tmp_path))
    assert not result.success
    assert "Unknown coding worker action" in result.output


def test_run_task_reports_missing_binary_gracefully(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.workers.claude_code.shutil.which", lambda _: None)
    tool = CodingWorkerTool(backend="claude_code")
    result = tool.run("run_task", prompt="implement the feature", cwd=str(tmp_path))
    assert not result.success
    assert result.data["backend"] == "claude_code"
