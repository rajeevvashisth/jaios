"""Specialized nodes for Developer and QA.

Every other agent's node (``build_agent_node`` in ``nodes.py``) produces a
single LLM turn and treats that text as the step's output. Developer and QA
are different: their job is to actually change and verify code, so their
nodes call a real tool after planning — Developer drives a coding worker
(Claude Code/OpenHands), QA runs the real test suite — rather than letting
an LLM's unverified claim ("I fixed it" / "tests pass") stand as the record.
"""

from typing import Any

from app.config import get_settings
from app.db.session import SessionLocal
from app.governance.permissions import invoke_tool_for_agent
from app.orchestration.nodes import plan_with_llm, record_step
from app.orchestration.state import WorkflowState

MAX_QA_RETRIES = 2


def _workspace(state: WorkflowState) -> str:
    return state.get("workspace_path") or get_settings().workspace_root


def build_developer_node():
    """Plan with the LLM, then hand that plan to the configured coding
    worker to actually implement. The worker's success/output is recorded
    alongside the plan — a missing/failed worker still produces a clear,
    truthful step record instead of silently no-opping.
    """

    def node(state: WorkflowState) -> dict[str, Any]:
        db = SessionLocal()
        try:
            plan = plan_with_llm("developer", state)
            tool_result = invoke_tool_for_agent(
                db,
                agent_key="developer",
                tool_key="coding_worker",
                action="run_task",
                workflow_run_id=state["workflow_run_id"],
                prompt=f"{state.get('goal')}\n\nPlan:\n{plan}",
                cwd=_workspace(state),
            )
            output = {
                "response": plan,
                "coding_worker_backend": tool_result.data.get("backend"),
                "coding_worker_success": tool_result.success,
                "coding_worker_output": tool_result.output,
            }
            record_step(db, state, "developer", output)
            return {"context": {"developer": output}}
        finally:
            db.close()

    return node


def build_qa_node():
    """Plan a test approach with the LLM, then actually run pytest in the
    workspace and record the structured pass/fail counts. ``qa_retry_count``
    only increments on a genuine failure, so a clean pass never counts
    against the retry budget ``route_after_qa`` enforces.
    """

    def node(state: WorkflowState) -> dict[str, Any]:
        db = SessionLocal()
        try:
            plan = plan_with_llm("qa", state)
            tool_result = invoke_tool_for_agent(
                db,
                agent_key="qa",
                tool_key="qa_test_runner",
                action="run_pytest",
                workflow_run_id=state["workflow_run_id"],
                cwd=_workspace(state),
            )
            failed = tool_result.data.get("failed", 0) + tool_result.data.get("errors", 0)
            output = {
                "response": plan,
                "tests_passed": tool_result.data.get("passed", 0),
                "tests_failed": failed,
                "test_output": tool_result.output,
            }
            record_step(db, state, "qa", output)

            retry_count = state.get("qa_retry_count", 0)
            return {
                "context": {"qa": output},
                "qa_retry_count": retry_count + 1 if failed else retry_count,
            }
        finally:
            db.close()

    return node


def route_after_qa(state: WorkflowState) -> str:
    """Loop back to Developer on a genuine test failure, up to
    ``MAX_QA_RETRIES`` rounds — after that, proceed to DevOps regardless so
    an unfixable or flaky test can't wedge the workflow forever."""
    qa_output = state.get("context", {}).get("qa", {})
    failed = qa_output.get("tests_failed", 0)
    retry_count = state.get("qa_retry_count", 0)
    if failed and retry_count <= MAX_QA_RETRIES:
        return "developer_rework"
    return "devops"
