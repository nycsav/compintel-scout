"""Second-brain pipeline placeholders for raw -> wiki -> schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from compintel_scout.config import Settings


@dataclass(frozen=True)
class PipelinePaths:
    """Filesystem locations used by the agent pipeline."""

    root: Path = Path(".")

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def wiki(self) -> Path:
        return self.root / "wiki"

    @property
    def schema(self) -> Path:
        return self.root / "schema"


@dataclass
class ScoutPipeline:
    """Coordinates the placeholder intelligence workflow."""

    settings: Settings
    paths: PipelinePaths = PipelinePaths()

    def collect_raw(self, entity: str) -> Path:
        """Return the intended raw artifact path without calling external APIs."""
        return self.paths.raw / f"{entity}.md"

    def synthesize_wiki(self, entity: str) -> Path:
        """Return the intended wiki artifact path without mutating append-only notes."""
        return self.paths.wiki / f"{entity}.md"

    def validate_schema(self, entity: dict[str, object]) -> bool:
        """Placeholder schema validation hook."""
        return bool(entity.get("name"))
