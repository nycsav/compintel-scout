import json
from pathlib import Path

from schema.validate import (
    SAMPLE_COMPETITOR,
    SAMPLE_SIGNAL,
    validate_competitor,
    validate_json_file,
    validate_sample_payloads,
    validate_signal,
)
from schema.validators import validate_entity


def test_entity_schema_file_exists_and_loads() -> None:
    schema_path = Path("schema/entity.schema.json")
    entity_schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert entity_schema["title"] == "CompIntel Entity"
    assert "name" in entity_schema["required"]


def test_entity_validator_accepts_placeholder_entity() -> None:
    assert validate_entity(
        {
            "name": "Acme",
            "category": "company",
            "sources": [],
        }
    )


def test_competitor_and_signal_samples_validate() -> None:
    results = validate_sample_payloads()

    assert results["competitor"].valid
    assert results["signal"].valid


def test_competitor_validation_reports_missing_fields() -> None:
    result = validate_competitor({"name": "Acme"})

    assert not result.valid
    assert "$: missing required field 'website'." in result.errors
    assert "$: missing required field 'category'." in result.errors
    assert "$: missing required field 'sources'." in result.errors


def test_signal_validation_reports_bad_enum_and_confidence() -> None:
    payload = {
        **SAMPLE_SIGNAL,
        "signal_type": "rumor",
        "confidence": 2,
    }

    result = validate_signal(payload)

    assert not result.valid
    assert any("$.signal_type: expected one of" in error for error in result.errors)
    assert "$.confidence: must be less than or equal to 1." in result.errors


def test_file_based_json_validation(tmp_path: Path) -> None:
    payload_path = tmp_path / "competitor.json"
    payload_path.write_text(json.dumps(SAMPLE_COMPETITOR), encoding="utf-8")

    result = validate_json_file(payload_path, "competitor")

    assert result.valid


def test_file_based_json_validation_reports_decode_errors(tmp_path: Path) -> None:
    payload_path = tmp_path / "bad.json"
    payload_path.write_text("{", encoding="utf-8")

    result = validate_json_file(payload_path, "signal")

    assert not result.valid
    assert "invalid JSON" in result.errors[0]
