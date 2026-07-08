# CompIntel Scout

CompIntel Scout is a scaffold for a model-agnostic competitive-intelligence
agent. It follows a second-brain pattern:

```text
raw/ -> wiki/ -> schema
```

The initial repository intentionally contains placeholders only. Provider
clients are abstracted, but external API calls are not implemented yet.

## Architecture

- `raw/` stores agent-written source captures. These files should not be
  hand-edited.
- `wiki/` stores append-only markdown synthesis produced from raw captures.
- `schema/` stores JSON schemas and lightweight validators for structured
  intelligence records.
- `src/compintel_scout/` contains the importable Python package, including
  configuration, pipeline placeholders, and provider abstractions.
- `src/compintel_scout/utils/config.py` loads typed settings from `.env` and
  environment variables.
- `src/compintel_scout/utils/logger.py` writes append-only run log entries in
  `[ISO8601] | ACTION | source | notes` format.
- `demo/` is static HTML only.
- `index.md` is the entity index.
- `log.md` is the append-only run history.

## Provider Abstraction

Set `LLM_PROVIDER` to choose a future backend:

```text
LLM_PROVIDER=codex|sonar|claude
```

The current implementation uses `PlaceholderLLMClient`, which raises
`NotImplementedError` for completions so no network calls are made.

## Backend Layer

`src/compintel_scout/utils/config.py` loads typed settings from `.env` and the
process environment for OpenAI, Perplexity, Anthropic, and BrightData. It only
requires credentials for the selected `LLM_PROVIDER`.

`src/compintel_scout/utils/logger.py` appends run events to `log.md` using the
public demo-friendly format `[ISO8601] | ACTION | source | notes`.

`schema/validate.py` validates competitor and signal payloads, including
file-based JSON inputs, and returns useful error messages without making any
network calls.

## Ingest Pipeline

Bright Data ingest helpers live in `src/compintel_scout/ingest/`. They accept
injectable clients so tests and demos can run without live API calls or
hardcoded secrets.

- SERP captures are stored as structured JSON at
  `raw/serp/{query_slug}_{unix_ts}.json`.
- Web page captures are stored as markdown-friendly text at
  `raw/pages/{domain}_{unix_ts}.md`.
- Bright Data credentials are loaded from `.env` or environment settings:
  `BRIGHTDATA_CUSTOMER_ID`, `BRIGHTDATA_ZONE_SERP`, `BRIGHTDATA_ZONE_WEB`,
  and `BRIGHTDATA_PASSWORD`.
- The configured Bright Data clients can make live requests, while tests and
  demos can still pass injected clients to avoid network calls.

### Live ingest

Create a local `.env` with your Bright Data credentials:

```text
BRIGHTDATA_CUSTOMER_ID=your_customer_id
BRIGHTDATA_PASSWORD=your_zone_password
BRIGHTDATA_ZONE_SERP=your_serp_zone
BRIGHTDATA_ZONE_WEB=your_web_unlocker_zone
```

`BRIGHTDATA_API_KEY` is also supported for Bright Data direct API access. If it
is omitted, CompIntel Scout uses Bright Data's documented proxy-style access
with customer ID, zone, and password.

Run one live ingest cycle:

```bash
PYTHONPATH=src python -m compintel_scout.ingest.pipeline --query "Salesforce Q2 2026 roadmap" --url "https://www.salesforce.com"
```

This writes a SERP JSON file to `raw/serp/{query_slug}_{unix_ts}.json` and a
markdown-friendly page capture to `raw/pages/{domain}_{unix_ts}.md`.

### Live ingest succeeded

Observed output files from a successful live run:

- `raw/serp/salesforce_q2_2026_roadmap_1783549135.json`
- `raw/pages/salesforce_com_1783549138.md`

## Provider Routing

`src/compintel_scout/synthesize/llm_router.py` selects the configured
`LLM_PROVIDER` and exposes a unified `LLMRouter.complete(system, user) -> str`
interface. The default client is a no-network placeholder; tests and future
provider modules inject clients behind the same interface.

Provider configuration:

- `LLM_PROVIDER=codex` uses `OPENAI_API_KEY` and `OPENAI_MODEL`.
- `LLM_PROVIDER=sonar` uses `PERPLEXITY_API_KEY`.
- `LLM_PROVIDER=claude` uses `ANTHROPIC_API_KEY`.

Unknown providers and missing provider-specific keys raise clear errors before
any completion call is attempted.

## Pipeline Flow

`src/compintel_scout/ingest/pipeline.py` runs the local second-brain flow:
load a raw JSON object, validate it, write or append a wiki page, rebuild
`index.md`, and append structured entries to `log.md`.

```python
from compintel_scout.ingest.pipeline import run_local_pipeline

run_local_pipeline("raw/sample_competitor.json")
```

Competitor pages are written under `wiki/competitors/`, market pages under
`wiki/markets/`, and signal pages under `wiki/signals/`. The index is rebuilt
with Competitors, Markets, and Signals sections while `log.md` remains
append-only.

## CompIntel Scout -> Enso Lead Gen

CompIntel Scout is Enso Labs' second-brain for competitive and market
intelligence. The `raw -> wiki -> schema` pattern becomes the research spine
for lead generation workflows.

- `wiki/leads/` stores enriched lead profiles, ICP fit scores, contacts, and
  outreach drafts.
- `wiki/roles/` stores buyer archetypes, pain points, and messaging angles.
- Three agent layers sit on top of Scout:
  1. Qualify Agent
  2. Enrich Agent
  3. Outreach Agent
- Perplexity Sonar acts as the live web-grounded enrichment layer for recency
  and synthesis, while Bright Data remains the raw acquisition layer.

## Demo

Run the 60-second hackathon demo:

1. Open `demo/dashboard.html` directly in a browser; no server or build step is
   required.
2. Start with the hero and pipeline overview: BrightData evidence lands in
   `raw/`, synthesis routes through `LLM_PROVIDER`, schemas gate writes, then
   `index.md` and `log.md` make the run navigable.
3. Scan the competitors, signals, index summary, and log snippet to see how the
   local second brain becomes production-ready: swap in live BrightData clients,
   inject real provider clients behind `LLMRouter`, and keep the same
   validation/index/log surfaces.

### Judge flow

1. Inspect `raw/serp/` for live Bright Data SERP captures, including `raw/serp/salesforce_q2_2026_roadmap_1783549135.json`.
2. Inspect `raw/pages/` for live Bright Data Web Unlocker page captures, including `raw/pages/salesforce_com_1783549138.md`.
3. Inspect `log.md` and `index.md` to verify append-only run history and navigable entity index surfaces.
4. Open `demo/dashboard.html` to see the end-to-end `raw -> wiki -> schema -> index -> log` story in one static view.

## Schema

The `schema/` package includes competitor and signal JSON schemas plus a
dependency-free validator. Payloads are checked before wiki pages or index
updates are written.

Competitor objects require:

```text
slug, name, category[], last_updated, sources[], confidence, summary,
products[], pricing[], signals[], moat, threat_level
```

Signal objects require:

```text
slug, type, date, headline, source_url, entities[], summary
```

```python
from schema.validate import validate_competitor, validate_signal

competitor = validate_competitor(payload)
```

`validate_competitor()` and `validate_signal()` return a validated `dict` or
raise `SchemaValidationError` with field-specific messages. Lower-level helpers
such as `validate_payload()` and `validate_json_file()` return a
`ValidationResult` for test and CLI-style workflows.

## Development

This project targets Python 3.11 or newer.

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The scaffold is considered healthy when package imports work and pytest
discovers the test suite.
