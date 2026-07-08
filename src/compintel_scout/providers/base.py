"""Base provider interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMResponse:
    """A normalized response returned by a model provider."""

    text: str
    provider: str


class LLMClient(Protocol):
    """Protocol implemented by provider clients."""

    provider_name: str

    def complete(self, prompt: str) -> LLMResponse:
        """Return a completion for a prompt."""
        raise NotImplementedError
