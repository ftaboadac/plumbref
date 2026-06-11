# [Plumbref](https://plumbref.vercel.app)

Plumbref verifies AI coding-agent claims against source references.

It exposes:

- an MCP server for agent-driven verification workflows
- a CLI for local smoke tests and report rendering
- deterministic Markdown and JSON reports

Plumbref does not call a model API. It does not need an API key, database,
vector store, hosted service, or UI.

## Why A Harness

Prompts and skills can ask an agent to be careful, but they do not preserve a
structured verification trail. Plumbref gives the agent a small protocol:

1. start a verification session
2. store atomic claims or predicted outcomes
3. search the repository
4. read bounded evidence snippets
5. record conservative judgments
6. render a report

The agent still extracts claims and reasons over evidence. Plumbref supplies
the source-grounded workflow, budgets, redaction, status semantics, and report
artifacts.

## Install

Install the latest published package:

```shell
pipx install plumbref
```

Install directly from GitHub:

```shell
pipx install git+https://github.com/ftaboadac/plumbref.git
```

For local development:

```shell
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

Plumbref uses `rg`/ripgrep for repository search:

```shell
rg --version
```

## CLI

Run the MCP server against a repository:

```shell
plumbref mcp --repo-root /path/to/repo
```

Run a local verification smoke test:

```shell
plumbref verify \
  --repo-root /path/to/repo \
  --question "What does this scheduled job do?" \
  --answer answer.md
```

Use a config file:

```shell
plumbref verify \
  --repo-root /path/to/repo \
  --config /path/to/plumbref.toml \
  --question "What happens if provider_id is missing?" \
  --answer answer.md
```

Explicit modes are available:

```shell
plumbref verify \
  --repo-root /path/to/repo \
  --mode scenario \
  --scenario "run_scheduled_job receives provider_id=None" \
  --budget-mode normal \
  --output-mode engineer \
  --output-mode json \
  --question "What happens if provider_id is missing?" \
  --answer answer.md
```

For change-impact checks:

```shell
plumbref verify \
  --repo-root /path/to/repo \
  --mode change_impact \
  --changed-file app/reports.py \
  --question "What does this change affect?" \
  --answer impact.md
```

The CLI does not extract claims automatically. For a full workflow, use MCP or
pass a JSON claims file with `--claims`.

## Config

Config discovery order:

1. explicit `--config`
2. `<repo-root>/.plumbref.local.toml`
3. `<repo-root>/.plumbref.toml`
4. `~/.config/plumbref/config.toml`

Example:

```toml
ignored_paths = [
  ".git",
  ".venv",
  "node_modules",
  ".cache",
]

privacy_patterns = [
  "AKIA[0-9A-Z]{16}",
  "(?i)(api[_-]?key|secret|token|password)\\s*[:=]\\s*['\\\"][^'\\\"]+['\\\"]",
]

default_budget_mode = "normal"
default_output_modes = ["engineer", "json"]
```

`redaction_patterns` is accepted as an alias for `privacy_patterns`.

## MCP Setup

Plumbref is a stdio MCP server. Any MCP-capable client can launch it with:

```shell
plumbref mcp --repo-root /path/to/repo
```

Cursor-style MCP config:

```json
{
  "mcpServers": {
    "plumbref": {
      "command": "plumbref",
      "args": ["mcp", "--repo-root", "/path/to/repo"]
    }
  }
}
```

With explicit config:

```json
{
  "mcpServers": {
    "plumbref": {
      "command": "plumbref",
      "args": [
        "mcp",
        "--repo-root",
        "/path/to/repo",
        "--config",
        "/path/to/repo/.plumbref.toml"
      ]
    }
  }
}
```

Claude Code, Codex, and other MCP clients generally use the same command/args
shape for stdio servers. Use the client-specific location for MCP server
configuration and point it at the same command.

## MCP Workflow

Start a session:

```json
{
  "question": "What does this scheduled job do?",
  "answer": "The scheduled job queues provider sync work when provider_id is present.",
  "mode": "explanation",
  "budget_mode": "normal",
  "output_modes": ["engineer", "json"]
}
```

Store claims extracted by the agent:

```json
{
  "claims": [
    {
      "text": "The scheduled job queues provider sync work when provider_id is present.",
      "claim_type": "behavior",
      "risk": "medium"
    }
  ]
}
```

Then search, read evidence, record a judgment, and render the report with the
MCP tools exposed by the server.

## Explanation Mode

Use explanation mode for claims about current source behavior.

Question:

```text
What does this scheduled job do?
```

Claim:

```json
{
  "text": "The scheduled job queues provider sync work when provider_id is present.",
  "claim_type": "behavior",
  "risk": "medium"
}
```

Plumbref should mark it `supported` only when the agent cites source lines
that show the queued path and has checked for relevant contradictions.

## Scenario Mode

Use scenario mode for predicted outcomes.

Question:

```text
What happens if provider_id is missing?
```

Start payload:

```json
{
  "mode": "scenario",
  "scenario": "run_scheduled_job receives provider_id=None.",
  "question": "What happens if provider_id is missing?",
  "answer": "The scheduled job is skipped.",
  "output_modes": ["engineer", "json"]
}
```

Predicted outcome claim:

```json
{
  "text": "run_scheduled_job returns skipped when provider_id is missing.",
  "expected_outcome": "The scheduled job is skipped.",
  "assumptions": ["provider_id is None."],
  "claim_type": "behavior",
  "risk": "medium"
}
```

## Change-Impact Mode

Use change-impact mode to verify a factual impact statement against changed
files, a diff, or a local git diff target.

Question:

```text
This change only affects report wording.
```

Start payload:

```json
{
  "mode": "change_impact",
  "question": "What does this change affect?",
  "answer": "This change only affects report wording.",
  "budget_mode": "normal",
  "output_modes": ["engineer", "json"]
}
```

Record explicit changed files:

```json
{
  "source": "files",
  "changed_files": ["app/reports.py"],
  "changed_symbols": [
    {
      "name": "render_report_title",
      "kind": "function",
      "file": "app/reports.py"
    }
  ]
}
```

Claims containing absolute language such as "only", "always", or "never"
require broader contradiction searches before they can be treated as supported.

## Status Semantics

- `supported`: cited source evidence supports the claim as written, and a
  contradiction pass was recorded.
- `too_broad`: evidence supports a narrower or qualified version, but not the
  claim as written.
- `uncertain`: relevant evidence exists, but it is insufficient for a confident
  judgment.
- `contradicted`: source evidence conflicts with the claim.
- `not_found`: searches did not find relevant evidence.
- `not_verifiable`: the claim cannot be verified from local source evidence.

## Reports And Cache

By default, reports are written under:

```text
.cache/plumbref/reports/
```

Generated reports and caches are ignored by the project `.gitignore`.

## Development

Run tests:

```shell
pytest
```

Run lint:

```shell
ruff check .
```

## Limitations

- Plumbref does not extract claims by itself.
- Plumbref does not decide truth with an LLM.
- Plumbref cannot verify claims that require production data, private
  services, or external systems unless the relevant evidence exists in the
  local repository.
- Plumbref search is lexical and repo-local.
- `supported` means supported by the cited source evidence, not globally true
  for every deployment or runtime state.

## Non-Goals

- no model API dependency
- no hosted service
- no database
- no vector store
- no UI
- no automatic code review replacement
- no production-data inspection
