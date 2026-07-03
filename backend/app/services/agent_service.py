from sqlalchemy.orm import Session

from app.agents.registry import agent_registry
from app.models.agent import AgentDefinition
from app.schemas.agent import AgentSpecRead


def sync_agent_definitions(db: Session) -> None:
    """Ensure every agent in the code registry has a runtime row in
    ``agent_definitions``. Idempotent — safe to call on every app startup so
    a newly added AgentSpec shows up without a manual migration."""
    existing_keys = {row.agent_key for row in db.query(AgentDefinition.agent_key).all()}
    for spec in agent_registry.list_specs():
        if spec.key not in existing_keys:
            db.add(AgentDefinition(agent_key=spec.key, name=spec.name, layer=spec.layer.value))
    db.commit()


def list_agents_with_runtime_state(db: Session) -> list[AgentSpecRead]:
    runtime_by_key = {row.agent_key: row for row in db.query(AgentDefinition).all()}
    results = []
    for spec in agent_registry.list_specs():
        runtime = runtime_by_key.get(spec.key)
        results.append(
            AgentSpecRead(
                key=spec.key,
                name=spec.name,
                layer=spec.layer.value,
                responsibility=spec.responsibility,
                allowed_tools=spec.allowed_tools,
                memory_scope=spec.memory_scope.value,
                can_delegate_to=spec.can_delegate_to,
                requires_approval_for=spec.requires_approval_for,
                escalates_to=spec.escalates_to,
                enabled=runtime.enabled if runtime else True,
                last_active_at=runtime.last_active_at if runtime else None,
            )
        )
    return results
