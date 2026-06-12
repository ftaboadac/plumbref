# External Private Repo Validation

Date: 2026-06-11

This validation used Plumbref against a private production monorepo as an
external target. The target repository was read-only for the run: no files were
created, edited, staged, or committed there.

The raw Plumbref reports contain private file paths and source excerpts, so they
are intentionally kept out of checked-in public examples. This document keeps
only abstracted task descriptions, measurements, and conclusions.

## Protocol

Three realistic questions were tested:

1. Explain how a frontend template-variable parser recognizes and renders
   variables.
2. Evaluate the impact of renaming a profile identifier field used across
   frontend payloads and backend request handling.
3. Evaluate whether changing a lightweight status endpoint could affect
   server-side routing.

Each question was run two ways:

- Plumbref MCP workflow: template selection, claim extraction, searches,
  bounded evidence snippets, judgments, contradiction passes, and report
  rendering.
- Non-Plumbref agent baseline: normal `rg` searches with a global 20-result cap
  per search, then explicit source ranges read by the agent to reach the same
  conclusions.

Token estimates use `ceil(characters / 4)`. They compare source text moved into
context, not provider billing.

## Results

| Task | Plumbref result | Claims | Plumbref source + previews | Careful agent source + previews | Full opened-file baseline | Full matched-file baseline |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Template-variable parser flow | Contradicted one overclaim | 4 | 4,329 | 4,607 | 3,331 | 52,503 |
| Profile identifier field migration | Qualified one overclaim | 4 | 3,309 | 2,912 | 36,587 | 63,938 |
| Status endpoint routing impact | Qualified one overclaim | 4 | 2,915 | 2,612 | 12,573 | 63,002 |
| **Total** | 3 unsupported/qualified claims caught | **12** | **10,553** | **10,131** | **52,491** | **179,443** |

These totals intentionally mirror the dogfood validation shape: three
questions, four claims per question, and one deliberately risky claim per
question. The external run did not reuse dogfood evidence or claims, but the
symmetry means the aggregate counts should not be presented as organically
representative workload statistics.

## What This Proves

- Plumbref worked on a different, larger repo and stack than Plumbref itself.
- It produced real source-backed reports through MCP without modifying the
  target repository.
- It caught three risky claims:
  - a parser-flow claim that implied validation happened earlier than the source
    supported
  - a migration claim that scoped the change to one frontend file when backend
    contract surfaces were involved
  - a routing claim that generalized one status dependency to every server-side
    onboarding guard
- It reduced source context by about 80% versus opening the full files needed
  by the baseline agent pass.
- It reduced source context by about 94% versus opening every file matched by
  the searches.

## What It Does Not Prove

- It does not prove Plumbref is cheaper than an already careful expert agent
  that reads tight source snippets. In this run, Plumbref used roughly the same
  source-token volume as the careful baseline, about 4% more in aggregate,
  because it performed explicit contradiction passes and recorded more evidence.
- It does not prove all templates are reliable for every repo shape.
- It does not prove the model's reasoning tokens are lower. The measurement is
  source text carried into context, not total inference cost.
- It does not replace engineering judgment. The agent still extracts claims,
  picks searches, and judges evidence.

## Public Claim I Would Make

Plumbref is not magic token compression. Its value is that it makes a careful
agent workflow repeatable: it forces bounded searches, cited snippets,
contradiction passes, conservative statuses, and an inspectable report. Against
broad full-file reading it can sharply reduce source context; against a careful
expert agent it mainly adds discipline, repeatability, and auditability.
