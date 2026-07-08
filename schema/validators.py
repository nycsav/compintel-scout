"""Small stdlib validators for scaffold-time schema checks."""

from __future__ import annotations

from collections.abc import Mapping


REQUIRED_ENTITY_FIELDS = {"name", "category", "sources"}
ENTITY_CATEGORIES = {"company", "product", "market", "person", "unknown"}


def validate_entity(entity: Mapping[str, object]) -> bool:
    """Validate the minimal entity shape used by placeholder tests."""
    if not REQUIRED_ENTITY_FIELDS.issubset(entity):
        return False
    if not isinstance(entity["name"], str) or not entity["name"].strip():
        return False
    if entity["category"] not in ENTITY_CATEGORIES:
        return False
    if not isinstance(entity["sources"], list):
        return False
    return all(isinstance(source, str) for source in entity["sources"])
