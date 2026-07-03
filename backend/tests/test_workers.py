import stat

from app.tools.workers.claude_code import ClaudeCodeWorker
from app.tools.workers.openhands import OpenHandsWorker


def _write_fake_binary(path, echo_text: str) -> str:
    script = path / "fake_binary.sh"
    script.write_text(f"#!/bin/sh\necho '{echo_text}'\nexit 0\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def test_claude_code_worker_reports_missing_binary(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.workers.claude_code.shutil.which", lambda _: None)
    worker = ClaudeCodeWorker()
    result = worker.run_task(prompt="do something", cwd=str(tmp_path))
    assert not result.success
    assert "not found" in result.output
    assert result.backend == "claude_code"


def test_claude_code_worker_runs_when_binary_present(tmp_path, monkeypatch):
    fake = _write_fake_binary(tmp_path, "hello from claude")
    monkeypatch.setattr("app.tools.workers.claude_code.shutil.which", lambda _: fake)
    worker = ClaudeCodeWorker()
    result = worker.run_task(prompt="do something", cwd=str(tmp_path))
    assert result.success
    assert "hello from claude" in result.output


def test_openhands_worker_reports_missing_binary(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.workers.openhands.shutil.which", lambda _: None)
    worker = OpenHandsWorker()
    result = worker.run_task(prompt="do something", cwd=str(tmp_path))
    assert not result.success
    assert "not found" in result.output
    assert result.backend == "openhands"


def test_openhands_worker_runs_when_binary_present(tmp_path, monkeypatch):
    fake = _write_fake_binary(tmp_path, "hello from openhands")
    monkeypatch.setattr("app.tools.workers.openhands.shutil.which", lambda _: fake)
    worker = OpenHandsWorker()
    result = worker.run_task(prompt="do something", cwd=str(tmp_path))
    assert result.success
    assert "hello from openhands" in result.output
