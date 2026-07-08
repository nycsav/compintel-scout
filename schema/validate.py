"""Validation helpers for CompIntel Scout JSON schemas."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCHEMA_DIR = Path(__file__).resolve().parent
SCHEMA_FILES = {
    "competitor": "competitor.schema.json",
    "lead": "lead.json",
    "role": "role.json",
    "signal": "signal.schema.json",
}

SAMPLE_COMPETITOR = {
    "slug": "acme_analytics",
    "name": "Acme Analytics",
    "category": ["direct", "analytics"],
    "last_updated": "2026-07-08T14:30:00+00:00",
    "sources": ["https://example.com/about"],
    "confidence": 0.86,
    "summary": "Analytics platform for revenue teams.",
    "products": ["Revenue dashboard", "Pipeline alerts"],
    "pricing": ["Team tier starts at $49 per seat"],
    "signals": ["enterprise_plan_launch"],
    "moat": "Fast onboarding and strong sales ops integrations.",
    "threat_level": "high",
}

SAMPLE_SIGNAL = {
    "slug": "enterprise_plan_launch",
    "type": "product",
    "date": "2026-07-08",
    "headline": "Acme launches enterprise plan",
    "source_url": "https://example.com/blog/enterprise",
    "entities": ["acme_analytics"],
    "summary": "Acme introduced enterprise packaging on its public blog.",
}

SAMPLE_LEAD = {
    "company_slug": "acme_analytics",
    "company_name": "Acme Analytics",
    "domain": "https://www.acme-analytics.example",
    "industry": "B2B SaaS",
    "employee_range": "51-200",
    "tech_stack": ["HubSpot", "Salesforce"],
    "buying_signals": ["expanded demand-gen hiring", "new enterprise pricing page"],
    "icp_fit_score": 8.2,
    "icp_fit_rationale": "Strong GTM complexity and urgent pipeline goals.",
    "contacts": [
        {
            "name": "Jane Example",
            "role_slug": "vp_marketing",
            "title": "VP Marketing",
            "linkedin_url": "https://www.linkedin.com/in/jane-example",
            "email_guess": "jane@example.com",
        }
    ],
    "source_urls": ["https://www.acme-analytics.example/about"],
    "collected_at": "2026-07-08T14:31:00+00:00",
    "llm_provider": "sonar",
}

SAMPLE_ROLE = {
    "role_slug": "vp_marketing",
    "titles": ["VP Marketing", "Vice President of Marketing"],
    "department": "Marketing",
    "pain_points": ["Pipeline pressure", "Attribution fragmentation"],
    "success_metrics": ["Marketing-sourced pipeline", "Conversion rate"],
    "buying_triggers": ["New quarterly target"],
    "messaging_angles": ["Automate qualification with evidence"],
    "preferred_channels": ["Email", "LinkedIn"],
}


class SchemaValidationError(ValueError):
    """Raised when a payload does not match a CompIntel schema."""

    def __init__(self, schema_name: str, errors: list[str]) -> None:
        self.schema_name = schema_name
        self.errors = errors
        super().__init__(f"{schema_name} schema validation failed: {'; '.join(errors)}")


@dataclass(frozen=True)
class ValidationResult:
    """Structured schema validation output."""

    valid: bool
    errors: list[str]
    value: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        return self.valid


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load a named JSON schema from the schema directory."""
    try:
        schema_file = SCHEMA_FILES[schema_name]
    except KeyError as exc:
        supported = ", ".join(sorted(SCHEMA_FILES))
        raise ValueError(f"Unknown schema '{schema_name}'. Use one of: {supported}.") from exc

    return json.loads((SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))


def validate_payload(payload: Mapping[str, Any], schema_name: str) -> ValidationResult:
    """Validate a JSON-like mapping against a named schema."""
    schema = load_schema(schema_name)
    errors = list(_validate_value(payload, schema, "$"))
    value = dict(payload) if not errors else None
    return ValidationResult(valid=not errors, errors=errors, value=value)


def validate_json_file(path: str | Path, schema_name: str) -> ValidationResult:
    """Validate a file-based JSON input against a named schema."""
    json_path = Path(path)
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(False, [f"{json_path}: file not found."])
    except json.JSONDecodeError as exc:
        return ValidationResult(False, [f"{json_path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}."])

    if not isinstance(payload, Mapping):
        return ValidationResult(False, [f"{json_path}: root value must be an object."])
    result = validate_payload(payload, schema_name)
    if result.valid:
        return result
    return ValidationResult(False, [f"{json_path}: {error}" for error in result.errors])


