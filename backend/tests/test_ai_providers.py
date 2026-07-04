from app.models.ai_provider_config import AIProviderConfig
from app.schemas.ai_provider import AIProviderConfigCreate, AIProviderConfigUpdate
from app.services import ai_provider_service, model_router
from app.services.ai_provider_service import create_provider_config, update_provider_config


def test_route_with_no_workspace_config_uses_global_fallback(db_session):
    from app.config import get_settings

    decision = model_router.route(db_session, workspace_id=None, task_type="company_planning")
    settings = get_settings()
    assert decision.provider == settings.default_llm_provider
    assert decision.model == settings.default_llm_model
    assert decision.api_key is None


def test_route_prefers_configured_local_provider_for_local_tier_task(db_session, make_company):
    company = make_company("Router Ollama Co")

    create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(
            workspace_id=company.workspace_id,
            provider="ollama",
            base_url="http://localhost:11434",
            default_model="llama3.2:latest",
            is_default=True,
        ),
    )

    # "document_summary" is a "local" tier task under the default
    # "balanced" operating mode — see model_router.TASK_TIER.
    decision = model_router.route(
        db_session, workspace_id=company.workspace_id, task_type="document_summary"
    )
    assert decision.provider == "ollama"
    assert decision.model == "llama3.2:latest"
    assert decision.base_url == "http://localhost:11434"


def test_route_falls_back_to_whatever_is_configured_when_tier_unmatched(db_session, make_company):
    """Workspace only has a premium (anthropic) provider configured, but
    the requested task is local-tier — routing should still use the one
    thing that IS configured rather than silently dropping to the global
    env default and ignoring the workspace's BYOK setup entirely."""
    company = make_company("Router Only Premium Co")
    create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(
            workspace_id=company.workspace_id,
            provider="anthropic",
            api_key="sk-test-123",
            default_model="claude-sonnet-5",
            is_default=True,
        ),
    )

    decision = model_router.route(
        db_session, workspace_id=company.workspace_id, task_type="document_summary"
    )
    assert decision.provider == "anthropic"
    assert decision.api_key == "sk-test-123"


def test_highest_quality_mode_forces_premium_even_for_local_task(db_session, make_company):
    from app.models.workspace import Workspace

    company = make_company("Router HQ Co")
    workspace = db_session.get(Workspace, company.workspace_id)
    workspace.operating_mode = "highest_quality"
    db_session.commit()

    create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(
            workspace_id=company.workspace_id, provider="ollama", is_default=True
        ),
    )
    create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(
            workspace_id=company.workspace_id,
            provider="anthropic",
            api_key="sk-hq",
            is_default=False,
        ),
    )

    decision = model_router.route(
        db_session, workspace_id=company.workspace_id, task_type="document_summary"
    )
    assert decision.tier == "premium"
    assert decision.provider == "anthropic"


def test_api_key_is_encrypted_at_rest_and_never_returned_plaintext(db_session, make_company):
    company = make_company("BYOK Encryption Co")

    read = create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(
            workspace_id=company.workspace_id,
            provider="anthropic",
            api_key="sk-super-secret",
        ),
    )

    assert read.has_api_key is True
    assert not hasattr(read, "api_key")

    row = db_session.get(AIProviderConfig, read.id)
    assert row.config["api_key_encrypted"] != "sk-super-secret"
    assert "sk-super-secret" not in row.config["api_key_encrypted"]

    # But routing can still recover the real key for actually calling the
    # provider — encryption is at-rest and in-transit-through-the-API only.
    decision = model_router.route(
        db_session, workspace_id=company.workspace_id, task_type="company_planning"
    )
    assert decision.api_key == "sk-super-secret"


def test_update_provider_config_can_rotate_key_and_flip_default(db_session, make_company):
    company = make_company("BYOK Rotate Co")
    first = create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(
            workspace_id=company.workspace_id,
            provider="anthropic",
            api_key="sk-old",
            is_default=True,
        ),
    )
    second = create_provider_config(
        db_session,
        payload=AIProviderConfigCreate(workspace_id=company.workspace_id, provider="ollama"),
    )

    updated_second = update_provider_config(
        db_session, config_id=second.id, updates=AIProviderConfigUpdate(is_default=True)
    )
    assert updated_second.is_default is True

    refreshed_first = ai_provider_service.to_read(db_session.get(AIProviderConfig, first.id))
    assert refreshed_first.is_default is False
