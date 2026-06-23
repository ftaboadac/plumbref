# Agent Usage Guide

Plumbref is intended to run behind a coding agent through MCP. The user should
ask normal repository questions in chat; the agent should use Plumbref tools to
check risky codebase claims before the user relies on them. The primary output
is a bounded, source-backed inline answer that says what checked evidence
supports, what needs qualification, what not to rely on, and what source lines
were checked. A Markdown report is the inspectable receipt when the answer is
risky, qualified, or explicitly requested.

Plumbref is not an independent truth oracle. The coding agent still extracts
claims, chooses searches, and records judgments; Plumbref stores the trail and
downgrades answers when the recorded checks are incomplete.

This guide is written for Codex, Claude Code, Cursor, and other MCP-capable
coding agents. The examples are intentionally generic and avoid company- or
product-specific workflows.

## MCP Setup

Install Plumbref once:

```shell
pipx install plumbref
```

For local development from a checkout:

```shell
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

Plumbref uses ripgrep for local repository search:

```shell
rg --version
```

Add Plumbref as a stdio MCP server for the repository:

```shell
plumbref mcp --repo-root /path/to/repo
```

The easiest setup path is:

```shell
cd /path/to/repo
plumbref init
plumbref doctor
```

`plumbref init` creates a starter `.plumbref.toml` if one does not already
exist, prints copy-paste MCP JSON, and prints the recommended agent
instructions. `plumbref doctor` checks local readiness: repo root, ripgrep,
config loading, template loading, and report-path writability.

Generic MCP server config:

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

With an explicit config file:

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

The server command is the same for most MCP clients. The config file format and
location are client-specific.

### Codex

Codex reads MCP servers from `~/.codex/config.toml`. Add one server per repo:

```toml
[mcp_servers.plumbref]
command = "plumbref"
args = ["mcp", "--repo-root", "/path/to/repo"]
startup_timeout_sec = 120
```

For a local development checkout where `plumbref` is not on `PATH`, point to
the virtualenv executable:

```toml
[mcp_servers.plumbref]
command = "/path/to/plumbref/.venv/bin/python"
args = ["-m", "plumbref", "mcp", "--repo-root", "/path/to/repo"]
startup_timeout_sec = 120
```

Restart Codex or reload the workspace after editing the config. Then ask:

```text
The agent said SSO only depends on Okta. Check that before I tell support.
Use Plumbref and return the inline answer.
```

The expected first-run shape is in
[`examples/first-run/README.md`](../examples/first-run/README.md). That example
includes a stdio transcript fixture, but it is not yet a captured live
Codex/Claude/Cursor client transcript.

### Troubleshooting

| Symptom | Check |
| --- | --- |
| Client cannot see Plumbref tools | Confirm the config file location and restart/reload the client. |
| MCP server exits on startup | Run `plumbref doctor --repo-root /path/to/repo --check-mcp-startup`. |
| `plumbref` command is not found | Use the virtualenv form above or install with `pipx install plumbref`. |
| Agent gives an answer without Plumbref | Add the agent instructions below and explicitly say "Use Plumbref". |
| Report path is missing | Check `report_policy`; low-risk supported answers may stay inline only. |
| Answer says checks are missing | Inspect `Unchecked` and rerun with the missing search/category. |

## Agent Instructions

Use this as a recommended agent instruction block:

```text
When a user may rely on an AI answer about repository behavior, migration risk,
downstream consumers, or change impact, use Plumbref through MCP before giving
a confident answer.

Trigger Plumbref explicitly when the user says things like "audit that",
"check that with Plumbref", "can I rely on this", "what can I safely say", or
"run this before I send/merge". Also use it automatically for risky claims that
use wording such as only, safe to, no downstream, always, never, all, every, or
guarantee.

Workflow:
1. Choose the closest Plumbref template. Use generic_verification if no
   specialized template fits.
2. Start a Plumbref session with the user's question, the draft answer or
   hypothesis, the verification mode, budget mode, selected template_id, and
   concrete template_values for placeholders such as flow_name, field_name,
   changed_file, or changed_symbol.
3. Break the draft answer into atomic claims. Avoid bundling multiple behaviors
   into one claim.
4. Search narrowly for each claim using the template's required searches.
5. Run contradiction searches before marking a claim supported, especially when
   the wording uses only, safe to, no downstream, always, never, all, none, or
   guarantees. For broad claims, run the first-order checks needed to answer
   the claim as written before returning: changed files, non-doc/code changes,
   direct callers/references, relevant tests, and obvious docs/config references.
