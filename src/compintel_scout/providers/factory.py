"""Factory for provider clients."""

from __future__ import annotations

from compintel_scout.config import LLMProvider, Settings
from compintel_scout.providers.placeholder import PlaceholderLLMClient


def build_client(settings: Settings) -> PlaceholderLLMClient:
    """Build a placeholder client for the configured provider."""
    if settings.llm_provider not in set(LLMProvider):
        raise ValueError(f"Unsupported provider: {settings.llm_provider}")
    return PlaceholderLLMClient(provider_name=settings.llm_provider.value)
