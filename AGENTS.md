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

## Initial goal
Scaffold the repository structure and placeholder modules first.
Do not implement external API calls yet.

## Done when
- Repo tree exists
- Placeholder modules import cleanly
- pytest discovers tests
- README explains the architecture
- .env.example includes provider env vars
