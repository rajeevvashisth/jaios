import re
import subprocess
import sys
from typing import Any

from app.tools.base import Tool, ToolResult

_NO_TESTS_RE = re.compile(r"no tests ran", re.IGNORECASE)
_PASSED_RE = re.compile(r"(\d+) passed")
_FAILED_RE = re.compile(r"(\d+) failed")
_ERROR_RE = re.compile(r"(\d+) error")


class QATestRunnerTool(Tool):
    """Runs pytest in a workspace and parses structured pass/fail counts out
    of its summary line — real quality-gate evidence a QA workflow can key
    decisions off of, rather than an LLM's unverified claim that tests pass.
    """

    key = "qa_test_runner"
    description = "Run the project's pytest suite and report structured pass/fail counts."

    def __init__(self, timeout_seconds: int = 120):
        self._timeout = timeout_seconds

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "run_pytest":
            return ToolResult(success=False, output=f"Unknown QA action: {action}")

        cwd = kwargs["cwd"]
        args = kwargs.get("args", ["-q"])

        try:
            # Use the interpreter running this process (not a bare "python3"
            # off PATH) so pytest resolution is unambiguous regardless of
            # how many Python installs are on the host.
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=f"pytest timed out after {self._timeout}s",
                data={"passed": 0, "failed": 0, "errors": 1},
            )

        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        passed, failed, errors = self._parse_summary(output)
        return ToolResult(
            success=failed == 0 and errors == 0,
            output=output,
            data={"passed": passed, "failed": failed, "errors": errors},
        )

    @staticmethod
    def _parse_summary(output: str) -> tuple[int, int, int]:
        if _NO_TESTS_RE.search(output):
            return 0, 0, 0

        passed_match = _PASSED_RE.search(output)
        failed_match = _FAILED_RE.search(output)
        error_match = _ERROR_RE.search(output)
        return (
            int(passed_match.group(1)) if passed_match else 0,
            int(failed_match.group(1)) if failed_match else 0,
            int(error_match.group(1)) if error_match else 0,
        )
