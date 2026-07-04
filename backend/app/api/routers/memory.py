from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.memory.store import list_memory, write_memory
from app.models.product import Product
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.memory import MemoryRecordCreate, MemoryRecordRead

router = APIRouter(prefix="/memory", tags=["memory"])


def _check_scope_ownership(db: Session, current_user: User, scope_type: str, scope_id: str) -> None:
    """Verify the (scope_type, scope_id) a memory record is being read/written
    for actually belongs to the caller's company. ``agent`` scope has no
    company concept — the agent registry is global/shared, not tenant data —
    so it's left unchecked for any authenticated user."""
    owner_company_id: str | None
    if scope_type == "company":
        owner_company_id = scope_id
    elif scope_type == "product":
        product = db.get(Product, scope_id)
        owner_company_id = product.company_id if product else None
    elif scope_type == "project":
        project = db.get(Project, scope_id)
        owner_company_id = project.company_id if project else None
    elif scope_type == "task":
        task = db.get(Task, scope_id)
        owner_company_id = task.company_id if task else None
    else:
        return

    if owner_company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Scope not found")


@router.post("", response_model=MemoryRecordRead)
def create_memory_record(
    payload: MemoryRecordCreate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
):
    _check_scope_ownership(db, current_user, payload.scope_type.value, payload.scope_id)
    return write_memory(
        db,
        scope_type=payload.scope_type.value,
        scope_id=payload.scope_id,
        content=payload.content,
        kind=payload.kind.value,
        agent_key=payload.agent_key,
        expires_at=payload.expires_at,
    )


@router.get("", response_model=list[MemoryRecordRead])
def get_memory_records(
    scope_type: str,
    scope_id: str,
    agent_key: str | None = None,
    kind: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_scope_ownership(db, current_user, scope_type, scope_id)
    return list_memory(
        db, scope_type=scope_type, scope_id=scope_id, agent_key=agent_key, kind=kind, limit=limit
    )
