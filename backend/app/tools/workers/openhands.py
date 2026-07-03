import shutil
import subprocess

from app.tools.workers.base import CodingWorker, CodingWorkerResult


class OpenHandsWorker(CodingWorker):
    """Drives OpenHands' headless CLI mode, when installed.

    The second pluggable coding worker per the spec ("Developer Agent can
    use Claude Code and/or OpenHands") — same defensive pattern as
    ``ClaudeCodeWorker``: a missing binary is a failed result, not a crash.
    OpenHands' headless entrypoint and flags have changed across releases;
    treat the command below as a documented starting point and adjust to
    match whatever version is installed.
    """

    backend_name = "openhands"

    def __init__(self, timeout_seconds: int = 300):
        self._timeout = timeout_seconds

    def run_task(self, prompt: str, cwd: str) -> CodingWorkerResult:
        binary = shutil.which("openhands")
        if binary is None:
            return CodingWorkerResult(
                success=False,
                output="`openhands` CLI not found on PATH — install OpenHands to enable this.",
                backend=self.backend_name,
            )

        try:
            proc = subprocess.run(
                [binary, "run", "--task", prompt],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return CodingWorkerResult(
                success=False,
                output=f"OpenHands timed out after {self._timeout}s",
                backend=self.backend_name,
            )

        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        return CodingWorkerResult(
            success=proc.returncode == 0, output=output, backend=self.backend_name
        )
