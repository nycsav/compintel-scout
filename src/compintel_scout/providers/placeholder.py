"""Placeholder provider client.

This module intentionally avoids external API calls while the repository is
being scaffolded.
"""

from __future__ import annotations

from dataclasses import dataclass

from compintel_scout.providers.base import LLMResponse


@dataclass(frozen=True)
class PlaceholderLLMClient:
    """A no-network stand-in for future provider integrations."""

    provider_name: str

    def complete(self, prompt: str) -> LLMResponse:
        raise NotImplementedError("External provider calls are not implemented yet.")
