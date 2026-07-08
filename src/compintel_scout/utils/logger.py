"""Append-only run logging for CompIntel Scout."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path


INGEST = "INGEST"
SYNTH = "SYNTH"
INDEX = "INDEX"
ARCHIVE = "ARCHIVE"

VALID_ACTIONS = {INGEST, SYNTH, INDEX, ARCHIVE}
LOG_LINE_PATTERN = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\] \| (?P<action>[A-Z]+) \| (?P<source>[^|]*) \| (?P<notes>.*)$"
)


def _one_line(value: str) -> str:
    return " ".join(value.split())


def format_log_line(
    action: str,
    source: str,
    notes: str,
    *,
    timestamp: datetime | None = None,
) -> str:
    """Format one append-only log entry."""
    normalized_action = action.strip().upper()
    if normalized_action not in VALID_ACTIONS:
        supported = ", ".join(sorted(VALID_ACTIONS))
        raise ValueError(f"Unsupported log action '{action}'. Use one of: {supported}.")

    logged_at = timestamp or datetime.now(UTC)
    if logged_at.tzinfo is None:
        logged_at = logged_at.replace(tzinfo=UTC)

    return (
        f"[{logged_at.isoformat(timespec='seconds')}] | "
        f"{normalized_action} | {_one_line(source)} | {_one_line(notes)}"
    )


def is_valid_log_line(line: str) -> bool:
    """Return whether a line matches the enforced CompIntel log format."""
    match = LOG_LINE_PATTERN.match(line)
    if not match:
        return False
    if match.group("action") not in VALID_ACTIONS:
        return False
    try:
        datetime.fromisoformat(match.group("timestamp"))
    except ValueError:
        return False
    return True


def append_log(
    action: str,
    source: str,
    notes: str,
    *,
    log_path: str | Path = "log.md",
    timestamp: datetime | None = None,
) -> str:
    """Append a formatted line to the run log and return the written line."""
    line = format_log_line(action, source, notes, timestamp=timestamp)
    path = Path(log_path)
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{line}\n")
    return line


def ingest(source: str, notes: str, *, log_path: str | Path = "log.md") -> str:
    """Append an INGEST run log entry."""
    return append_log(INGEST, source, notes, log_path=log_path)


def synth(source: str, notes: str, *, log_path: str | Path = "log.md") -> str:
    """Append a SYNTH run log entry."""
    return append_log(SYNTH, source, notes, log_path=log_path)


def index(source: str, notes: str, *, log_path: str | Path = "log.md") -> str:
    """Append an INDEX run log entry."""
    return append_log(INDEX, source, notes, log_path=log_path)


def archive(source: str, notes: str, *, log_path: str | Path = "log.md") -> str:
    """Append an ARCHIVE run log entry."""
    return append_log(ARCHIVE, source, notes, log_path=log_path)
