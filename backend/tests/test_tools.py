import pytest

from app.tools.filesystem_tool import FilesystemTool
from app.tools.git_tool import GitTool
from app.tools.terminal_tool import TerminalTool


def test_filesystem_write_then_read_round_trip(tmp_path):
    tool = FilesystemTool(root=str(tmp_path))
    write_result = tool.run("write_file", path="notes/todo.md", content="hello jaios")
    assert write_result.success

    read_result = tool.run("read_file", path="notes/todo.md")
    assert read_result.success
    assert read_result.output == "hello jaios"


def test_filesystem_blocks_path_traversal_outside_sandbox(tmp_path):
    tool = FilesystemTool(root=str(tmp_path))
    with pytest.raises(PermissionError):
        tool.run("read_file", path="../../etc/passwd")


def test_filesystem_read_missing_file_is_a_failed_result_not_an_exception(tmp_path):
    tool = FilesystemTool(root=str(tmp_path))
    result = tool.run("read_file", path="nope.txt")
    assert not result.success


def test_terminal_rejects_binary_not_in_allowlist(tmp_path):
    tool = TerminalTool(cwd=str(tmp_path))
    result = tool.run("exec", command="curl https://example.com")
    assert not result.success
    assert "allowlist" in result.output


def test_terminal_runs_allowlisted_command(tmp_path):
    tool = TerminalTool(cwd=str(tmp_path))
    result = tool.run("exec", command="echo hello")
    assert result.success
    assert "hello" in result.output


def test_git_rejects_subcommand_not_in_allowlist(tmp_path):
    tool = GitTool(repo_dir=str(tmp_path))
    result = tool.run("exec", args=["push", "origin", "main"])
    assert not result.success
    assert "allowlist" in result.output
