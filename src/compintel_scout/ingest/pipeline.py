"""Local orchestration for raw -> wiki -> index -> log."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from compintel_scout.synthesize.llm_router import route_llm
from compintel_scout.synthesize.index_updater import rebuild_index
from compintel_scout.synthesize.wiki_writer import WikiPage, infer_payload_kind, write_wiki_page
from compintel_scout.utils.config import Settings
from compintel_scout.utils.logger import append_log
from schema.validate import validate_competitor, validate_signal


class PipelineError(ValueError):
    """Raised when local pipeline orchestration fails."""


@dataclass(frozen=True)
class PipelineResult:
    """Artifacts created by a local pipeline run."""

    kind: str
    raw_source: str
    wiki_page: WikiPage
    index_path: Path
    log_lines: tuple[str, ...]
    provider: str | None = None


def run_local_pipeline(
    raw_input: Mapping[str, Any] | str | Path,
    *,
    workspace_root: str | Path = ".",
    settings: Settings | None = None,
    wiki_timestamp: datetime | None = None,
    log_timestamp: datetime | None = None,
) -> PipelineResult:
    """Run a deterministic local raw -> wiki -> index -> log flow."""
    root = Path(workspace_root)
    provider = route_llm(settings).provider.value if settings is not None else None
    payload, raw_source = load_ingest_payload(raw_input)
    kind = infer_payload_kind(payload)
    validated_payload = validate_ingest_payload(payload, kind)

    wiki_page = write_wiki_page(
        validated_payload,
        wiki_root=root / "wiki",
        kind=kind,
        timestamp=wiki_timestamp,
    )
    index_path = rebuild_index(wiki_root=root / "wiki", index_path=root / "index.md")

    logged_at = log_timestamp or datetime.now(UTC)
    log_path = root / "log.md"
    log_lines = (
        append_log("INGEST", raw_source, f"validated {kind} payload", log_path=log_path, timestamp=logged_at),
        append_log("SYNTH", wiki_page.path.as_posix(), f"wrote {kind} wiki page", log_path=log_path, timestamp=logged_at),
        append_log("INDEX", index_path.as_posix(), "rebuilt entity index", log_path=log_path, timestamp=logged_at),
    )
    return PipelineResult(
        kind=kind,
        raw_source=raw_source,
        wiki_page=wiki_page,
        index_path=index_path,
        log_lines=log_lines,
        provider=provider,
    )


def load_ingest_payload(raw_input: Mapping[str, Any] | str | Path) -> tuple[dict[str, Any], str]:
    """Load a mock ingest payload from memory or a JSON file."""
    if isinstance(raw_input, Mapping):
        return dict(raw_input), "memory"

    path = Path(raw_input)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"Raw input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Raw input file is not valid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}.") from exc

    if not isinstance(payload, Mapping):
        raise PipelineError("Raw input JSON must be an object.")
    return dict(payload), path.as_posix()


def validate_ingest_payload(payload: Mapping[str, Any], kind: str | None = None) -> dict[str, Any]:
    """Validate and return the schema payload used for synthesis."""
    resolved_kind = kind or infer_payload_kind(payload)
    schema_payload = _strip_pipeline_metadata(payload)

    if resolved_kind == "competitor":
        result = validate_competitor(schema_payload)
    elif resolved_kind == "signal":
        result = validate_signal(schema_payload)
    else:
        raise PipelineError(f"No schema validator is available for payload kind '{resolved_kind}'.")

    if not result.valid:
        raise PipelineError("; ".join(result.errors))
    return schema_payload


def _strip_pipeline_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    schema_payload = dict(payload)
    schema_payload.pop("kind", None)
    return schema_payload
