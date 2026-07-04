from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.agent import AgentDefinition
from app.models.user import User
from app.schemas.agent import AgentDefinitionUpdate, AgentSpecRead
from app.services.agent_service import list_agents_with_runtime_state

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentSpecRead])
def list_agents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AgentSpecRead]:
    return list_agents_with_runtime_state(db)


@router.patch("/{agent_key}", response_model=AgentSpecRead)
def update_agent_runtime_state(
    agent_key: str,
    payload: AgentDefinitionUpdate,
    # The agent registry is global (shared across every company on this
    # JAIOS instance), not per-tenant data — so there's no company to check
    # ownership against. Restricting to admin is the floor for a mutation
    # with that blast radius.
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AgentSpecRead:
    runtime = db.get(AgentDefinition, agent_key)
    if runtime is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(runtime, field, value)
    db.commit()
    return next(a for a in list_agents_with_runtime_state(db) if a.key == agent_key)
