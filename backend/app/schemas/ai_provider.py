from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class AIProvider(StrEnum):
    anthropic = "anthropic"
    openai = "openai"
    ollama = "ollama"


class AIProviderConfigCreate(BaseModel):
    workspace_id: str
    provider: AIProvider
    display_name: str | None = None
    is_enabled: bool = True
    is_default: bool = False
    # Plaintext here (over HTTPS in production) — encrypted before storage
    # by ai_provider_service.create_provider_config, never stored raw and
    # never returned by any read endpoint. Irrelevant for ollama.
    api_key: str | None = None
    base_url: str | None = None  # ollama endpoint
    default_model: str | None = None


class AIProviderConfigUpdate(BaseModel):
    display_name: str | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None


class AIProviderConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    provider: AIProvider
    display_name: str | None
    is_enabled: bool
    is_default: bool
    # Never the key itself — just whether one is on file, so the UI can
    # show "configured" / "not configured" without ever handling ciphertext.
    has_api_key: bool
    base_url: str | None
    default_model: str | None
