"""Provider router for synthesis-time LLM clients.

The router selects a configured provider and returns an injectable, no-network
client placeholder. Real API calls belong in future provider implementations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from compintel_scout.providers.placeholder import PlaceholderLLMClient
from compintel_scout.utils.config import LLMProvider, Settings


class LLMRouterError(ValueError):
    """Raised when LLM provider routing cannot be completed."""


@dataclass(frozen=True)
class LLMRoute:
    """Resolved provider route and placeholder client."""

    provider: LLMProvider
    client: PlaceholderLLMClient
    model: str | None = None


ClientFactory = Callable[[str], PlaceholderLLMClient]


def route_llm(
    settings: Settings,
    *,
    client_factory: ClientFactory = PlaceholderLLMClient,
) -> LLMRoute:
    """Select the configured LLM provider and return a no-network route."""
    provider = _normalize_provider(settings.llm_provider)

    if provider is LLMProvider.CODEX:
        _require("OPENAI_API_KEY", settings.openai_api_key, provider)
        _require("OPENAI_MODEL", settings.openai_model, provider)
        return LLMRoute(
            provider=provider,
            client=client_factory(provider.value),
            model=settings.openai_model,
        )

    if provider is LLMProvider.SONAR:
        _require("PERPLEXITY_API_KEY", settings.perplexity_api_key, provider)
        return LLMRoute(provider=provider, client=client_factory(provider.value))

    if provider is LLMProvider.CLAUDE:
        _require("ANTHROPIC_API_KEY", settings.anthropic_api_key, provider)
        return LLMRoute(provider=provider, client=client_factory(provider.value))

    raise LLMRouterError(f"Unsupported LLM_PROVIDER '{provider}'.")


def _normalize_provider(provider: Any) -> LLMProvider:
    if isinstance(provider, LLMProvider):
        return provider
    try:
        return LLMProvider(str(provider).strip().lower())
    except ValueError as exc:
        supported = ", ".join(provider.value for provider in LLMProvider)
        raise LLMRouterError(f"Unknown LLM_PROVIDER '{provider}'. Use one of: {supported}.") from exc


def _require(field_name: str, value: str | None, provider: LLMProvider) -> None:
    if not value:
        raise LLMRouterError(f"{field_name} is required when LLM_PROVIDER={provider.value}.")
