import json
from datetime import UTC, datetime
from pathlib import Path

from compintel_scout.ingest.pipeline import run_local_pipeline
from compintel_scout.synthesize.index_updater import rebuild_index
from compintel_scout.synthesize.wiki_writer import write_competitor_page, write_signal_page
from compintel_scout.utils.logger import is_valid_log_line


SNAPSHOT_TIME = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
LOG_TIME = datetime(2026, 7, 8, 14, 31, tzinfo=UTC)


def competitor_payload() -> dict[str, object]:
    return {
        "name": "Acme Analytics",
        "website": "https://example.com",
        "category": "direct",
        "summary": "Analytics platform for revenue teams.",
        "strengths": ["Fast onboarding"],
        "weaknesses": ["Limited enterprise controls"],
        "sources": ["https://example.com/about"],
    }


def signal_payload() -> dict[str, object]:
    return {
        "title": "Acme launches enterprise plan",
        "signal_type": "product",
        "source": "https://example.com/blog/enterprise",
        "notes": "New packaging surfaced on the public blog.",
        "confidence": 0.9,
        "related_competitors": ["Acme Analytics"],
    }


def test_competitor_page_creation(tmp_path: Path) -> None:
    page = write_competitor_page(
        competitor_payload(),
        wiki_root=tmp_path / "wiki",
        timestamp=SNAPSHOT_TIME,
    )

    assert page.path == tmp_path / "wiki" / "competitors" / "acme_analytics.md"
    content = page.path.read_text(encoding="utf-8")
    assert content.startswith("# Acme Analytics")
    assert "## Snapshot - 2026-07-08T14:30:00+00:00" in content
    assert "- **Website:** https://example.com" in content
    assert "  - Fast onboarding" in content


def test_signal_page_creation(tmp_path: Path) -> None:
    page = write_signal_page(
        signal_payload(),
        wiki_root=tmp_path / "wiki",
        timestamp=SNAPSHOT_TIME,
    )

    assert page.path == tmp_path / "wiki" / "signals" / "acme_launches_enterprise_plan.md"
    content = page.path.read_text(encoding="utf-8")
    assert content.startswith("# Acme launches enterprise plan")
    assert "- **Signal Type:** product" in content
    assert "- **Confidence:** 0.9" in content


def test_wiki_page_updates_append_snapshots(tmp_path: Path) -> None:
    write_competitor_page(
        competitor_payload(),
        wiki_root=tmp_path / "wiki",
        timestamp=SNAPSHOT_TIME,
    )
    page = write_competitor_page(
        {**competitor_payload(), "summary": "Updated public summary."},
        wiki_root=tmp_path / "wiki",
        timestamp=datetime(2026, 7, 8, 15, 0, tzinfo=UTC),
    )

    content = page.path.read_text(encoding="utf-8")
    assert content.count("## Snapshot -") == 2
    assert "Analytics platform for revenue teams." in content
    assert "Updated public summary." in content


def test_index_rebuild_content(tmp_path: Path) -> None:
    write_competitor_page(competitor_payload(), wiki_root=tmp_path / "wiki", timestamp=SNAPSHOT_TIME)
    write_signal_page(signal_payload(), wiki_root=tmp_path / "wiki", timestamp=SNAPSHOT_TIME)

    index_path = rebuild_index(wiki_root=tmp_path / "wiki", index_path=tmp_path / "index.md")

    content = index_path.read_text(encoding="utf-8")
    assert "## Competitors" in content
    assert "- [Acme Analytics](wiki/competitors/acme_analytics.md)" in content
    assert "## Markets" in content
    assert "_No entries yet._" in content
    assert "## Signals (latest entries)" in content
    assert "- [Acme launches enterprise plan](wiki/signals/acme_launches_enterprise_plan.md)" in content


def test_pipeline_success_path_creates_wiki_index_and_appends_log(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw" / "sample_competitor.json"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(json.dumps({"kind": "competitor", **competitor_payload()}), encoding="utf-8")
    existing_log_line = "[2026-07-08T14:00:00+00:00] | INGEST | seed | previous run\n"
    (tmp_path / "log.md").write_text(existing_log_line, encoding="utf-8")

    result = run_local_pipeline(
        raw_path,
        workspace_root=tmp_path,
        wiki_timestamp=SNAPSHOT_TIME,
        log_timestamp=LOG_TIME,
    )

    assert result.kind == "competitor"
    assert result.wiki_page.path.exists()
    assert (tmp_path / "index.md").read_text(encoding="utf-8").startswith("# Entity Index")

    log_lines = (tmp_path / "log.md").read_text(encoding="utf-8").splitlines()
    assert log_lines[0] == existing_log_line.strip()
    assert len(log_lines) == 4
    assert [line.split(" | ")[1] for line in log_lines[1:]] == ["INGEST", "SYNTH", "INDEX"]
    assert all(is_valid_log_line(line) for line in log_lines)
    assert all(line.startswith("[2026-07-08T14:31:00+00:00]") for line in log_lines[1:])
