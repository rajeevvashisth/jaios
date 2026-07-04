from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_own_workspace, require_role
from app.models.ai_provider_config import AIProviderConfig
from app.models.user import User
from app.schemas.ai_provider import (
    AIProviderConfigCreate,
    AIProviderConfigRead,
    AIProviderConfigUpdate,
)
from app.schemas.ai_usage import AIUsageRecordRead, AIUsageSummary
from app.services.ai_provider_service import (
    create_provider_config,
    delete_provider_config,
    list_provider_configs,
    update_provider_config,
)
from app.services.ai_usage_service import list_usage, summarize_usage

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers", response_model=list[AIProviderConfigRead])
def get_providers(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AIProviderConfigRead]:
    require_own_workspace(db, current_user, workspace_id)
    return list_provider_configs(db, workspace_id=workspace_id)


@router.post("/providers", response_model=AIProviderConfigRead)
def create_provider(
    payload: AIProviderConfigCreate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> AIProviderConfigRead:
    require_own_workspace(db, current_user, payload.workspace_id)
    return create_provider_config(db, payload=payload)


@router.patch("/providers/{config_id}", response_model=AIProviderConfigRead)
def update_provider(
    config_id: str,
    payload: AIProviderConfigUpdate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> AIProviderConfigRead:
    row = db.get(AIProviderConfig, config_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Provider config not found")
    require_own_workspace(db, current_user, row.workspace_id)
    try:
        return update_provider_config(db, config_id=config_id, updates=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/providers/{config_id}", status_code=204)
def delete_provider(
    config_id: str,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> None:
    row = db.get(AIProviderConfig, config_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Provider config not found")
    require_own_workspace(db, current_user, row.workspace_id)
    delete_provider_config(db, config_id=config_id)


@router.get("/usage", response_model=list[AIUsageRecordRead])
def get_usage(
    workspace_id: str,
    limit: int = 200,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AIUsageRecordRead]:
    require_own_workspace(db, current_user, workspace_id)
    return list_usage(db, workspace_id=workspace_id, limit=limit)


@router.get("/usage/summary", response_model=AIUsageSummary)
def get_usage_summary(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIUsageSummary:
    require_own_workspace(db, current_user, workspace_id)
    return summarize_usage(db, workspace_id=workspace_id)
