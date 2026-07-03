import stat

from app.tools.github_tool import GitHubTool


def test_rejects_subcommand_not_in_allowlist(tmp_path):
    tool = GitHubTool(cwd=str(tmp_path))
    result = tool.run("exec", args=["repo", "delete"])
    assert not result.success
    assert "allowlist" in result.output


def test_rejects_too_few_args(tmp_path):
    tool = GitHubTool(cwd=str(tmp_path))
    result = tool.run("exec", args=["pr"])
    assert not result.success


def test_reports_missing_gh_binary(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.github_tool.shutil.which", lambda _: None)
    tool = GitHubTool(cwd=str(tmp_path))
    result = tool.run("exec", args=["pr", "list"])
    assert not result.success
    assert "not found" in result.output


def test_allows_read_subcommand_when_gh_present(tmp_path, monkeypatch):
    fake_gh = tmp_path / "fake_gh.sh"
    fake_gh.write_text("#!/bin/sh\necho 'PR #1: fix bug'\nexit 0\n")
    fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr("app.tools.github_tool.shutil.which", lambda _: str(fake_gh))

    tool = GitHubTool(cwd=str(tmp_path))
    result = tool.run("exec", args=["pr", "list"])
    assert result.success
    assert "PR #1" in result.output


def test_allows_write_subcommand_at_tool_level(tmp_path, monkeypatch):
    """The tool enforces the allowlist only — approval gating for write
    actions like `pr create` happens at the orchestration node level (same
    pattern as DevOps' deploy checkpoint), not inside the tool itself."""
    fake_gh = tmp_path / "fake_gh.sh"
    fake_gh.write_text("#!/bin/sh\necho 'created PR #2'\nexit 0\n")
    fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr("app.tools.github_tool.shutil.which", lambda _: str(fake_gh))

    tool = GitHubTool(cwd=str(tmp_path))
    result = tool.run("exec", args=["pr", "create", "--title", "x"])
    assert result.success
