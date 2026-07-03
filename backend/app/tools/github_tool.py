import shutil
import subprocess
from typing import Any

from app.tools.base import Tool, ToolResult

READ_ONLY_SUBCOMMANDS = {
    ("pr", "list"),
    ("pr", "view"),
    ("pr", "diff"),
    ("pr", "checks"),
    ("issue", "list"),
    ("issue", "view"),
    ("repo", "view"),
}
WRITE_SUBCOMMANDS = {
    ("pr", "create"),
    ("pr", "comment"),
    ("pr", "merge"),
    ("issue", "create"),
    ("issue", "comment"),
}
ALL_ALLOWED = READ_ONLY_SUBCOMMANDS | WRITE_SUBCOMMANDS


class GitHubTool(Tool):
    """Wraps the `gh` CLI for PR/issue visibility and write actions.

    This tool only enforces the subcommand allowlist above — read vs. write
    is a distinction the *workflow* is responsible for acting on via
    ``AgentSpec.requires_approval_for`` (e.g. "github_pr_create"), the same
    pattern as DevOps' "deploy" checkpoint. That enforcement happens in a
    dedicated graph node that pauses for approval *before* calling this
    tool — no graph currently wires a PR-creation node, so today the write
    subcommands are reachable but not yet approval-gated end-to-end; treat
    the allowlist here as a floor, not a substitute for that node-level gate.

    Requires the `gh` CLI to be installed and authenticated; a missing
    binary returns a failed result rather than raising.
    """

    key = "github"
    description = "Run a whitelisted `gh` (GitHub CLI) subcommand."

    def __init__(self, cwd: str, timeout_seconds: int = 60):
        self._cwd = cwd
        self._timeout = timeout_seconds

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "exec":
            return ToolResult(success=False, output=f"Unknown github action: {action}")

        args: list[str] = kwargs["args"]
        if len(args) < 2 or (args[0], args[1]) not in ALL_ALLOWED:
            return ToolResult(
                success=False,
                output=f"gh subcommand {' '.join(args[:2])!r} is not in the allowlist",
            )

        binary = shutil.which("gh")
        if binary is None:
            return ToolResult(success=False, output="`gh` CLI not found on PATH")

        try:
            proc = subprocess.run(
                [binary, *args],
                cwd=self._cwd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output=f"gh command timed out after {self._timeout}s")

        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        return ToolResult(
            success=proc.returncode == 0, output=output, data={"returncode": proc.returncode}
        )
