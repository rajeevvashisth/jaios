from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_workspace_id, get_db, require_role
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceRead, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/me", response_model=WorkspaceRead)
def get_my_workspace(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Workspace:
    workspace_id = get_current_workspace_id(db, current_user)
    workspace = db.get(Workspace, workspace_id) if workspace_id else None
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> Workspace:
    if workspace_id != get_current_workspace_id(db, current_user):
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workspace, field, value)
    db.commit()
    db.refresh(workspace)
    return workspace
