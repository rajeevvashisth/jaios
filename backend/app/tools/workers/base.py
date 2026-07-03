from abc import ABC, abstractmethod

from pydantic import BaseModel


class CodingWorkerResult(BaseModel):
    success: bool
    output: str
    backend: str


class CodingWorker(ABC):
    """A worker system the Developer agent drives to actually write code.

    LangGraph orchestrates; this is where execution happens. Swap the
    backend (Claude Code today, OpenHands or a future remote sandbox later)
    without touching the Developer node's logic — it only ever calls
    ``run_task`` through the ``coding_worker`` tool.
    """

    backend_name: str

    @abstractmethod
    def run_task(self, prompt: str, cwd: str) -> CodingWorkerResult: ...
