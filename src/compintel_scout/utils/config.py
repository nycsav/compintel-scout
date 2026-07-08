"""Typed configuration loading for CompIntel Scout."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ConfigError(ValueError):
    """Raised when required configuration is missing or invalid."""


class LLMProvider(StrEnum):
    """Supported LLM provider identifiers."""

    CODEX = "codex"
    SONAR = "sonar"
    CLAUDE = "claude"


CONFIG_KEYS = {
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "PERPLEXITY_API_KEY",
    "ANTHROPIC_API_KEY",
    "BRIGHTDATA_CUSTOMER_ID",
    "BRIGHTDATA_ZONE_SERP",
    "BRIGHTDATA_ZONE_WEB",
    "BRIGHTDATA_PASSWORD",
}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a dotenv file."""
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key in CONFIG_KEYS:
            values[key] = value
    return values


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from dotenv and environment variables."""

    llm_provider: LLMProvider = LLMProvider.CODEX
    openai_api_key: str | None = None
    openai_model: str | None = None
    perplexity_api_key: str | None = None
    anthropic_api_key: str | None = None
    brightdata_customer_id: str | None = None
    brightdata_zone_serp: str | None = None
    brightdata_zone_web: str | None = None
    brightdata_password: str | None = None

    @classmethod
    def from_env(
        cls,
        env_file: str | Path = ".env",
        environ: Mapping[str, str] | None = None,
        *,
        validate: bool = True,
    ) -> "Settings":
        """Load settings from `.env` and the process environment.

        Values in `environ` override values from the dotenv file.
        """
        process_env = os.environ if environ is None else environ
        merged = load_env_file(env_file)
        merged.update({key: process_env[key] for key in CONFIG_KEYS if key in process_env})

        provider = cls._parse_provider(merged.get("LLM_PROVIDER"))
        settings = cls(
            llm_provider=provider,
            openai_api_key=_clean(merged.get("OPENAI_API_KEY")),
            openai_model=_clean(merged.get("OPENAI_MODEL")),
            perplexity_api_key=_clean(merged.get("PERPLEXITY_API_KEY")),
            anthropic_api_key=_clean(merged.get("ANTHROPIC_API_KEY")),
            brightdata_customer_id=_clean(merged.get("BRIGHTDATA_CUSTOMER_ID")),
            brightdata_zone_serp=_clean(merged.get("BRIGHTDATA_ZONE_SERP")),
            brightdata_zone_web=_clean(merged.get("BRIGHTDATA_ZONE_WEB")),
            brightdata_password=_clean(merged.get("BRIGHTDATA_PASSWORD")),
        )

        if validate:
            settings.require_valid()
        return settings

    @staticmethod
    def _parse_provider(provider_name: str | None) -> LLMProvider:
        provider_value = _clean(provider_name) or LLMProvider.CODEX.value
        try:
            return LLMProvider(provider_value.lower())
        except ValueError as exc:
            supported = ", ".join(provider.value for provider in LLMProvider)
            raise ConfigError(f"Unsupported LLM_PROVIDER '{provider_value}'. Use one of: {supported}.") from exc

    def validation_errors(self) -> list[str]:
        """Return missing-field messages for the selected provider."""
        errors: list[str] = []
        if self.llm_provider is LLMProvider.CODEX:
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=codex.")
            if not self.openai_model:
                errors.append("OPENAI_MODEL is required when LLM_PROVIDER=codex.")
        elif self.llm_provider is LLMProvider.SONAR:
            if not self.perplexity_api_key:
                errors.append("PERPLEXITY_API_KEY is required when LLM_PROVIDER=sonar.")
        elif self.llm_provider is LLMProvider.CLAUDE:
            if not self.anthropic_api_key:
                errors.append("ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude.")
        return errors

    def require_valid(self) -> None:
        """Raise `ConfigError` when selected-provider settings are incomplete."""
        errors = self.validation_errors()
        if errors:
            raise ConfigError(" ".join(errors))
