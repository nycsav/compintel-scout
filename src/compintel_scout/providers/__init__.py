"""Provider abstractions for future model backends."""

from compintel_scout.providers.base import LLMClient, LLMResponse
from compintel_scout.providers.factory import build_client

__all__ = ["LLMClient", "LLMResponse", "build_client"]
