from compintel_scout import ScoutPipeline, Settings
from compintel_scout.providers import build_client


def test_placeholder_modules_import_cleanly() -> None:
    settings = Settings()
    pipeline = ScoutPipeline(settings=settings)
    client = build_client(settings)

    assert pipeline.collect_raw("acme").as_posix() == "raw/acme.md"
    assert client.provider_name == "codex"
