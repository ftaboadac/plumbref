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

Ask natural questions about your repository:

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

Plumbref is local-first. It does not call a model API, require an API key,
upload your repository, use a database, depend on a vector store, or run a
hosted service.

## Why

Prompts and skills can ask an agent to be careful, but they do not preserve a
structured verification trail. Plumbref gates coding-agent answers against
recorded source evidence.

The agent still extracts claims and reasons over evidence. Plumbref supplies
the source-grounded workflow, budgets, redaction, status semantics, and report
artifacts.

## How It Works

1. Install Plumbref once.
2. Add it to your MCP-capable coding agent for a repository.
3. Ask repo questions naturally in chat.
4. The agent uses Plumbref tools to verify claims against source evidence.
5. You get a concise answer with cited files, supported claims, uncertain
   areas, limits, and safer wording.

You should not need to manually run verification commands during normal use.
The CLI exists mainly for setup, smoke tests, debugging, and report rendering.

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

## Install

Install the latest published package:

```shell
pipx install plumbref
```

Or install directly from GitHub:

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

## Quick Start

From the repository you want an agent to verify:

```shell
cd /path/to/repo
plumbref init
plumbref doctor
```

`plumbref init` prints repo-specific MCP configuration and recommended agent
instructions. `plumbref doctor` checks local readiness: repo root, ripgrep,
config loading, templates, report-path writability, and optional MCP startup.

Any MCP-capable client can launch Plumbref as a stdio server:

```shell
plumbref mcp --repo-root /path/to/repo
```

Example MCP config:

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

For agent-specific usage guidance and conversational examples, see
[Agent Usage Guide](docs/agent-usage.md).

## Templates

Templates are versioned verification playbooks. They define evidence
categories, required search passes, contradiction searches, budgets, report
sections, and unchecked-area prompts for a class of engineering question.

Built-in templates:

- `generic_verification`: fallback protocol for unsupported or unusual cases
- `explain_flow`: explain how a workflow or integration works
- `field_migration`: check impact of moving or changing a field
- `change_impact`: evaluate likely downstream effects of a diff or changed file
- `downstream_consumers`: find direct and likely consumers of a contract or API
- `external_integration`: inspect vendor syncs, webhooks, pushes, pulls, and clients

List templates:

```shell
plumbref templates --repo-root /path/to/repo
```

Inspect one template:

```shell
plumbref templates --repo-root /path/to/repo --template-id field_migration
```

Custom templates can live in `.plumbref/templates/`, in
`~/.config/plumbref/templates/`, or in shared template-pack directories listed
in `template_paths`. Later sources can override earlier templates with the same
ID, so teams can adapt a built-in playbook without forking Plumbref.

## Reports And Cache

Reports are written under:

```text
.cache/plumbref/reports/
```

Reports lead with a verification outcome: whether the agent can answer from
checked evidence, must qualify the answer, or should avoid the claim as
written. They also include broad-claim findings, safer wording, cited evidence,
search traces, limits, and cache metrics.

Searches are cached by query/options and repository state. Evidence snippets
are cached by file path, line range, file hash, and privacy settings. Cache
hits and in-session evidence reuse can return compact evidence references
without repasting source text.

Checked-in example reports:

- [Dogfood template-loading demo](examples/reports/plumbref-template-loading-demo.md)
- [Real MCP template-loading report](examples/reports/real-template-loading-mcp.md)
- [Real MCP template_id migration report](examples/reports/real-template-id-migration-mcp.md)
- [Real MCP onboarding change-impact report](examples/reports/real-onboarding-change-impact-mcp.md)

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

## Config

Config discovery order:

1. explicit `--config`
2. `<repo-root>/.plumbref.local.toml`
3. `<repo-root>/.plumbref.toml`
4. `~/.config/plumbref/config.toml`

Minimal example:

```toml
ignored_paths = [".git", ".venv", "node_modules", ".cache"]
privacy_patterns = [
  "(?i)(api[_-]?key|secret|token|password)\\s*[:=]\\s*['\\\"][^'\\\"]+['\\\"]",
]

default_budget_mode = "normal"
default_output_modes = ["engineer", "json"]
default_template_id = "generic_verification"
template_paths = ["plumbref-template-pack"]
```

`redaction_patterns` is accepted as an alias for `privacy_patterns`.
`template_paths` entries are resolved relative to the repository root unless
they are absolute paths.

## Development

Run tests:

```shell
python -m pytest
```

Run lint:

```shell
ruff check .
```

See [ROADMAP.md](ROADMAP.md) for the implementation roadmap. For public-demo
readiness and honest positioning, see [Launch Checklist](docs/launch-checklist.md).

## Limitations

- Plumbref does not extract claims by itself.
- Plumbref does not decide truth with an LLM.
- Plumbref search is lexical and repo-local.
- `supported` means supported by the cited source evidence, not globally true
  for every deployment or runtime state.
- Plumbref cannot verify claims that require production data, private
  services, or external systems unless the relevant evidence exists in the
  local repository.

## Non-Goals

- no model API dependency
- no hosted service
- no database
- no vector store
- no UI
- no automatic code review replacement
- no production-data inspection
