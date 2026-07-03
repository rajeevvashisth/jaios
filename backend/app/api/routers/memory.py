from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.memory.store import list_memory, write_memory
from app.schemas.memory import MemoryRecordCreate, MemoryRecordRead

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryRecordRead)
def create_memory_record(payload: MemoryRecordCreate, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db),
):
    return list_memory(
        db, scope_type=scope_type, scope_id=scope_id, agent_key=agent_key, kind=kind, limit=limit
    )
