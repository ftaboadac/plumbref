# Real Workflow Test Results

Date: 2026-06-11

These results came from running Plumbref through its MCP server against the
Plumbref repository itself. They are dogfood runs, not fabricated example
reports.

## What Was Tested

1. `explain_flow`: how Plumbref loads built-in and custom templates.
2. `field_migration`: what would be involved in renaming the public
   `template_id` input.
3. `change_impact`: whether the current onboarding/reporting changes affect
   setup docs and generated reports.

## Aggregate Results

- MCP sessions: 3
- Claims checked: 12
- Searches run: 29
- Search matches returned: 186
- Evidence snippets read: 28
- Unique evidence files read: 14 summed per-report unique-file counts
- Contradiction passes: 12/12 judged claims
- Unsupported or qualified claims caught: 3

## Source Token Comparison

Token counts are estimates, not provider billing records. The estimate uses
`ceil(characters / 4)` so the comparison is stable without depending on one
model tokenizer.

- Bounded Plumbref evidence snippets: about 6,666 source tokens
- Search previews returned by Plumbref: about 2,956 source tokens
- Full cited-file baseline: about 35,240 source tokens
- Full matched-file baseline: about 95,694 source tokens

That is an estimated 81% reduction versus opening every cited file in full, or
93% reduction versus opening every file matched by the searches. If you include
search previews plus bounded snippets as the Plumbref-side source text, the run
still used about 9,622 estimated source tokens instead of 95,694 for the full
matched-file baseline.

This is the cost claim I would make publicly: Plumbref does not remove the
agent's reasoning tokens, but it sharply reduces and records the amount of
repository text the agent needs to carry into context to support the answer.

## Reports

- [Template loading MCP report](../examples/reports/real-template-loading-mcp.md)
- [template_id migration MCP report](../examples/reports/real-template-id-migration-mcp.md)
- [Onboarding/reporting change-impact MCP report](../examples/reports/real-onboarding-change-impact-mcp.md)

## What Plumbref Caught

- It contradicted the claim that Plumbref automatically downloads templates from
  a remote marketplace. Current evidence only supports local built-in, user,
  repo-local, and configured template-pack directories.
- It marked "only the Pydantic model field would need to change" as too broad
  for a `template_id` rename, because the name appears in the MCP API, CLI,
  config fallback, docs, and tests.
- It marked "setup is now as simple as it can possibly be for every MCP client"
  as too broad. The setup is simpler, but users still need to put the generated
  MCP JSON in their client-specific config.

## Product Fixes Found By The Run

The first real run exposed two issues in Plumbref itself:

- Searches for query strings beginning with `--`, such as `--template-id`, were
  treated as ripgrep options unless the generated command inserted a `--`
  separator before the pattern.
- Markdown reports could become malformed when an evidence snippet contained
  fenced code blocks. Reports now choose a longer code fence when needed.

Both fixes are covered by regression tests.

## Public Claim I Would Make

Plumbref does not prove a whole repository is correct. It gives an agent a
repeatable verification trail: selected template, atomic claims, searches,
bounded snippets, conservative judgments, contradiction passes, and a report
that shows exactly where the answer is supported or needs qualification.
