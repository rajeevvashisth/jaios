"""Decides which AI provider/model handles a given task.

Deliberately a plain, inspectable table lookup — not a learned or adaptive
system. Each ``task_type`` has a natural "tier" (premium reasoning vs.
cheap/local), and the workspace's ``operating_mode`` either respects that
(``balanced``) or forces every task to one tier regardless of type.

Backward-compatibility guarantee: a workspace with no ``AIProviderConfig``
rows at all (true for Jyka Labs LLP today, and for this repo's own dev
setup) always gets exactly the pre-routing behavior — the single global
env-configured provider/model for every task, ignoring tier entirely.
Routing/tiering only takes effect once a workspace has actually configured
at least one provider, so nothing changes for an existing deployment until
someone opts in via AI Settings.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.secrets import decrypt_secret
from app.models.ai_provider_config import AIProviderConfig
from app.models.workspace import Workspace

# task_type -> natural tier. "premium" = highest-quality reasoning path;
# "local" = cheap/local path. Unknown task types default to "premium" —
# under-routing an unfamiliar task to a weaker model is a worse failure
# mode than over-spending on one that turns out to be simple.
TASK_TIER: dict[str, str] = {
    "company_planning": "premium",
    "product_feature_planning": "premium",
    "coding_assistance": "premium",
    "document_summary": "local",
    "document_extraction": "local",
    "compliance_summary": "premium",
    "finance_summary": "premium",
    "expense_categorization": "local",
    "workflow_followup_draft": "local",
    "knowledgebase_qa": "local",
    "general_chat": "local",
}

# Which tier each provider is considered to serve.
PROVIDER_TIER: dict[str, str] = {
    "anthropic": "premium",
    "openai": "premium",
    "ollama": "local",
}


@dataclass
class RoutingDecision:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None
    tier: str
    task_type: str


def _resolve_tier(task_type: str, operating_mode: str) -> str:
    natural = TASK_TIER.get(task_type, "premium")
    if operating_mode == "highest_quality":
        return "premium"
    if operating_mode in ("lowest_cost", "privacy_first"):
        return "local"
    return natural  # balanced: respect the task's own tier


def route(
    db: Session,
    *,
    workspace_id: str | None,
    task_type: str,
    agent_key: str | None = None,
) -> RoutingDecision:
    operating_mode = "balanced"
    configs: list[AIProviderConfig] = []
    if workspace_id:
        workspace = db.get(Workspace, workspace_id)
        if workspace:
            operating_mode = workspace.operating_mode
        configs = (
            db.query(AIProviderConfig)
            .filter(
                AIProviderConfig.workspace_id == workspace_id,
                AIProviderConfig.is_enabled.is_(True),
            )
            .all()
        )

    tier = _resolve_tier(task_type, operating_mode)

    if not configs:
        return _global_fallback(task_type, tier)

    chosen = _pick(configs, tier)
    if chosen is None:
        return _global_fallback(task_type, tier)

    config = chosen.config or {}
    api_key = (
        decrypt_secret(config["api_key_encrypted"]) if config.get("api_key_encrypted") else None
    )
    model = config.get("default_model") or _default_model_for(chosen.provider)
    return RoutingDecision(
        provider=chosen.provider,
        model=model,
        api_key=api_key,
        base_url=config.get("base_url"),
        tier=tier,
        task_type=task_type,
    )


def _pick(configs: list[AIProviderConfig], tier: str) -> AIProviderConfig | None:
    matching = [c for c in configs if PROVIDER_TIER.get(c.provider) == tier]
    default_match = next((c for c in matching if c.is_default), None)
    if default_match:
        return default_match
    if matching:
        return matching[0]
    # Nothing configured for the requested tier — fall back to whatever
    # IS configured rather than silently dropping to the global env
    # default when the workspace clearly has BYOK set up for something.
    default_any = next((c for c in configs if c.is_default), None)
    return default_any or (configs[0] if configs else None)


def _default_model_for(provider: str) -> str:
    settings = get_settings()
    if provider == "anthropic":
        return (
            settings.default_llm_model
            if settings.default_llm_provider == "anthropic"
            else "claude-sonnet-5"
        )
    if provider == "openai":
        return "gpt-4o-mini"
    return "llama3.2:latest"


def _global_fallback(task_type: str, tier: str) -> RoutingDecision:
    settings = get_settings()
    return RoutingDecision(
        provider=settings.default_llm_provider,
        model=settings.default_llm_model,
        api_key=None,
        base_url=None,
        tier=tier,
        task_type=task_type,
    )
