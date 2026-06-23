# Codex Live First-Run Transcript - 2026-06-22

This is a captured named-client first-run proof using Codex CLI against the
public SSO fixture. It starts from install/config level MCP wiring, executes
real Plumbref MCP tool calls, returns an inline answer, and writes a report.

## Target

- Client: Codex CLI at `/Applications/Codex.app/Contents/Resources/codex`
- Repo under review: `examples/fixtures/sso-before`
- Plumbref server: local stdio MCP via `.venv/bin/python -m plumbref mcp`
- Prompt:

```text
Use the Plumbref MCP server to answer this. Do not use shell commands.

Question: The agent said SSO only depends on Okta. Check that before I tell support.
Draft answer to check: SSO only depends on Okta.

Use a normal repository verification flow: start a Plumbref session, record the claim, search/read evidence, record a conservative judgment, render the report, and return the Plumbref inline_answer plus any generated report path.
```

## Command

```shell
codex exec --json \
  -C /Users/facundotaboada/Documents/GitHub/plumbref/examples/fixtures/sso-before \
  --sandbox read-only \
  -c 'mcp_servers.plumbref.command="/Users/facundotaboada/Documents/GitHub/plumbref/.venv/bin/python"' \
  -c 'mcp_servers.plumbref.args=["-m","plumbref","mcp","--repo-root","/Users/facundotaboada/Documents/GitHub/plumbref/examples/fixtures/sso-before"]' \
  -c 'mcp_servers.plumbref.default_tools_approval_mode="approve"' \
  - < /tmp/plumbref-live-codex/prompt-2.txt \
  > /tmp/plumbref-live-codex/codex-events-success.jsonl \
  2> /tmp/plumbref-live-codex/codex-stderr-success.log
```

The approval-mode override matters for noninteractive Codex. With `auto` or
`prompt`, Codex discovered the Plumbref tools but cancelled MCP calls with
`user cancelled MCP tool call`. With `approve`, the same local server executed.

## What Happened

The first-run was successful, but not friction-free:

- Codex first tried `output_modes=["inline_answer","report"]`; Plumbref rejected
  `inline_answer` as an invalid output mode.
- Codex then tried `mode="verify"`; Plumbref rejected `verify` as an invalid
  verification mode.
- Codex recovered by calling `plumbref_start` with defaults, then completed the
  full workflow.

Successful tool path:

1. `plumbref_start`
2. `plumbref_extract_claims`
3. `plumbref_search_repo` for `Okta`
4. `plumbref_search_repo` for `okta`
5. `plumbref_search_repo` for `sso`
6. `plumbref_search_repo` for `rippling`
7. `plumbref_search_repo` for `sso_enabled`
8. `plumbref_read_evidence` for `app/sso.py`
9. `plumbref_read_evidence` for `checks/sso_checks.py`
10. `plumbref_record_judgment`
11. `plumbref_render_report`

## Inline Answer

```text
Plumbref found source evidence against the answer as written.

Do not rely on:
- contradicted: SSO only depends on Okta.

Safer wording:
- SSO can be enabled through Okta or through a Rippling integration; it is not Okta-only.

Evidence:
- `app/sso.py:1-22`
- `checks/sso_checks.py:1-13`
```

## Generated Report Path

Original generated paths from the live run:

```text
/Users/facundotaboada/Documents/GitHub/plumbref/examples/fixtures/sso-before/.cache/plumbref/reports/2026-06-22/3235deb8-bc8c-4f7e-9f3d-961c8938353d.md
/Users/facundotaboada/Documents/GitHub/plumbref/examples/fixtures/sso-before/.cache/plumbref/reports/2026-06-22/3235deb8-bc8c-4f7e-9f3d-961c8938353d.json
```

Archived public-safe copies:

- [reports/codex-live-sso-2026-06-22.md](reports/codex-live-sso-2026-06-22.md)
- [reports/codex-live-sso-2026-06-22.json](reports/codex-live-sso-2026-06-22.json)

Raw Codex JSONL transcript:

- [transcripts/codex-live-sso-2026-06-22.jsonl](transcripts/codex-live-sso-2026-06-22.jsonl)

## Product Signal

This proves the named-client first-run is possible in Codex. The original run
also showed an onboarding gap: agents can guess enum values that sound natural
but are not valid. Plumbref now accepts common aliases like `verify`,
`inline_answer`, and `report` at the MCP boundary; see the customer-exports
benchmark transcript for a fixed run that starts successfully with those
aliases.
