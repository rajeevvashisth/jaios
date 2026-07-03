from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://jaios:jaios@localhost:5432/jaios"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    default_llm_provider: str = "anthropic"
    default_llm_model: str = "claude-sonnet-5"

    backend_port: int = 8000

    workspace_root: str = "./workspace"
    coding_worker_backend: str = "claude_code"  # claude_code | openhands
    slack_webhook_url: str | None = None

    global_approval_required_actions: str = "deploy,finance_payment,legal_signature"

    # --- Auth ---
    # Default is dev-only and MUST be overridden via JWT_SECRET_KEY before
    # any non-local deployment — anyone with this value can forge tokens.
    jwt_secret_key: str = "insecure-dev-secret-change-me-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    @property
    def global_approval_required_action_list(self) -> list[str]:
        return [a.strip() for a in self.global_approval_required_actions.split(",") if a.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
