# [Plumbref](https://plumbref.vercel.app)

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![MCP](https://img.shields.io/badge/MCP-supported-blue)
![Local first](https://img.shields.io/badge/local--first-no%20API%20key-green)
![License](https://img.shields.io/badge/license-MIT-green)

![A plumb line suspended over a dark surface](docs/assets/plumbref-readme-hero.png)

Plumbref helps coding agents check risky repo claims before you rely on them.

It gives coding agents a report gate: before you repeat or act on an answer,
the agent breaks it into claims, checks local repository evidence, and returns
what is supported by checked source lines, what needs qualification, what not
to rely on, and the source lines behind that call. When the answer is risky,
qualified, or explicitly requested, Plumbref also writes an inspectable report.

Ask natural reliance-check questions about your repository:

```text
The agent said this only affects onboarding. Check that.
```

```text
Can I tell support that SSO only depends on Okta?
```

```text
The agent says this field is safe to rename. What is actually supported?
```

The goal is to replace vague "are you sure?" loops with source-backed reliance
decisions your team can inspect.

Plumbref is local-first. It does not call a model API, require an API key,
upload your repository, use a database, depend on a vector store, or run a
hosted service.

## Trust Boundary

Plumbref does not independently determine truth. The coding agent still
extracts claims, chooses searches, reads evidence, and records judgments.
Plumbref structures that workflow, stores the evidence trail, applies template
and strict-gate checks, and downgrades answers when required recorded checks
are missing.

Treat `supported` as "supported by the cited local evidence and recorded
checks," not as a guarantee about every deployment, runtime state, or external
system.

## Why

Prompts and skills can ask an agent to be careful, but they often produce more
prose when you ask "are you sure?" Plumbref gates coding-agent answers against
recorded source evidence and turns them into safe-to-rely-on statements with
explicit limits.

The agent still extracts claims and reasons over evidence. Plumbref supplies
the source-grounded workflow, budgets, redaction, status semantics, and report
artifacts.

## How It Works

1. Install Plumbref once.
2. Add it to your MCP-capable coding agent for a repository.
3. Ask repo questions naturally in chat.
4. The agent uses Plumbref tools to check claims against source evidence.
5. You get a concise answer with safe-to-rely-on claims, qualified claims,
   do-not-rely-on claims, evidence locations, unchecked areas, and safer wording.

Example inline answer shape:

```text
Safe to rely on:
- The checked function rewrites the report label from "items" to "records".

Say with qualification:
- too_broad: The change only affects formatting.

Safer wording:
- The checked function changes report-label wording, but downstream exports were
  not fully traced.

Evidence:
- `src/reports/labels.ts:41-58`

Unchecked:
- Conflicting-code-path search not recorded: generated client exports.
```

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
- broad-claim detection for phrases like `only`, `safe to`, `no downstream`,
  `always`, `never`, `all`, `every`, and `guarantee`
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
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
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

MCP clients that support stdio servers can launch Plumbref with:

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

For the current first-run proof path, see
[examples/first-run](examples/first-run/). It includes captured Codex CLI
transcripts, real Plumbref MCP tool calls, inline answers, generated report
paths, and a careful-prompt-plus-`rg` baseline.

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
.cache/plumbref/reports/YYYY-MM-DD/
```

Reports are local generated receipts. They are intentionally stored under
`.cache` so they stay out of normal source control and can be deleted without
changing the project.

By default, `report_policy = "on_demand"` writes report files only when the
user asks for a report or when the result has risk, uncertainty, qualifications,
change impact, or broad/absolute language. Low-risk supported answers can stay
inline in chat without creating report files. Set `report_policy = "manual"` to
write reports only when explicitly forced, or `report_policy = "always"` to
write one for every rendered Plumbref result.

Written reports lead with a verification outcome: whether the claim is safe to
rely on from checked evidence, needs qualification, or should not be relied on
as written. They also include broad-claim findings, safer wording, cited
evidence, search traces, limits, and cache metrics.
`.cache/plumbref/reports/index.json` tracks reports that were actually written.

MCP render responses include `inline_answer`: the chat-shaped answer agents
should return by default. It summarizes what is safe to rely on, what needs
qualification, what not to rely on, safer wording, evidence locations,
unchecked areas, and verification counts. Markdown and JSON reports are the
inspectable receipt behind that answer, not the primary user-facing surface.

Agents can compare two JSON reports for the same question through the MCP
`plumbref_diff_reports` tool. The tool returns structured claim changes plus a
Markdown diff, so the agent can summarize what changed inline in chat.

For local debugging, the same diff renderer is available through the CLI:

```shell
plumbref diff-reports old-report.json new-report.json --output report-diff.md
```

The diff shows claim status changes, evidence-only changes, added claims,
removed claims, and unchanged claims. New reports include stable claim IDs for
this workflow; older reports can be compared by claim order as a fallback.

Searches are cached by query/options and repository state. Evidence snippets
are cached by file path, line range, file hash, and privacy settings. Cache
hits and in-session evidence reuse can return compact evidence references
without repasting source text.

Current demo artifacts:

- [First-run SSO fixture](examples/first-run/)
- [Customer exports benchmark](examples/first-run/benchmark-and-user-validation.md)
- [SSO business-rule drift diff](examples/reports/sso-eligibility-drift-diff.md)

Historical dogfood reports live in [examples/reports](examples/reports/).
They are useful for seeing report shape and earlier product exploration, but
some line references and quoted README wording may be stale. Do not treat them
as current proof until they are regenerated.

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

The current public benchmark shows the same pattern more concretely: careful
prompting plus `rg` can answer the controlled fixtures correctly, while
Plumbref adds structured claim state, contradiction-pass records, durable
Markdown/JSON reports, and rerunnable evidence trails. Do not use the current
fixtures to claim Plumbref is more correct than a careful agent.

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
report_policy = "on_demand"
template_paths = ["plumbref-template-pack"]
```

`redaction_patterns` is accepted as an alias for `privacy_patterns`.
`template_paths` entries are resolved relative to the repository root unless
they are absolute paths.

## Development

Run tests:

```shell
python3 -m pytest
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
