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

## Ingest Layer

Bright Data ingest helpers live in `src/compintel_scout/ingest/`. They accept
injectable clients so tests and demos can run without live API calls or
hardcoded secrets.

- SERP captures are stored as structured JSON at
  `raw/serp/{query_slug}_{unix_ts}.json`.
- Web page captures are stored as markdown-friendly text at
  `raw/pages/{domain}_{unix_ts}.md`.

## Provider Routing

`src/compintel_scout/synthesize/llm_router.py` selects the configured
`LLM_PROVIDER` and returns a no-network placeholder client. `codex` requires
`OPENAI_API_KEY` and `OPENAI_MODEL`, `sonar` requires `PERPLEXITY_API_KEY`,
and `claude` requires `ANTHROPIC_API_KEY`.

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

## Demo

Open `demo/dashboard.html` directly in a browser for a static hackathon
dashboard. It uses sample local-run data and links to generated `wiki/`,
`index.md`, and `log.md` artifacts when they exist.

## Schema Validation

The `schema/` package includes competitor and signal JSON schemas plus a
dependency-free validator:

```python
from schema.validate import validate_competitor, validate_signal
```

Validation returns a `ValidationResult` with `valid` and `errors` fields.

## Development

This project targets Python 3.11 or newer.

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The scaffold is considered healthy when package imports work and pytest
discovers the test suite.
