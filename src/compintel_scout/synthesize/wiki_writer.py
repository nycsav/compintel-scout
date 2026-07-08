"""Append-style wiki page writers for synthesized intelligence."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


WIKI_COLLECTIONS = {
    "competitor": "competitors",
    "market": "markets",
    "signal": "signals",
}


@dataclass(frozen=True)
class WikiPage:
    """A written wiki page."""

    kind: str
    title: str
    path: Path


def slugify_title(value: str) -> str:
    """Convert a title into a stable markdown filename slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "untitled"


def infer_payload_kind(payload: Mapping[str, Any]) -> str:
    """Infer the wiki collection for a payload."""
    explicit_kind = payload.get("kind")
    if isinstance(explicit_kind, str) and explicit_kind.strip():
        return explicit_kind.strip().lower()
    if "signal_type" in payload:
        return "signal"
    if "market_size" in payload or "market" in payload:
        return "market"
    return "competitor"


def payload_title(payload: Mapping[str, Any], kind: str | None = None) -> str:
    """Return the display title for a payload."""
    resolved_kind = kind or infer_payload_kind(payload)
    if resolved_kind == "signal":
        return str(payload.get("title") or "Untitled Signal")
    return str(payload.get("name") or payload.get("title") or "Untitled")


def wiki_page_path(
    payload: Mapping[str, Any],
    *,
    wiki_root: str | Path = "wiki",
    kind: str | None = None,
) -> Path:
    """Return the target wiki path for a payload."""
    resolved_kind = kind or infer_payload_kind(payload)
    try:
        collection = WIKI_COLLECTIONS[resolved_kind]
    except KeyError as exc:
        supported = ", ".join(sorted(WIKI_COLLECTIONS))
        raise ValueError(f"Unsupported wiki payload kind '{resolved_kind}'. Use one of: {supported}.") from exc
    return Path(wiki_root) / collection / f"{slugify_title(payload_title(payload, resolved_kind))}.md"


def write_wiki_page(
    payload: Mapping[str, Any],
    *,
    wiki_root: str | Path = "wiki",
    kind: str | None = None,
    timestamp: datetime | None = None,
) -> WikiPage:
    """Create or append a deterministic snapshot to a wiki page."""
    resolved_kind = kind or infer_payload_kind(payload)
    title = payload_title(payload, resolved_kind)
    path = wiki_page_path(payload, wiki_root=wiki_root, kind=resolved_kind)
    path.parent.mkdir(parents=True, exist_ok=True)

    snapshot = _snapshot_markdown(payload, resolved_kind, timestamp=timestamp)
    if path.exists():
        existing = path.read_text(encoding="utf-8").rstrip()
        content = f"{existing}\n\n---\n\n{snapshot}\n"
    else:
        content = f"# {title}\n\n<!-- compintel-kind: {resolved_kind} -->\n\n{snapshot}\n"
    path.write_text(content, encoding="utf-8")
    return WikiPage(kind=resolved_kind, title=title, path=path)


def write_competitor_page(
    payload: Mapping[str, Any],
    *,
    wiki_root: str | Path = "wiki",
    timestamp: datetime | None = None,
) -> WikiPage:
    """Write a competitor wiki page."""
    return write_wiki_page(payload, wiki_root=wiki_root, kind="competitor", timestamp=timestamp)


def write_market_page(
    payload: Mapping[str, Any],
    *,
    wiki_root: str | Path = "wiki",
    timestamp: datetime | None = None,
) -> WikiPage:
    """Write a market wiki page."""
    return write_wiki_page(payload, wiki_root=wiki_root, kind="market", timestamp=timestamp)


def write_signal_page(
    payload: Mapping[str, Any],
    *,
    wiki_root: str | Path = "wiki",
    timestamp: datetime | None = None,
) -> WikiPage:
    """Write a signal wiki page."""
    return write_wiki_page(payload, wiki_root=wiki_root, kind="signal", timestamp=timestamp)


def _snapshot_markdown(
    payload: Mapping[str, Any],
    kind: str,
    *,
    timestamp: datetime | None = None,
) -> str:
    snapshot_time = timestamp or datetime.now(UTC)
    if snapshot_time.tzinfo is None:
        snapshot_time = snapshot_time.replace(tzinfo=UTC)

    lines = [f"## Snapshot - {snapshot_time.isoformat(timespec='seconds')}", ""]
    if kind == "competitor":
        _append_field(lines, "Website", payload.get("website"))
        _append_field(lines, "Category", payload.get("category"))
        _append_field(lines, "Summary", payload.get("summary"))
        _append_list(lines, "Strengths", payload.get("strengths"))
        _append_list(lines, "Weaknesses", payload.get("weaknesses"))
        _append_list(lines, "Sources", payload.get("sources"))
    elif kind == "signal":
        _append_field(lines, "Signal Type", payload.get("signal_type"))
        _append_field(lines, "Source", payload.get("source"))
        _append_field(lines, "Confidence", payload.get("confidence"))
        _append_field(lines, "Observed At", payload.get("observed_at"))
        _append_field(lines, "Notes", payload.get("notes"))
        _append_list(lines, "Related Competitors", payload.get("related_competitors"))
    elif kind == "market":
        _append_field(lines, "Summary", payload.get("summary"))
        _append_field(lines, "Market Size", payload.get("market_size"))
        _append_list(lines, "Sources", payload.get("sources"))
    return "\n".join(lines).rstrip()


def _append_field(lines: list[str], label: str, value: Any) -> None:
    if value is None or value == "":
        return
    lines.append(f"- **{label}:** {value}")


def _append_list(lines: list[str], label: str, value: Any) -> None:
    if not value:
        return
    if isinstance(value, str):
        value = [value]
    lines.append(f"- **{label}:**")
    for item in value:
        lines.append(f"  - {item}")
