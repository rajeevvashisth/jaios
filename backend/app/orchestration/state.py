from typing import Annotated, Any, TypedDict


def merge_dicts(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Reducer for ``context``: shallow-merge each node's output in rather
    than overwrite, so agent A's entry survives when agent B's node runs."""
    merged = dict(current)
    merged.update(update)
    return merged


class WorkflowState(TypedDict, total=False):
    """Shared state threaded through every node in a workflow graph.

    ``context`` accumulates each agent's output keyed by ``agent_key`` so
    downstream agents (and the final consolidation step) can read what came
    before them without re-querying the database.
    """

    company_id: str
    workflow_run_id: str
    originating_task_id: str | None
    goal: str
    workspace_path: str | None
    context: Annotated[dict[str, Any], merge_dicts]
    qa_retry_count: int
    status: str
