"""Bright Data Web Unlocker raw page ingestion helpers."""

from __future__ import annotations

import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse


class WebClient(Protocol):
    """Minimal client interface for raw page responses."""

    def fetch(self, url: str) -> str | bytes:
        """Return raw HTML or text content for a URL."""


def unix_timestamp() -> int:
    """Return the current Unix timestamp in seconds."""
    return int(time.time())


def slugify_domain(url_or_domain: str) -> str:
    """Convert a URL or domain into a stable filename slug."""
    parsed = urlparse(url_or_domain)
    if not parsed.netloc:
        parsed = urlparse(f"//{url_or_domain}")

    domain = (parsed.hostname or url_or_domain).lower()
    if domain.startswith("www."):
        domain = domain[4:]
    slug = re.sub(r"[^a-z0-9]+", "_", domain)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "page"


def page_output_path(
    url_or_domain: str,
    *,
    raw_root: str | Path = "raw",
    timestamp: int | None = None,
) -> Path:
    """Return `raw/pages/{domain}_{unix_ts}.md` for a page."""
    unix_ts = unix_timestamp() if timestamp is None else timestamp
    return Path(raw_root) / "pages" / f"{slugify_domain(url_or_domain)}_{unix_ts}.md"


def html_to_markdown_text(content: str | bytes) -> str:
    """Convert raw HTML or text into markdown-friendly text."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    parser = _MarkdownTextParser()
    parser.feed(content)
    parser.close()
    text = parser.text()
    if text:
        return text
    return _normalize_text(content)


def ingest_web_page(
    url: str,
    client: WebClient,
    *,
    raw_root: str | Path = "raw",
    timestamp: int | None = None,
) -> Path:
    """Fetch a page and store markdown-friendly text in the raw layer."""
    content = client.fetch(url)
    output_path = page_output_path(url, raw_root=raw_root, timestamp=timestamp)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_to_markdown_text(content) + "\n", encoding="utf-8")
    return output_path


class _MarkdownTextParser(HTMLParser):
    block_tags = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "section",
        "table",
        "tr",
        "ul",
    }

    ignored_tags = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.ignored_tags:
            self._ignored_depth += 1
            return
        if tag in self.block_tags:
            self._newline()
        if tag == "li":
            self._parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if tag in self.block_tags:
            self._newline()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        normalized = _normalize_inline(data)
        if normalized:
            if self._needs_inline_space():
                self._parts.append(" ")
            self._parts.append(normalized)

    def text(self) -> str:
        return _normalize_markdown("".join(self._parts))

    def _newline(self) -> None:
        if self._parts and not self._parts[-1].endswith("\n"):
            self._parts.append("\n")

    def _needs_inline_space(self) -> bool:
        if not self._parts:
            return False
        previous = self._parts[-1]
        return bool(previous and not previous.endswith((" ", "\n", "- ")))


def _normalize_inline(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_text(value: str) -> str:
    lines = [_normalize_inline(line) for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_markdown(value: str) -> str:
    lines = [_normalize_inline(line) for line in value.splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines)