6. Read bounded snippets only around relevant source lines. Tag snippets with
   the closest template evidence_category when possible. Cache hits and reused
   evidence may return compact references; ask for include_excerpt=true only
   when source text needs to be inspected again.
7. Record conservative judgments. Use supported only when cited evidence
   supports the claim as written and a contradiction pass was completed. For
   too-broad, contradicted, uncertain, not-found, or not-verifiable claims,
   provide safer_wording when there is wording the user can rely on instead.
8. Render the Plumbref result. Return the `inline_answer` in chat by default.
   Let `report_policy` decide whether report files should be written, unless
   the user explicitly asks for a report.

Answering rules:
- Prefer cited source evidence over confidence.
- Say what was not checked.
- Do not leave the obvious check unchecked when it is required to answer the
  user's actual reliance question.
- Use the report's answer gate: say what is safe to rely on from checked
  evidence, qualify too-broad claims, and do not rely on contradicted or
  unverifiable parts.
- Keep normal answers inline with `inline_answer`. Mention report paths only
  when a report was written because the user asked, the answer is risky, or
  the answer needs qualifications.
- If the repo is too large for the current budget, say the result is bounded by
  that budget and suggest a deeper pass.
- Treat supported as supported by checked evidence, not globally true.
- Do not claim global truth from local snippets.
- Do not use Plumbref to inspect production data or external systems.
```

For low-risk exploratory questions, use `budget_mode="fast"`. For normal
engineering answers, use `budget_mode="normal"`. Use `budget_mode="deep"` when
the question has broad impact, external contracts, data movement, or absolute
language.

Valid verification modes are `explanation`, `scenario`, and `change_impact`.
The MCP server also accepts common first-run aliases such as `verify`,
`verification`, and `explain_flow` for `explanation`.

Valid output modes are `engineer`, `support`, and `json`. The MCP server also
accepts `inline_answer`, `inline`, `answer`, `report`, and `markdown` as
aliases for `engineer`, because agents often ask for the chat-shaped answer or
report surface rather than the internal renderer name.

Valid judgment statuses are `supported`, `contradicted`, `uncertain`,
`too_broad`, `not_found`, and `not_verifiable`. The MCP server accepts common
aliases conservatively: for example, `refuted` maps to `contradicted`, while
`partially_supported` maps to `uncertain`.

Valid claim types are `definition`, `behavior`, `api`, `ui`, `business_rule`,
`impact`, `recommendation`, and `unknown`. The MCP server accepts common
claim-type guesses such as `data_outputs` and maps them to `behavior`.

## Template Selection

Use these defaults:

| User intent | Template | Mode |
| --- | --- | --- |
| "How does this workflow work?" | `explain_flow` | `explanation` |
| "What happens if this condition changes?" | `generic_verification` or a closer custom template | `scenario` |
| "What if we move or rename this field?" | `field_migration` | `scenario` |
| "Could this diff affect anything else?" | `change_impact` | `change_impact` |
| "Who consumes this API, event, model, or job?" | `downstream_consumers` | `explanation` or `change_impact` |
| "How does this vendor/webhook/API integration behave?" | `external_integration` | `explanation` |
| "This use case is not covered." | `generic_verification` | best matching mode |

Custom templates can live in `.plumbref/templates/`, in
`~/.config/plumbref/templates/`, or in shared template-pack directories listed
in `template_paths`.

## MCP Workflow Examples

Users do not need to send these payloads manually. These examples show what an
agent should do behind the scenes.

### Explain Flow

User:

```text
How does the nightly account cleanup job decide what to delete?
```

Agent starts:

```json
{
  "question": "How does the nightly account cleanup job decide what to delete?",
  "answer": "The cleanup job deletes inactive accounts after checking retention rules.",
  "mode": "explanation",
  "template_id": "explain_flow",
  "template_values": {
    "flow_name": "nightly account cleanup",
    "entry_point": "cleanup job",
    "main_entity": "account"
  },
  "budget_mode": "normal",
  "output_modes": ["engineer", "json"]
}
```

Agent then:

- stores atomic claims about entry points, retention checks, deletion behavior,
  and failure handling
- searches for the job name, entry point, retention rule names, and tests
- reads bounded snippets for the job path and relevant tests
- runs contradiction searches for disabled paths, dry-run behavior, and error
  handling
- records judgments and renders the result

The returned `inline_answer` is suitable for chat, for example:

```text
Plumbref found source support for the cleanup entry point and retention check.
Deletion behavior is supported for inactive accounts matching the shown rule.
Retry behavior was not found in the checked files, so that part remains
uncertain. See the report for cited snippets and searches.
```

### Field Migration

User:

```text
What should we consider before moving customer_external_id from Account to
AccountConnection?
```

Agent starts:

```json
{
  "question": "What should we consider before moving customer_external_id from Account to AccountConnection?",
  "answer": "The move may affect direct reads, writes, API payloads, migrations, and tests.",
  "mode": "scenario",
  "template_id": "field_migration",
  "template_values": {
    "field_name": "customer_external_id",
    "source_owner": "Account",
    "target_owner": "AccountConnection"
  },
  "budget_mode": "normal",
  "output_modes": ["engineer", "json"]
}
```

Agent then:

- extracts claims for the current field owner, reads, writes, payloads,
  migration/backfill needs, and downstream consumers
- searches for the field name, source owner, target owner, reads, writes, tests,
  and payload builders
- tags evidence categories such as `field definition`, `direct reads`,
  `direct writes`, `API or event payload boundary`, and `tests`
- treats any "only needs model changes" claim as too broad unless broad
  contradiction searches support it

The returned `inline_answer` is suitable for chat, for example:

```text
The source-backed impacts are direct reads in two code paths and one payload
builder. Plumbref did not find migration or backfill evidence under the normal
budget, so the migration plan should include an explicit data check. The claim
that this is only a model move is too broad.
```

### Change Impact

User:

```text
Could this local change affect downstream consumers?
```

Agent starts:

```json
{
  "question": "Could this local change affect downstream consumers?",
  "answer": "The change appears limited to report formatting.",
  "mode": "change_impact",
  "template_id": "change_impact",
  "template_values": {
    "changed_file": "path/to/changed_file.ext",
    "changed_symbol": "changed_symbol_name"
  },
  "budget_mode": "normal",
  "output_modes": ["engineer", "json"]
}
```

Agent records change context:

```json
{
  "source": "worktree"
}
```

Agent then:

- records changed files and symbols when available
- stores impact claims about changed behavior, API/contract boundaries, tests,
  and likely consumers
- searches for changed symbols, callers, imports, tests, fixtures, and docs
- marks absolute language such as "only formatting" as supported only after a
  contradiction pass

The returned `inline_answer` is suitable for chat, for example:

```text
Plumbref supports the narrower statement that the changed symbol formats report
labels. It did not support the broader claim that no downstream consumer can be
affected, because caller coverage was incomplete under the current budget.
Safer wording: this appears to affect report formatting in the checked paths.
```

### Downstream Consumers

User:

```text
Who consumes the user.created event?
```

Agent should use `downstream_consumers` and search for event definitions,
publishers, subscribers, handlers, clients, tests, and docs. The final answer
should separate directly cited consumers from inferred or unchecked consumers.

### External Integration

User:

```text
How does the payment provider webhook handle duplicate delivery?
```

Agent should use `external_integration` and check webhook entry points, request
parsing, idempotency keys, retry behavior, error handling, tests, mocks, and
configuration dependencies. The final answer should say whether duplicate
delivery behavior is source-backed, contradicted, or not found.

## Expected Chat Output

After rendering a Plumbref result, the agent should use the returned
`inline_answer` as the default chat response:

```text
Based on checked evidence, rely on this only with the qualifications below.

Safe to rely on:
- The changed function rewrites the report label from "items" to "records".

Say with qualification:
- too_broad: The change only affects formatting.

Safer wording:
- The checked function changes report-label wording, but caller coverage was
  incomplete, so generated clients and downstream exports still need review.

Evidence:
- `src/reports/labels.ts:41-58`
- `src/reports/labels.test.ts:12-27`

Unchecked:
- Conflicting-code-path search not recorded: generated client exports.

Verification: 2 claim(s) (supported=1, too_broad=1); 2 evidence snippet(s);
1/2 contradiction pass(es).
```

The report is the detailed artifact. `inline_answer` is the chat surface: it
summarizes what is safe to rely on, what needs qualification, what not to rely
on, safer wording, evidence locations, unchecked areas, and verification
counts. For low-risk fully supported answers, keep the result inline and do not
mention a report path unless one was written.
