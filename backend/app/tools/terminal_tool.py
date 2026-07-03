import shlex
import subprocess
from typing import Any

from app.tools.base import Tool, ToolResult

DEFAULT_ALLOWED_BINARIES = {
    "ls",
    "cat",
    "grep",
    "find",
    "pytest",
    "python",
    "python3",
    "pip",
    "npm",
    "npx",
    "node",
    "ruff",
    "black",
    "mypy",
    "echo",
    "wc",
}


class TerminalTool(Tool):
    """Run a whitelisted shell command in a sandboxed working directory.

    Only the first token (the binary) is checked against
    ``allowed_binaries`` — this is a coarse guardrail suited to Phase 1
    (agents running trusted, known workflows locally), not a full sandbox.
    Shell metacharacters are not interpreted since we use ``shell=False``
    with a parsed argv, which blocks the common command-injection vector of
    string-concatenated shell commands.
    """

    key = "terminal"
    description = "Execute a whitelisted command in the sandboxed workspace."

    def __init__(
        self, cwd: str, allowed_binaries: set[str] | None = None, timeout_seconds: int = 60
    ):
        self._cwd = cwd
        self._allowed = allowed_binaries or DEFAULT_ALLOWED_BINARIES
        self._timeout = timeout_seconds

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "exec":
            return ToolResult(success=False, output=f"Unknown terminal action: {action}")

        command = kwargs["command"]
        argv = shlex.split(command)
        if not argv:
            return ToolResult(success=False, output="Empty command")

        binary = argv[0]
        if binary not in self._allowed:
            return ToolResult(
                success=False,
                output=f"Binary '{binary}' is not in the terminal tool's allowlist",
            )

        try:
            proc = subprocess.run(
                argv,
                cwd=self._cwd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output=f"Command timed out after {self._timeout}s")

        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        return ToolResult(
            success=proc.returncode == 0, output=output, data={"returncode": proc.returncode}
        )
