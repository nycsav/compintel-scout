"""Schema helpers for CompIntel Scout."""

from schema.validate import (
    SAMPLE_LEAD,
    SAMPLE_ROLE,
    SchemaValidationError,
    ValidationResult,
    validate_competitor,
    validate_lead,
    validate_json_file,
    validate_payload,
    validate_role,
    validate_sample_payloads,
    validate_signal,
)
from schema.validators import validate_entity

__all__ = [
    "SchemaValidationError",
    "SAMPLE_LEAD",
    "SAMPLE_ROLE",
    "ValidationResult",
    "validate_competitor",
    "validate_entity",
    "validate_lead",
    "validate_json_file",
    "validate_payload",
    "validate_role",
    "validate_sample_payloads",
    "validate_signal",
]
