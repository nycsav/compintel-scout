import json
from pathlib import Path

from compintel_scout.ingest.brightdata_serp import (
    ingest_serp_query,
    serp_output_path,
    slugify_query,
    unix_timestamp as serp_unix_timestamp,
)
from compintel_scout.ingest.brightdata_web import (
    html_to_markdown_text,
    ingest_web_page,
    page_output_path,
    slugify_domain,
    unix_timestamp as web_unix_timestamp,
)


class FakeSerpClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str) -> dict[str, object]:
        self.queries.append(query)
        return {
            "query": query,
            "results": [
                {
                    "title": "Example",
                    "url": "https://example.com",
                }
            ],
        }


class FakeWebClient:
    def __init__(self, content: str | bytes) -> None:
        self.content = content
        self.urls: list[str] = []

    def fetch(self, url: str) -> str | bytes:
        self.urls.append(url)
        return self.content


def test_serp_slug_and_output_path() -> None:
    path = serp_output_path(
        "Acme Analytics pricing / competitors",
        raw_root="raw",
        timestamp=1_720_000_000,
    )

    assert slugify_query("Acme Analytics pricing / competitors") == "acme_analytics_pricing_competitors"
    assert path == Path("raw/serp/acme_analytics_pricing_competitors_1720000000.json")


def test_serp_ingest_writes_structured_json_to_raw_path(tmp_path: Path) -> None:
    client = FakeSerpClient()

    output_path = ingest_serp_query(
        "Acme competitors",
        client,
        raw_root=tmp_path,
        timestamp=1_720_000_001,
    )

    assert client.queries == ["Acme competitors"]
    assert output_path == tmp_path / "serp" / "acme_competitors_1720000001.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "query": "Acme competitors",
        "results": [
            {
                "title": "Example",
                "url": "https://example.com",
            }
        ],
    }


def test_web_domain_slug_and_output_path() -> None:
    path = page_output_path(
        "https://www.example.com/pricing?ref=ad",
        raw_root="raw",
        timestamp=1_720_000_002,
    )

    assert slugify_domain("https://www.example.com/pricing?ref=ad") == "example_com"
    assert path == Path("raw/pages/example_com_1720000002.md")


def test_web_ingest_converts_html_to_markdown_friendly_text(tmp_path: Path) -> None:
    client = FakeWebClient(
        """
        <html>
          <head><title>Ignored title</title><style>.hidden{}</style></head>
          <body>
            <h1>Acme Pricing</h1>
            <p>Plans for teams.</p>
            <ul><li>Starter</li><li>Enterprise</li></ul>
            <script>alert("ignore")</script>
          </body>
        </html>
        """
    )

    output_path = ingest_web_page(
        "https://www.example.com/pricing",
        client,
        raw_root=tmp_path,
        timestamp=1_720_000_003,
    )

    assert client.urls == ["https://www.example.com/pricing"]
    assert output_path == tmp_path / "pages" / "example_com_1720000003.md"
    assert output_path.read_text(encoding="utf-8") == (
        "Ignored title\n"
        "Acme Pricing\n"
        "Plans for teams.\n"
        "- Starter\n"
        "- Enterprise\n"
    )


def test_html_to_markdown_text_accepts_bytes() -> None:
    assert html_to_markdown_text(b"<p>Hello <strong>world</strong></p>") == "Hello world"


def test_timestamp_helpers_return_unix_seconds() -> None:
    assert isinstance(serp_unix_timestamp(), int)
    assert isinstance(web_unix_timestamp(), int)
