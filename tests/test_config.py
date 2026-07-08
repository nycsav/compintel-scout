from pathlib import Path

import pytest

from compintel_scout.utils.config import ConfigError, LLMProvider, Settings, load_env_file


def test_load_env_file_reads_known_keys(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
        # comments are ignored
        LLM_PROVIDER=sonar
        PERPLEXITY_API_KEY='from-file'
        IGNORED_KEY=value
        """,
        encoding="utf-8",
    )

    values = load_env_file(env_file)

    assert values == {
        "LLM_PROVIDER": "sonar",
        "PERPLEXITY_API_KEY": "from-file",
    }


def test_environment_overrides_dotenv_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_PROVIDER=sonar\nPERPLEXITY_API_KEY=from-file\n",
        encoding="utf-8",
    )

    settings = Settings.from_env(
        env_file,
        environ={"PERPLEXITY_API_KEY": "from-env"},
    )

    assert settings.llm_provider is LLMProvider.SONAR
    assert settings.perplexity_api_key == "from-env"


def test_codex_requires_openai_key_and_model(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_PROVIDER=codex\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="OPENAI_API_KEY.*OPENAI_MODEL"):
        Settings.from_env(env_file, environ={})


def test_provider_specific_validation_only_requires_selected_provider(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_PROVIDER=claude\nANTHROPIC_API_KEY=anthropic-test-key\n",
        encoding="utf-8",
    )

    settings = Settings.from_env(env_file, environ={})

    assert settings.llm_provider is LLMProvider.CLAUDE
    assert settings.openai_api_key is None
    assert settings.perplexity_api_key is None


def test_brightdata_settings_load_but_are_not_provider_required(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "LLM_PROVIDER=sonar",
                "PERPLEXITY_API_KEY=perplexity-test-key",
                "BRIGHTDATA_CUSTOMER_ID=customer-id",
                "BRIGHTDATA_ZONE_SERP=serp-zone",
                "BRIGHTDATA_ZONE_WEB=web-zone",
                "BRIGHTDATA_PASSWORD=brightdata-password",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings.from_env(env_file, environ={})

    assert settings.llm_provider is LLMProvider.SONAR
    assert settings.brightdata_customer_id == "customer-id"
    assert settings.brightdata_zone_serp == "serp-zone"
    assert settings.brightdata_zone_web == "web-zone"
    assert settings.brightdata_password == "brightdata-password"
