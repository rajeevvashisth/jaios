"""Deterministic keyword-based task router.

Maps a task's title/description to the best-fit agent by scoring keyword
overlap against each agent's domain vocabulary. Deliberately rule-based
rather than an LLM call — routing needs to be instant, free, deterministic,
and unit-testable; swap in an LLM classifier later behind the same
``suggest_agent_for_task`` signature if keyword matching proves too coarse
for real task volume.
"""

from sqlalchemy.orm import Session

from app.models.task import Task

_AGENT_KEYWORDS: dict[str, list[str]] = {
    "devops": [
        "deploy",
        "infra",
        "infrastructure",
        "docker",
        "ci/cd",
        "pipeline",
        "release",
        "environment",
        "outage",
        "incident",
        "monitoring",
        "server",
    ],
    "qa": ["test", "regression", "bug", "qa", "quality", "verify", "flaky"],
    "developer": [
        "implement",
        "build",
        "feature",
        "code",
        "fix",
        "refactor",
        "api",
        "frontend",
        "backend",
        "endpoint",
    ],
    "legal": [
        "contract",
        "trademark",
        "compliance",
        "legal",
        "nda",
        "agreement",
        "policy",
        "signature",
    ],
    "finance": [
        "invoice",
        "expense",
        "revenue",
        "budget",
        "payment",
        "cost",
        "billing",
        "runway",
        "gst",
        "tax",
    ],
    "operations": ["follow-up", "followup", "meeting", "action item", "checklist"],
    "cto": ["architecture", "technical plan", "engineering plan", "tech stack"],
    "ceo": ["strategy", "prioritize", "priority", "roadmap", "investment", "okr"],
}

DEFAULT_AGENT_KEY = "operations"


def suggest_agent_for_task(task: Task) -> str:
    """Return the agent key with the highest keyword-overlap score against
    the task's title + description. Falls back to Operations (the
    cross-functional catch-all) when nothing scores above zero."""
    text = f"{task.title} {task.description or ''}".lower()

    best_key = DEFAULT_AGENT_KEY
    best_score = 0
    for agent_key, keywords in _AGENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_key = agent_key
    return best_key


def route_task(db: Session, task: Task) -> Task:
    task.assignee_agent_key = suggest_agent_for_task(task)
    db.commit()
    db.refresh(task)
    return task
