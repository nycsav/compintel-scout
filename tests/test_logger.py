from datetime import UTC, datetime
from pathlib import Path

import pytest

from compintel_scout.utils.logger import (
    INGEST,
    append_log,
    archive,
    format_log_line,
    index,
    ingest,
    is_valid_log_line,
    synth,
)


def test_log_line_format_is_enforced() -> None:
    line = format_log_line(
        INGEST,
        "raw/acme.md",
        "captured homepage",
        timestamp=datetime(2026, 7, 8, 12, 30, tzinfo=UTC),
    )

    assert line == "[2026-07-08T12:30:00+00:00] | INGEST | raw/acme.md | captured homepage"
    assert is_valid_log_line(line)


def test_append_log_writes_one_formatted_line(tmp_path: Path) -> None:
    log_path = tmp_path / "log.md"

    written = append_log(
        "index",
        "index.md",
        "updated entity index",
        log_path=log_path,
        timestamp=datetime(2026, 7, 8, 13, 0, tzinfo=UTC),
    )

    assert log_path.read_text(encoding="utf-8") == f"{written}\n"
    assert is_valid_log_line(written)


def test_log_helpers_append_supported_actions(tmp_path: Path) -> None:
    log_path = tmp_path / "log.md"

    ingest("raw/acme.md", "captured", log_path=log_path)
    synth("wiki/acme.md", "summarized", log_path=log_path)
    index("index.md", "linked acme", log_path=log_path)
    archive("raw/acme.md", "archived source", log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert [line.split(" | ")[1] for line in lines] == ["INGEST", "SYNTH", "INDEX", "ARCHIVE"]
    assert all(is_valid_log_line(line) for line in lines)


def test_unsupported_log_action_fails() -> None:
    with pytest.raises(ValueError, match="Unsupported log action"):
        format_log_line("DELETE", "raw/acme.md", "not allowed")
