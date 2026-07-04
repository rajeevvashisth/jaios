from sqlalchemy.orm import Session

from app.core.secrets import encrypt_secret
from app.models.ai_provider_config import AIProviderConfig
from app.schemas.ai_provider import (
    AIProvider,
    AIProviderConfigCreate,
    AIProviderConfigRead,
    AIProviderConfigUpdate,
)


def to_read(row: AIProviderConfig) -> AIProviderConfigRead:
    config = row.config or {}
    return AIProviderConfigRead(
        id=row.id,
        workspace_id=row.workspace_id,
        # Explicit enum construction (not just a str->enum annotation) so a
        # stray/legacy value stored in the DB surfaces as a clear error here
        # rather than silently passing through as a plain string.
        provider=AIProvider(row.provider),
        display_name=row.display_name,
        is_enabled=row.is_enabled,
        is_default=row.is_default,
        has_api_key=bool(config.get("api_key_encrypted")),
        base_url=config.get("base_url"),
        default_model=config.get("default_model"),
    )


def list_provider_configs(db: Session, *, workspace_id: str) -> list[AIProviderConfigRead]:
    rows = db.query(AIProviderConfig).filter(AIProviderConfig.workspace_id == workspace_id).all()
    return [to_read(r) for r in rows]


def create_provider_config(db: Session, *, payload: AIProviderConfigCreate) -> AIProviderConfigRead:
    config: dict = {}
    if payload.api_key:
        config["api_key_encrypted"] = encrypt_secret(payload.api_key)
    if payload.base_url:
        config["base_url"] = payload.base_url
    if payload.default_model:
        config["default_model"] = payload.default_model

    if payload.is_default:
        _clear_other_defaults(db, workspace_id=payload.workspace_id)

    row = AIProviderConfig(
        workspace_id=payload.workspace_id,
        provider=payload.provider.value,
        display_name=payload.display_name,
        is_enabled=payload.is_enabled,
        is_default=payload.is_default,
        config=config,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return to_read(row)


def update_provider_config(
    db: Session, *, config_id: str, updates: AIProviderConfigUpdate
) -> AIProviderConfigRead:
    row = db.get(AIProviderConfig, config_id)
    if row is None:
        raise ValueError(f"No such AI provider config: {config_id}")

    data = updates.model_dump(exclude_unset=True)
    config = dict(row.config or {})

    api_key = data.pop("api_key", None)
    if api_key:
        config["api_key_encrypted"] = encrypt_secret(api_key)
    base_url = data.pop("base_url", None)
    if base_url is not None:
        config["base_url"] = base_url
    default_model = data.pop("default_model", None)
    if default_model is not None:
        config["default_model"] = default_model
    row.config = config

    if data.get("is_default"):
        _clear_other_defaults(db, workspace_id=row.workspace_id, exclude_id=row.id)

    for field, value in data.items():
        setattr(row, field, value)

    db.commit()
    db.refresh(row)
    return to_read(row)


def delete_provider_config(db: Session, *, config_id: str) -> None:
    row = db.get(AIProviderConfig, config_id)
    if row is None:
        raise ValueError(f"No such AI provider config: {config_id}")
    db.delete(row)
    db.commit()


def _clear_other_defaults(db: Session, *, workspace_id: str, exclude_id: str | None = None) -> None:
    query = db.query(AIProviderConfig).filter(
        AIProviderConfig.workspace_id == workspace_id, AIProviderConfig.is_default.is_(True)
    )
    if exclude_id:
        query = query.filter(AIProviderConfig.id != exclude_id)
    for other in query.all():
        other.is_default = False
