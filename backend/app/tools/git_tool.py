import subprocess
from typing import Any

from app.tools.base import Tool, ToolResult

DEFAULT_ALLOWED_SUBCOMMANDS = {
    "status",
    "diff",
    "log",
    "add",
    "commit",
    "branch",
    "checkout",
    "show",
}


class GitTool(Tool):
    """Run a whitelisted git subcommand against a repository directory.

    ``push`` and force-history-rewriting subcommands are intentionally
    excluded from the default allowlist — those are exactly the
    hard-to-reverse, shared-state actions the governance layer requires
    human approval for, so DevOps/Developer agents get read/local-write git
    access here and escalate anything that leaves the local clone.
    """

    key = "git"
    description = "Run a whitelisted git subcommand in a repository directory."

    def __init__(self, repo_dir: str, allowed_subcommands: set[str] | None = None):
        self._repo_dir = repo_dir
        self._allowed = allowed_subcommands or DEFAULT_ALLOWED_SUBCOMMANDS

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "exec":
            return ToolResult(success=False, output=f"Unknown git action: {action}")

        args: list[str] = kwargs["args"]
        if not args:
            return ToolResult(success=False, output="Empty git command")

        subcommand = args[0]
        if subcommand not in self._allowed:
            return ToolResult(
                success=False,
                output=f"git subcommand '{subcommand}' is not in the allowlist",
            )

        proc = subprocess.run(
            ["git", *args],
            cwd=self._repo_dir,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        return ToolResult(
            success=proc.returncode == 0, output=output, data={"returncode": proc.returncode}
        )
