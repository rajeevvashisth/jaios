"""Model provider abstraction.

Agents call ``get_chat_model()`` and never import a provider SDK directly.
This is what lets Phase 1 run entirely on local Ollama models with no API
keys, while production can point the same call at Claude or OpenAI by
changing configuration only.
"""

from dataclasses import dataclass
from typing import Any, Protocol, cast

from app.config import get_settings


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    raw: dict | None = None


class ChatModel(Protocol):
    def invoke(self, messages: list[LLMMessage]) -> LLMResponse: ...


class AnthropicChatModel:
    def __init__(self, model: str, api_key: str):
        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key)
        self._model = model

    def invoke(self, messages: list[LLMMessage]) -> LLMResponse:
        system = "\n".join(m.content for m in messages if m.role == "system")
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        # The Anthropic/OpenAI SDKs type their `messages`/`system` params as
        # narrow TypedDicts; our plain dicts satisfy that shape at runtime
        # but mypy can't verify it structurally, hence the casts below.
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=cast(Any, turns),
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return LLMResponse(
            content=text, model=self._model, provider="anthropic", raw=resp.model_dump()
        )


class OpenAIChatModel:
    def __init__(self, model: str, api_key: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def invoke(self, messages: list[LLMMessage]) -> LLMResponse:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=cast(Any, [{"role": m.role, "content": m.content} for m in messages]),
        )
        text = resp.choices[0].message.content or ""
        return LLMResponse(
            content=text, model=self._model, provider="openai", raw=resp.model_dump()
        )


class OllamaChatModel:
    def __init__(self, model: str, base_url: str):
        self._model = model
        self._base_url = base_url.rstrip("/")

    def invoke(self, messages: list[LLMMessage]) -> LLMResponse:
        import httpx

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        resp = httpx.post(f"{self._base_url}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self._model,
            provider="ollama",
            raw=data,
        )


def get_chat_model(
    provider: str | None = None,
    model: str | None = None,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ChatModel:
    """Return a chat model for the given provider.

    ``api_key``/``base_url`` let a caller pass workspace-level BYOK
    credentials (see ``services/model_router.py``) instead of the global
    env-configured ones — when omitted, falls back to app settings exactly
    as before BYOK existed.

    Raises ``ValueError`` for an unknown provider and ``RuntimeError`` if the
    provider is selected but its credentials are missing — both are
    configuration errors, not something to silently fall back from.
    """
    settings = get_settings()
    provider = provider or settings.default_llm_provider
    model = model or settings.default_llm_model

    if provider == "anthropic":
        key = api_key or settings.anthropic_api_key
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        return AnthropicChatModel(model=model, api_key=key)
    if provider == "openai":
        key = api_key or settings.openai_api_key
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return OpenAIChatModel(model=model, api_key=key)
    if provider == "ollama":
        return OllamaChatModel(model=model, base_url=base_url or settings.ollama_base_url)

    raise ValueError(f"Unknown LLM provider: {provider}")
