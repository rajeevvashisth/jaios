import shutil
import subprocess

from app.tools.workers.base import CodingWorker, CodingWorkerResult


class ClaudeCodeWorker(CodingWorker):
    """Drives the Claude Code CLI in non-interactive ("print") mode.

    A thin wrapper, not a reimplementation — Claude Code's own permission
    and sandboxing model applies to whatever it does in ``cwd``. Requires
    the `claude` binary on PATH; a missing binary returns a failed result
    rather than raising, so a machine without Claude Code installed doesn't
    crash the workflow, it just reports the Developer step as unavailable.
    """

    backend_name = "claude_code"

    def __init__(self, timeout_seconds: int = 300):
        self._timeout = timeout_seconds

    def run_task(self, prompt: str, cwd: str) -> CodingWorkerResult:
        binary = shutil.which("claude")
        if binary is None:
            return CodingWorkerResult(
                success=False,
                output="`claude` CLI not found on PATH — install Claude Code to enable this.",
                backend=self.backend_name,
            )

        try:
            proc = subprocess.run(
                [binary, "-p", prompt, "--output-format", "text"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return CodingWorkerResult(
                success=False,
                output=f"Claude Code timed out after {self._timeout}s",
                backend=self.backend_name,
            )

        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        return CodingWorkerResult(
            success=proc.returncode == 0, output=output, backend=self.backend_name
        )
