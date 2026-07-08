import json
from pathlib import Path

import jsonschema
import pytest

from schema.validate import (
    SAMPLE_COMPETITOR,
    SAMPLE_LEAD,
    SAMPLE_ROLE,
    SAMPLE_SIGNAL,
    SchemaValidationError,
    validate_competitor,
    validate_lead,
    validate_json_file,
    validate_sample_payloads,
    validate_role,
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
    assert results["lead"].valid
    assert results["role"].valid
    assert results["signal"].valid
    assert validate_competitor(SAMPLE_COMPETITOR) == SAMPLE_COMPETITOR
    assert validate_lead(SAMPLE_LEAD) == SAMPLE_LEAD
    assert validate_role(SAMPLE_ROLE) == SAMPLE_ROLE
    assert validate_signal(SAMPLE_SIGNAL) == SAMPLE_SIGNAL


def test_competitor_validation_reports_missing_fields() -> None:
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_competitor({"slug": "acme", "name": "Acme"})

    errors = exc_info.value.errors
    assert "$: missing required field 'category'." in errors
    assert "$: missing required field 'last_updated'." in errors
    assert "$: missing required field 'sources'." in errors


def test_competitor_validation_reports_invalid_fields() -> None:
    payload = {
        **SAMPLE_COMPETITOR,
        "slug": "Acme Analytics",
        "confidence": 2,
        "threat_level": "extreme",
        "sources": [],
    }

    with pytest.raises(SchemaValidationError) as exc_info:
        validate_competitor(payload)

    errors = exc_info.value.errors
    assert "$.slug: must match pattern" in errors[0]
    assert "$.sources: must contain at least 1 item(s)." in errors
    assert "$.confidence: must be less than or equal to 1." in errors
    assert any("$.threat_level: expected one of" in error for error in errors)


def test_signal_validation_reports_bad_enum_and_date() -> None:
    payload = {
        **SAMPLE_SIGNAL,
        "type": "rumor",
        "date": "07/08/2026",
        "source_url": "not-a-url",
        "entities": [],
    }

    with pytest.raises(SchemaValidationError) as exc_info:
        validate_signal(payload)

    errors = exc_info.value.errors
    assert any("$.type: expected one of" in error for error in errors)
    assert "$.date: must be an ISO8601 date." in errors
    assert "$.source_url: must be a valid URI." in errors
    assert "$.entities: must contain at least 1 item(s)." in errors


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


def test_seeded_role_files_validate_against_role_schema() -> None:
    role_schema = json.loads(Path("schema/role.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(role_schema)

    role_files = sorted(
        path for path in Path("wiki/roles").glob("*.md") if path.name != "_template.md"
    )
    assert role_files, "Expected seeded role files in wiki/roles/."

    for role_file in role_files:
        payload = _parse_frontmatter(role_file)
        errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
        assert errors == [], f"{role_file}: " + "; ".join(error.message for error in errors)


def _parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"{path} is missing YAML frontmatter.")

    payload: dict[str, object] = {}
    active_list_key: str | None = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped:
            continue

        if stripped.startswith("- "):
            if active_list_key is None:
                raise AssertionError(f"{path} has list item outside a list key.")
            list_value = payload.get(active_list_key)
            if not isinstance(list_value, list):
                raise AssertionError(f"{path} has invalid list key {active_list_key!r}.")
            list_value.append(_parse_scalar(stripped.removeprefix("- ").strip()))
            continue

        key, sep, raw_value = stripped.partition(":")
        if not sep:
            raise AssertionError(f"{path} has malformed frontmatter line: {line!r}")
        key = key.strip()
        value = raw_value.strip()
        if not value:
            payload[key] = []
            active_list_key = key
            continue
        payload[key] = _parse_scalar(value)
        active_list_key = None

    return payload


def _parse_scalar(value: str) -> object:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
