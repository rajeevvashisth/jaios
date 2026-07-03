from typing import Any

from app.tools.base import Tool, ToolResult
from app.tools.workers.base import CodingWorker
from app.tools.workers.claude_code import ClaudeCodeWorker
from app.tools.workers.openhands import OpenHandsWorker

_BACKENDS: dict[str, type[CodingWorker]] = {
    "claude_code": ClaudeCodeWorker,
    "openhands": OpenHandsWorker,
}


class CodingWorkerTool(Tool):
    """Routes a coding task to whichever worker backend is configured.

    The Developer agent calls this one tool key regardless of which
    underlying system executes the task — swapping backends is a
    ``CODING_WORKER_BACKEND`` config change, not an agent/graph code change.
    """

    key = "coding_worker"
    description = "Drive a coding worker (Claude Code or OpenHands) to implement a task."

    def __init__(self, backend: str = "claude_code"):
        if backend not in _BACKENDS:
            raise ValueError(f"Unknown coding worker backend: {backend}")
        self._worker: CodingWorker = _BACKENDS[backend]()

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "run_task":
            return ToolResult(success=False, output=f"Unknown coding worker action: {action}")

        result = self._worker.run_task(prompt=kwargs["prompt"], cwd=kwargs["cwd"])
        return ToolResult(
            success=result.success, output=result.output, data={"backend": result.backend}
        )
