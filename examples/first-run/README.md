# Plumbref First-Run Example

This is the first public proof path for the checked-claims direction. It shows
the intended MCP user moment without claiming that Plumbref reasons
independently from the coding agent.

## Goal

Check a risky support-facing repo claim:

```text
The agent said SSO only depends on Okta. Check that before I tell support.
```

## Setup

From a checkout:

```shell
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
plumbref init --repo-root .
plumbref doctor --repo-root . --check-mcp-startup
```

MCP server command for a client that accepts stdio MCP config:

```json
{
  "mcpServers": {
    "plumbref": {
      "command": "plumbref",
      "args": ["mcp", "--repo-root", "/path/to/plumbref"]
    }
  }
}
```

## Prompt

```text
The agent said SSO only depends on Okta. Check that before I tell support.
Use Plumbref and return the inline answer.
```

## What The Agent Should Do

The coding agent still chooses claims and searches. Plumbref enforces the
recorded workflow and downgrades unsafe confidence when required traces are
missing.

Expected tool flow:

1. `plumbref_start`
2. `plumbref_extract_claims`
3. `plumbref_search_repo`
4. `plumbref_read_evidence`
5. `plumbref_record_judgment`
6. `plumbref_render_report`

## Expected Inline Answer

See [expected/inline-answer.md](expected/inline-answer.md).

The important part is not the exact wording. The important part is that the
answer does not say the broad "only depends on Okta" claim is safe unless the
required contradiction searches and evidence are recorded.

## Expected Report Artifact

See [expected/checked-claim.json](expected/checked-claim.json) for the checked
claim shape exported from a report.

This example is intentionally small. It proves the first value moment:

- risky claim
- local evidence trail
- qualified or contradicted output
- explicit unchecked areas
- exportable checked claim
