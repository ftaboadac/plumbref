# [Plumbref](https://plumbref.vercel.app)

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![MCP](https://img.shields.io/badge/MCP-supported-blue)
![Local first](https://img.shields.io/badge/local--first-no%20API%20key-green)
![License](https://img.shields.io/badge/license-MIT-green)

![A plumb line suspended over a dark surface](docs/assets/plumbref-readme-hero.png)

Plumbref is a local verification harness for coding agents.

It gives agents an evidence gate: before they answer confidently, they break
the answer into claims, search the repository, read bounded source snippets,
record conservative judgments, and return an inspectable report.

Set it up once through MCP, then ask natural questions about your repository:

```text
How does the nightly account cleanup job work?
```

```text
What should we consider if we move customer_external_id from Account to AccountConnection?
```

```text
Could this code change affect downstream consumers or adjacent flows?
```

The goal is fewer "are you sure?" loops, less blind source reading, and answers
your team can check.

It exposes:

- an MCP server for agent-driven verification workflows
- a CLI for local smoke tests, debugging, and report rendering
- deterministic Markdown and JSON reports

Plumbref does not call a model API. It does not need an API key, database,
vector store, hosted service, or UI.

The intended product surface is conversational agent usage through MCP. The CLI
exists mainly as a development and validation path.

## Why A Verification Harness

Prompts and skills can ask an agent to be careful, but they do not preserve a
structured verification trail. Plumbref gates coding-agent answers against
recorded source evidence.

The agent still extracts claims and reasons over evidence. Plumbref supplies
the source-grounded workflow, budgets, redaction, status semantics, and report
artifacts.

## How It Works

- `init` writes starter config and prints MCP setup instructions.
- `doctor` checks repo root, ripgrep, config, templates, report-path
  writability, and optional MCP startup.
- MCP tools let the agent start a session, store claims, search the repo, read
  bounded snippets, record judgments, and render a report.
- Reports show the verification outcome, supported claims, too-broad claims,
  uncertain areas, source evidence, limits, and safer wording.

## Mental Model

- repository: the local codebase being checked
- question: the user's natural-language repo question
- claim: one atomic statement the agent wants to make
- evidence: bounded source snippets read from the repo
- judgment: `supported`, `too_broad`, `uncertain`, `contradicted`,
  `not_found`, or `not_verifiable`
- template: a verification playbook for a class of engineering question
- report: the source-backed trail the user can inspect

## Batteries Included

- MCP server for agent-driven verification
- CLI for setup, doctor checks, templates, smoke tests, and report rendering
- built-in templates for flow explanation, field migration, change impact,
  downstream consumers, and external integrations
- Markdown and JSON reports
- broad-claim detection for words like `only`, `always`, `never`, `all`,
  `every`, and `guarantee`
- local repository search through ripgrep
- source snippet bounds, redaction patterns, budgets, and cache metrics

## Early Dogfood Results

In real MCP runs against this repository:

- 3 sessions
- 12 claims checked
- 29 searches run
- 28 bounded evidence snippets read
- 12/12 contradiction passes on judged claims
- 3 unsupported or over-broad claims caught

Plumbref also reduced source text compared with opening every matched file, but
it does not claim to always use fewer tokens than a careful expert agent. See
[Real Workflow Test Results](docs/real-workflow-test-results.md) for the
measurement details and limitations.

## User Flow

1. Install Plumbref once.
2. Add it to your MCP-capable coding agent for a repository.
3. Ask repo questions naturally in chat.
4. The agent uses Plumbref tools behind the scenes to verify claims against
   source evidence.
5. You get a concise answer with cited files, supported claims, uncertain
   areas, and safer wording.

You should not need to manually run verification commands during normal use.

## Architecture

Plumbref is a local-first verification harness with three small layers:

- `plumbref.mcp_server` exposes the agent-facing MCP tools: start a session,
  store claims, search the repo, read bounded snippets, record judgments, and
  render reports.
- `plumbref.sessions`, `plumbref.search`, `plumbref.evidence`, and
  `plumbref.judgments` hold the verification state and enforce local budgets,
  ignored paths, snippet bounds, and conservative status rules.
- `plumbref.reports` renders deterministic Markdown and JSON reports with
  cited evidence, search traces, limits, and safe wording for scenario or
  change-impact checks.

The CLI wraps the same harness for development smoke tests. It is intentionally
not a separate product path and it does not add model-based claim extraction.

## One-Time Setup

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

Then add Plumbref to your MCP client configuration. See [MCP Setup](#mcp-setup)
for the command and JSON shape.

Fast setup from a repository checkout:

```shell
cd /path/to/repo
plumbref init
plumbref doctor
```

For agent-specific usage guidance, recommended instructions, and conversational
examples, see [Agent Usage Guide](docs/agent-usage.md).

For public-demo readiness, honest positioning, and the dogfood demo, see
[Launch Checklist](docs/launch-checklist.md).

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
default_template_id = "generic_verification"

template_paths = [
  "plumbref-template-pack",
]
```

`redaction_patterns` is accepted as an alias for `privacy_patterns`.
`template_paths` entries are resolved relative to the repository root unless
they are absolute paths.

## MCP Setup

The quickest path is to let Plumbref print the repo-specific MCP config and
agent instructions:

```shell
cd /path/to/repo
plumbref init
```

Then verify local readiness:

```shell
plumbref doctor
```

For an MCP startup check:

```shell
plumbref doctor --check-mcp-startup
```

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

## Behind-The-Scenes MCP Workflow

Users normally do not send these payloads by hand. An agent should call these
tools after you ask a natural-language repo question.

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

## Verification Templates

Templates are versioned verification playbooks. They do not encode knowledge
about one repository. They define the evidence categories, required search
passes, contradiction searches, budgets, report sections, and unchecked-area
prompts that an agent should follow for a class of engineering question.

Built-in templates:

- `generic_verification`: fallback protocol for unsupported or unusual cases
- `explain_flow`: explain how a workflow or integration works
- `field_migration`: check impact of moving or changing a field
- `change_impact`: evaluate likely downstream effects of a diff or changed file
- `downstream_consumers`: find direct and likely consumers of a contract or API
- `external_integration`: inspect vendor syncs, webhooks, pushes, pulls, and clients

List available templates:

```shell
plumbref templates --repo-root /path/to/repo
```

Inspect one template:

```shell
plumbref templates --repo-root /path/to/repo --template-id field_migration
```

Agents can start a session with a template:

```json
{
  "question": "What should we consider before moving provider_id?",
  "answer": "The field move may affect job enqueueing and payload builders.",
  "mode": "scenario",
  "template_id": "field_migration",
  "template_values": {
    "field_name": "provider_id",
    "source_owner": "CurrentOwner",
    "target_owner": "TargetOwner"
  },
  "budget_mode": "normal",
  "output_modes": ["engineer", "json"]
}
```

If no built-in template fits, use `generic_verification` or add a custom
template.

### Custom Templates

Repo-local templates live in:

```text
.plumbref/templates/
```

Shared template packs can live anywhere and be referenced with `template_paths`
in `.plumbref.toml`. Plumbref loads templates in this order:

1. built-in templates
2. user templates from `~/.config/plumbref/templates`
3. repo-local templates from `.plumbref/templates`
4. configured `template_paths`

Later sources can override earlier templates with the same ID. This lets a team
adapt a built-in playbook without forking Plumbref.

Minimal custom template:

```toml
id = "billing_webhook"
version = "1.0"
name = "Billing webhook"
description = "Verify billing webhook behavior."
modes = ["explanation", "scenario", "change_impact"]

required_claim_types = ["behavior", "api", "impact"]
required_searches = ["{webhook_name}", "{event_name}"]
contradiction_searches = ["{webhook_name} test", "{event_name} retry"]
evidence_categories = ["webhook entry point", "payload handling", "tests"]
report_sections = ["supported behavior", "unchecked areas", "safe conclusion"]
unchecked_area_prompts = ["Were retries and duplicate deliveries checked?"]

[budgets.normal]
max_claims = 8
searches_per_claim = 6
files_per_claim = 6
snippets_per_claim = 10
reference_depth = 2
```

Template placeholders are intentionally generic. The agent maps them to the
repo-specific names from the user's question or changed files, then records the
actual searches and evidence snippets in the report.

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

Claims containing absolute language such as "only", "always", "never", "all",
"every", or "guarantee" are detected automatically. They require broader
contradiction checks and explicit contradiction notes before they can be treated
as supported.

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

Reports lead with a verification outcome: whether the agent can answer from
checked evidence, must qualify the answer, or should avoid the claim as
written. They also include broad-claim findings, safer wording assembled from
supported and qualified claims, and the verification scope recorded by the
selected template. Template checks are scope markers, not a report grade.
Checks that use placeholders require concrete `template_values`; unresolved
placeholders stay outside the verified scope instead of being treated as done.

Searches are cached by query/options and repository state. Evidence snippets
are cached by file path, line range, file hash, and privacy settings, with
stable evidence IDs so repeated investigations can reuse unchanged snippets.
Cache hits and in-session evidence reuse can return compact evidence
references without repasting source text; agents can request the excerpt again
only when they need to inspect it. Reports expose cache hit, miss, reuse, and
source-text-returned metrics.

Generated reports and caches are ignored by the project `.gitignore`.

Checked-in example reports:

- [Explanation report](examples/reports/explanation.md)
- [Scenario report](examples/reports/scenario.md)
- [Change-impact report](examples/reports/change-impact.md)
- [Dogfood template-loading demo](examples/reports/plumbref-template-loading-demo.md)
- [Real MCP template-loading report](examples/reports/real-template-loading-mcp.md)
- [Real MCP template_id migration report](examples/reports/real-template-id-migration-mcp.md)
- [Real MCP onboarding change-impact report](examples/reports/real-onboarding-change-impact-mcp.md)

For aggregate measurements from the real MCP runs, see
[Real Workflow Test Results](docs/real-workflow-test-results.md).
For a sanitized external private-repo validation, see
[External Private Repo Validation](docs/external-private-repo-validation.md).

## Development CLI

The CLI is primarily for local smoke tests, debugging, and report rendering.
For normal usage, connect an MCP-capable agent to Plumbref and ask questions in
chat.

Initialize a repo and print MCP setup:

```shell
plumbref init --repo-root /path/to/repo
```

Check local readiness:

```shell
plumbref doctor --repo-root /path/to/repo
```

Run a local smoke test:

```shell
plumbref verify \
  --repo-root /path/to/repo \
  --question "What does this scheduled job do?" \
  --answer answer.md
```

The CLI does not extract claims automatically. For a full workflow, use MCP or
pass a JSON claims file with `--claims`.

## Development

See [ROADMAP.md](ROADMAP.md) for the implementation roadmap toward
source-grounded repo answers, migration checks, change-impact analysis, and
lower-token verification workflows.

Run tests:

```shell
python -m pytest
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
