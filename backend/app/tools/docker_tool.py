import subprocess
from typing import Any

from app.tools.base import Tool, ToolResult

DEFAULT_ALLOWED_SUBCOMMANDS = {"ps", "logs", "build", "compose", "images", "inspect"}


class DockerTool(Tool):
    """Run a whitelisted docker/docker-compose subcommand.

    ``rm``/``system prune``/volume-deleting subcommands are excluded from
    the default allowlist — destructive infra actions belong behind the
    approval layer (``requires_approval_for=["deploy"]`` on the DevOps
    agent), not available to call directly.
    """

    key = "docker"
    description = "Run a whitelisted docker/docker-compose subcommand."

    def __init__(self, cwd: str, allowed_subcommands: set[str] | None = None):
        self._cwd = cwd
        self._allowed = allowed_subcommands or DEFAULT_ALLOWED_SUBCOMMANDS

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "exec":
            return ToolResult(success=False, output=f"Unknown docker action: {action}")

        args: list[str] = kwargs["args"]
        if not args:
            return ToolResult(success=False, output="Empty docker command")

        subcommand = args[0]
        if subcommand not in self._allowed:
            return ToolResult(
                success=False,
                output=f"docker subcommand '{subcommand}' is not in the allowlist",
            )

        proc = subprocess.run(
            ["docker", *args],
            cwd=self._cwd,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        return ToolResult(
            success=proc.returncode == 0, output=output, data={"returncode": proc.returncode}
        )