def validate_sample_payloads() -> dict[str, ValidationResult]:
    """Validate built-in sample payloads for both primary schemas."""
    return {
        "competitor": validate_payload(SAMPLE_COMPETITOR, "competitor"),
        "lead": validate_payload(SAMPLE_LEAD, "lead"),
        "role": validate_payload(SAMPLE_ROLE, "role"),
        "signal": validate_payload(SAMPLE_SIGNAL, "signal"),
    }


def validate_competitor(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a validated competitor object or raise `SchemaValidationError`."""
    return _validated_object(payload, "competitor")


def validate_signal(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a validated signal object or raise `SchemaValidationError`."""
    return _validated_object(payload, "signal")


def validate_lead(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a validated lead object or raise `SchemaValidationError`."""
    return _validated_object(payload, "lead")


def validate_role(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a validated role object or raise `SchemaValidationError`."""
    return _validated_object(payload, "role")


def _validated_object(payload: Mapping[str, Any], schema_name: str) -> dict[str, Any]:
    result = validate_payload(payload, schema_name)
    if not result.valid:
        raise SchemaValidationError(schema_name, result.errors)
    return result.value or dict(payload)


def _validate_value(value: Any, schema: Mapping[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type and not _matches_type(value, expected_type):
        return [f"{path}: expected {expected_type}, got {_type_name(value)}."]

    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(repr(item) for item in schema["enum"])
        errors.append(f"{path}: expected one of {allowed}, got {value!r}.")

    if expected_type == "object":
        errors.extend(_validate_object(value, schema, path))
    elif expected_type == "array":
        errors.extend(_validate_array(value, schema, path))
    elif expected_type == "string":
        errors.extend(_validate_string(value, schema, path))
    elif expected_type in {"number", "integer"}:
        errors.extend(_validate_number(value, schema, path))

    return errors


def _validate_object(value: Any, schema: Mapping[str, Any], path: str) -> list[str]:
    if not isinstance(value, Mapping):
        return []

    errors: list[str] = []
    required = schema.get("required", [])
    for field in required:
        if field not in value:
            errors.append(f"{path}: missing required field '{field}'.")

    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        for field in value:
            if field not in properties:
                errors.append(f"{path}.{field}: unexpected field.")

    for field, field_schema in properties.items():
        if field in value:
            errors.extend(_validate_value(value[field], field_schema, f"{path}.{field}"))
    return errors


def _validate_array(value: Any, schema: Mapping[str, Any], path: str) -> list[str]:
    if not isinstance(value, list):
        return []

    errors: list[str] = []
    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(value) < min_items:
        errors.append(f"{path}: must contain at least {min_items} item(s).")

    item_schema = schema.get("items")
    if isinstance(item_schema, Mapping):
        for index, item in enumerate(value):
            errors.extend(_validate_value(item, item_schema, f"{path}[{index}]"))
    return errors


def _validate_string(value: Any, schema: Mapping[str, Any], path: str) -> list[str]:
    if not isinstance(value, str):
        return []

    errors: list[str] = []
    min_length = schema.get("minLength")
    if isinstance(min_length, int) and len(value) < min_length:
        errors.append(f"{path}: must be at least {min_length} character(s).")

    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
        errors.append(f"{path}: must match pattern {pattern!r}.")

    value_format = schema.get("format")
    if value_format == "date-time" and not _is_datetime(value):
        errors.append(f"{path}: must be an ISO8601 date-time.")
    elif value_format == "date" and not _is_date(value):
        errors.append(f"{path}: must be an ISO8601 date.")
    elif value_format == "uri" and not _is_uri(value):
        errors.append(f"{path}: must be a valid URI.")
    return errors


def _validate_number(value: Any, schema: Mapping[str, Any], path: str) -> list[str]:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return []

    errors: list[str] = []
    minimum = schema.get("minimum")
    if isinstance(minimum, int | float) and value < minimum:
        errors.append(f"{path}: must be greater than or equal to {minimum}.")
    maximum = schema.get("maximum")
    if isinstance(maximum, int | float) and value > maximum:
        errors.append(f"{path}: must be less than or equal to {maximum}.")
    return errors


def _matches_type(value: Any, expected_type: Any) -> bool:
    if expected_type == "object":
        return isinstance(value, Mapping)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, Mapping):
        return "object"
    return type(value).__name__


def _is_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _is_date(value: str) -> bool:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%d") == value


def _is_uri(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)
