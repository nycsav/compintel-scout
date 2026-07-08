"""Raw-layer ingestion helpers."""

from compintel_scout.ingest.brightdata_serp import (
    SerpClient,
    ingest_serp_query,
    serp_output_path,
    slugify_query,
)
from compintel_scout.ingest.brightdata_web import (
    WebClient,
    html_to_markdown_text,
    ingest_web_page,
    page_output_path,
    slugify_domain,
)
from compintel_scout.ingest.pipeline import PipelineError, PipelineResult, run_local_pipeline

__all__ = [
    "PipelineError",
    "PipelineResult",
    "SerpClient",
    "WebClient",
    "html_to_markdown_text",
    "ingest_serp_query",
    "ingest_web_page",
    "page_output_path",
    "serp_output_path",
    "slugify_domain",
    "slugify_query",
    "run_local_pipeline",
]
