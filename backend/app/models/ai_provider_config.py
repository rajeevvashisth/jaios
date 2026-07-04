from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class AIProviderConfig(Base, TimestampMixin):
    """A workspace's configuration for one AI provider (BYOK).

    ``config`` holds provider-specific, non-secret-shaped data plus one
    encrypted secret where relevant:
      - anthropic/openai: ``{"api_key_encrypted": "...", "default_model": "..."}``
      - ollama: ``{"base_url": "...", "default_model": "..."}`` (no secret)

    Secrets are encrypted at rest via ``core/secrets.py`` before being
    written to ``config`` and are never returned decrypted through the API
    — see ``schemas/ai_provider.py``'s read model, which omits the raw
    ciphertext entirely and only reports whether a key is configured.
    """

    __tablename__ = "ai_provider_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # anthropic|openai|ollama
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
