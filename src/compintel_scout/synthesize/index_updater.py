"""Index rebuilding for local wiki artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IndexEntry:
    """A single wiki entry shown in index.md."""

    title: str
    path: Path


def rebuild_index(
    *,
    wiki_root: str | Path = "wiki",
    index_path: str | Path = "index.md",
    signal_limit: int = 10,
) -> Path:
    """Rebuild index.md from wiki competitors, markets, and signals."""
    wiki_path = Path(wiki_root)
    output_path = Path(index_path)
    competitors = _scan_collection(wiki_path / "competitors")
    markets = _scan_collection(wiki_path / "markets")
    signals = _scan_collection(wiki_path / "signals", reverse=True)[:signal_limit]

    sections = [
        "# Entity Index",
        "",
        "## Competitors",
        "",
        *_format_entries(competitors, output_path.parent),
        "",
        "## Markets",
        "",
        *_format_entries(markets, output_path.parent),
        "",
        "## Signals (latest entries)",
        "",
        *_format_entries(signals, output_path.parent),
        "",
    ]
    output_path.write_text("\n".join(sections), encoding="utf-8")
    return output_path


def _scan_collection(directory: Path, *, reverse: bool = False) -> list[IndexEntry]:
    if not directory.exists():
        return []
    entries = [IndexEntry(title=_read_title(path), path=path) for path in directory.glob("*.md")]
    return sorted(entries, key=lambda entry: entry.path.name, reverse=reverse)


def _read_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return path.stem.replace("_", " ").title()


def _format_entries(entries: list[IndexEntry], relative_to: Path) -> list[str]:
    if not entries:
        return ["_No entries yet._"]
    return [f"- [{entry.title}]({_relative_path(entry.path, relative_to)})" for entry in entries]


def _relative_path(path: Path, relative_to: Path) -> str:
    try:
        return path.relative_to(relative_to).as_posix()
    except ValueError:
        return path.as_posix()
