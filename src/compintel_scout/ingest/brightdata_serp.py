"""Bright Data SERP raw ingestion helpers.

The network client is intentionally injectable so tests and demos can run
without live Bright Data credentials or API calls.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Protocol


class SerpClient(Protocol):
    """Minimal client interface for structured SERP responses."""

    def search(self, query: str) -> Any:
        """Return a JSON-serializable Bright Data SERP response."""


def unix_timestamp() -> int:
    """Return the current Unix timestamp in seconds."""
    return int(time.time())


def slugify_query(query: str) -> str:
    """Convert a search query into a stable filename slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", query.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "query"


def serp_output_path(
    query: str,
    *,
    raw_root: str | Path = "raw",
    timestamp: int | None = None,
) -> Path:
    """Return `raw/serp/{query_slug}_{unix_ts}.json` for a query."""
    unix_ts = unix_timestamp() if timestamp is None else timestamp
    return Path(raw_root) / "serp" / f"{slugify_query(query)}_{unix_ts}.json"


def ingest_serp_query(
    query: str,
    client: SerpClient,
    *,
    raw_root: str | Path = "raw",
    timestamp: int | None = None,
) -> Path:
    """Fetch a structured SERP response and store it in the raw layer."""
    payload = client.search(query)
    output_path = serp_output_path(query, raw_root=raw_root, timestamp=timestamp)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path
