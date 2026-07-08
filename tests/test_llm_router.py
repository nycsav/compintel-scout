from dataclasses import dataclass
from typing import Any

import pytest

from compintel_scout.synthesize.llm_router import LLMRouterError, route_llm
from compintel_scout.utils.config import LLMProvider, Settings


@dataclass(frozen=True)
class FakeClient:
    provider_name: str


def fake_client_factory(provider_name: str) -> FakeClient:
    return FakeClient(provider_name=provider_name)


def test_route_codex_uses_openai_key_and_model() -> None:
    route = route_llm(
        Settings(
            llm_provider=LLMProvider.CODEX,
            openai_api_key="openai-test-key",
            openai_model="gpt-test",
        ),
        client_factory=fake_client_factory,
    )

    assert route.provider is LLMProvider.CODEX
    assert route.model == "gpt-test"
    assert route.client.provider_name == "codex"


def test_route_sonar_uses_perplexity_key() -> None:
    route = route_llm(
        Settings(
            llm_provider=LLMProvider.SONAR,
            perplexity_api_key="perplexity-test-key",
        ),
        client_factory=fake_client_factory,
    )

    assert route.provider is LLMProvider.SONAR
    assert route.model is None
    assert route.client.provider_name == "sonar"


def test_route_claude_uses_anthropic_key() -> None:
    route = route_llm(
        Settings(
            llm_provider=LLMProvider.CLAUDE,
            anthropic_api_key="anthropic-test-key",
        ),
        client_factory=fake_client_factory,
    )

    assert route.provider is LLMProvider.CLAUDE
    assert route.model is None
    assert route.client.provider_name == "claude"


def test_route_raises_for_missing_provider_relevant_key() -> None:
    with pytest.raises(LLMRouterError, match="OPENAI_MODEL is required"):
        route_llm(
            Settings(
                llm_provider=LLMProvider.CODEX,
                openai_api_key="openai-test-key",
            ),
            client_factory=fake_client_factory,
        )


def test_route_raises_clear_error_for_unknown_provider() -> None:
    settings = Settings(llm_provider="bedrock")  # type: ignore[arg-type]

    with pytest.raises(LLMRouterError, match="Unknown LLM_PROVIDER 'bedrock'"):
        route_llm(settings, client_factory=fake_client_factory)


def test_route_does_not_call_network_client_methods() -> None:
    calls: list[str] = []

    class SpyClient:
        def __init__(self, provider_name: str) -> None:
            self.provider_name = provider_name

        def complete(self, prompt: str) -> Any:
            calls.append(prompt)
            raise AssertionError("network-like completion should not be called")

    route = route_llm(
        Settings(
            llm_provider=LLMProvider.SONAR,
            perplexity_api_key="perplexity-test-key",
        ),
        client_factory=SpyClient,
    )

    assert route.client.provider_name == "sonar"
    assert calls == []
