# CompIntel Scout

## Purpose
Build a model-agnostic competitive-intelligence agent using the Karpathy second-brain pattern:
raw/ -> wiki/ -> schema

## Repo rules
- Python 3.11+
- No hardcoded secrets
- raw/ is agent-written only, never hand-edit
- wiki/ is append-only markdown
- schema/ contains JSON schema and validators
- index.md is the entity index
- log.md is append-only run history
- demo/ must stay static HTML only
- Keep provider abstraction: LLM_PROVIDER=codex|sonar|claude

## LLM Router Contract
- `LLM_PROVIDER=codex` uses `OPENAI_API_KEY` and `OPENAI_MODEL`
- `LLM_PROVIDER=sonar` uses `PERPLEXITY_API_KEY`
- `LLM_PROVIDER=claude` uses `ANTHROPIC_API_KEY`
- Synthesis code calls `LLMRouter.complete(system, user) -> str`
- Provider clients must be injectable/mockable; tests must not make live network calls

## Schema Contract
- Competitor schema fields: `slug`, `name`, `category[]`, `last_updated`, `sources[]`, `confidence`, `summary`, `products[]`, `pricing[]`, `signals[]`, `moat`, `threat_level`
- Signal schema fields: `slug`, `type`, `date`, `headline`, `source_url`, `entities[]`, `summary`
- Validate payloads before writing wiki pages or refreshing `index.md`
- Schema validation must not write files or make network calls

## Lead-Gen Agent Conventions
- `wiki/leads/`
- One subfolder per target company: `wiki/leads/{company_slug}/`
- `profile.md` stores firmographics, tech stack, buying signals, ICP fit score, and rationale.
- `contacts.md` stores role-matched contacts keyed to `wiki/roles/` slugs.
- `outreach_draft.md` stores generated personalized outreach drafts.
- Validate lead data against `schema/lead.json`.
- `wiki/roles/`
- One file per ICP role archetype.
- `role_slug` values must match the contact `role_slug` used in lead files.
- Each role file must include `pain_points`, `buying_triggers`, and `messaging_angles`.
- Seed roles include `vp_marketing`, `head_of_growth`, `cmo`, and `rev_ops`.
- `_template.md` is the canonical starting point.
- Ingest -> Lead flow
- 1. `ingest.pipeline` writes `raw/serp/` and `raw/pages/`
- 2. qualify agent reads `raw/` and writes `wiki/leads/{slug}/profile.md`
- 3. enrich agent writes `wiki/leads/{slug}/contacts.md`
- 4. outreach agent writes `wiki/leads/{slug}/outreach_draft.md`
- LLM_PROVIDER routing for lead tasks
- qualify: `sonar`
- enrich: `codex`
- outreach: `claude`

## Initial goal
Scaffold the repository structure and placeholder modules first.
Do not implement external API calls yet.

## Done when
- Repo tree exists
- Placeholder modules import cleanly
- pytest discovers tests
- README explains the architecture
- .env.example includes provider env vars
