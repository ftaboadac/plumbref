# Plumbref Roadmap

This roadmap tracks the path from the current MVP to the intended result:
fast, source-grounded answers about repository behavior, migration risk, and
change impact, with much lower token spend than letting an agent explore
freely.

The primary user experience is conversational agent usage through MCP or a
similar agent tool interface. The CLI should remain useful for development,
smoke tests, and debugging, but it is not the product surface to optimize for.

## Product Goal

Plumbref should help an engineer ask questions like:

- How does this integration or workflow work?
- What should we consider before moving this field or changing this contract?
- Could this code change affect downstream consumers or adjacent flows?

Engineers should ask these questions in chat. Plumbref should give the agent a
disciplined verification protocol and compact tool results, not require the
engineer to manually run commands.

The output should be a compact verification report with:

- atomic claims or predicted outcomes
- searches performed
- bounded evidence snippets
- conservative judgments
- limits, unchecked areas, and safer wording

The tool should reduce token spend by forcing agents to search narrowly, read
bounded snippets, reuse structured traces, and stop when a confidence budget is
exhausted.

## Guiding Principles

- Source evidence beats agent confidence.
- Claims must be atomic enough to verify.
- Every supported claim needs cited evidence and a contradiction pass.
- Broad language such as "only", "always", and "never" requires broader checks.
- Token budgets are a product feature, not just an implementation detail.
- MCP and agent ergonomics matter more than standalone CLI ergonomics.
- CLI behavior should remain testable but should not drive product design.
- Reports should say what was not checked, not only what was found.
- Local-first behavior matters: no model API, hosted service, vector store, or
  production data dependency should be required.

## Phase 0: Baseline Hygiene

Goal: make the existing MVP easier to trust, install, and explain.

- [ ] Fix package version mismatch between `pyproject.toml` and `plumbref/__init__.py`.
- [x] Position the README around one-time MCP setup and natural chat usage.
- [x] Update README test command to use the local project environment, such as
      `python -m pytest`.
- [ ] Add a short architecture section to the README.
- [ ] Add example reports for explanation, scenario, and change-impact modes.
- [ ] Add a changelog or release checklist.

Acceptance criteria:

- A teammate can connect Plumbref to an agent, run tests, and understand the
  main workflow in under 10 minutes.
- The README explains what Plumbref does and what it deliberately does not do.

## Phase 1: Opinionated Verification Templates

Goal: make common team questions cheaper and more reliable by giving the agent
structured playbooks.

Add first-class templates:

- [ ] `explain_flow`: for questions like "how does the Workday leave push work?"
- [ ] `field_migration`: for questions like "what if we move Rippling remote id
      from User to UserAccess?"
- [ ] `change_impact`: for diffs, PRs, and local worktree changes.
- [ ] `downstream_consumers`: for contract, event, API, model, and job changes.
- [ ] `external_integration`: for vendor syncs, pushes, pulls, webhooks, and API
      clients.

Each template should define:

- required claim types
- required search passes
- suggested contradiction searches
- expected evidence categories
- default budgets
- report sections
- unchecked-area prompts

Acceptance criteria:

- An agent no longer has to invent the verification strategy from scratch.
- The same question type produces comparable reports across engineers.

## Phase 2: Token-Efficient Search And Reading

Goal: reduce token burn by making repository exploration staged, bounded, and
cacheable.

Implement staged evidence collection:

- [ ] Stage 1: lexical search summaries only, no large file reads.
- [ ] Stage 2: bounded snippets around likely matches.
- [ ] Stage 3: only follow references when a claim needs more support.
- [ ] Stage 4: stop and report uncertainty when budget is exhausted.

Add stricter read controls:

- [ ] Per-template limits for searches, files, snippets, and reference depth.
- [ ] Maximum snippet line count.
- [ ] Maximum total excerpt characters per claim.
- [ ] Search result deduplication by file and symbol.
- [ ] Reuse previous searches within a session.
- [ ] Cache evidence snippets by file path, line range, and content hash.

Add token-aware report data:

- [ ] Record estimated excerpt characters per claim.
- [ ] Record avoided reads, cache hits, and skipped broad searches.
- [ ] Show why a claim stopped at `uncertain`, `not_found`, or `too_broad`.

Acceptance criteria:

- A normal flow explanation should not require reading whole files.
- A field migration check should start from identifiers and fan out only as
  needed.
- Reports make it obvious where token budget was spent.

## Phase 3: Repository Structure Intelligence

Goal: move beyond raw lexical search while staying local-first.

Add lightweight repo indexing:

- [ ] Detect languages and framework markers.
- [ ] Build a file inventory grouped by source, tests, docs, migrations, config,
      jobs, API routes, clients, and models.
- [ ] Extract symbols where practical using standard library parsers or
      lightweight local tooling.
- [ ] Track imports and direct references for supported languages.
- [ ] Add a symbol lookup API.
- [ ] Add a caller/reference lookup API.

Initial target areas:

- Python functions/classes/imports
- TypeScript/JavaScript imports and exported symbols
- ORM models and fields where they can be detected safely
- migration files
- scheduled jobs and background workers
- API routes/controllers
- external integration clients

Acceptance criteria:

- Plumbref can answer "where is this field used?" without dumping every match
  into the agent context.
- Change-impact mode can identify likely direct consumers before asking the
  agent to reason.

## Phase 4: Field Migration Workflow

Goal: make model/field movement questions systematic.

For a proposed field move, collect:

- [ ] current model definition
- [ ] all direct field reads/writes
- [ ] serializers, schemas, forms, and payload builders
- [ ] API endpoints and background jobs
- [ ] external integration clients
- [ ] migrations and data backfill requirements
- [ ] tests that encode current behavior
- [ ] docs and config references

Report sections:

- supported migration impacts
- likely code changes
- data migration/backfill risks
- downstream consumers
- unchecked areas
- safer implementation plan

Acceptance criteria:

- A question like "move Rippling remote id from User to UserAccess" produces a
  checklist of impacted code paths and unknowns, not a vague answer.

## Phase 5: Flow Explanation Workflow

Goal: make "how does this work?" questions produce compact, source-backed flow
maps.

For an integration or workflow, collect:

- [ ] entry points
- [ ] main functions/classes
- [ ] data models involved
- [ ] external calls
- [ ] failure handling
- [ ] retries/idempotency behavior
- [ ] tests and docs
- [ ] config/env dependencies

Report sections:

- short flow summary
- step-by-step source-backed path
- data inputs and outputs
- failure modes
- open uncertainties
- files worth reading next

Acceptance criteria:

- A teammate can understand a flow without asking "did the agent actually look
  at the source?"

## Phase 6: Change Impact Workflow

Goal: make local diffs and PRs easier to evaluate for unexpected downstream
effects.

Improve change context:

- [ ] detect changed symbols from diffs
- [ ] classify change type: behavior, API, schema, config, dependency, tests,
      docs, or refactor
- [ ] map direct references to changed symbols
- [ ] identify likely downstream consumers
- [ ] identify missing tests for touched behavior
- [ ] distinguish supported impact from speculative impact

Report sections:

- changed surface area
- direct consumers
- possible downstream effects
- tests that cover the changed behavior
- missing or uncertain areas
- safer impact statement

Acceptance criteria:

- For a small PR, Plumbref should produce a bounded blast-radius report without
  reading unrelated parts of the repo.

## Phase 7: Agent Integration Quality

Goal: make MCP usage predictable across Codex, Claude Code, Cursor, and similar
clients.

- [ ] Add MCP workflow examples per template.
- [ ] Add recommended agent instructions.
- [ ] Add conversational examples for the target questions: flow explanation,
      field migration, and change impact.
- [ ] Add a "minimal context" mode that returns IDs and summaries first, then
      snippets only when requested.
- [ ] Add structured errors that tell the agent what to do next.
- [ ] Add report links and session summaries optimized for chat clients.
- [ ] Treat the CLI as an internal validation/debug path, not as a primary
      user journey.

Acceptance criteria:

- Agents use Plumbref as a disciplined workflow instead of as a thin wrapper
  around search.

## Phase 8: Measurement And Benchmarks

Goal: prove that Plumbref improves trust and reduces waste.

Track:

- [ ] searches per answer
- [ ] files opened per answer
- [ ] snippet characters read
- [ ] cache hit rate
- [ ] claims by status
- [ ] unsupported broad claims caught
- [ ] time to report

Create benchmark fixtures:

- [ ] simple flow explanation
- [ ] field migration
- [ ] downstream consumer impact
- [ ] intentionally broad claim
- [ ] intentionally contradicted claim

Acceptance criteria:

- The project can show before/after behavior compared with unrestricted agent
  exploration.
- Token-related savings can be discussed with evidence, even if token counts are
  estimated.

## Phase 9: Optional Developer Interface Improvements

Goal: improve developer ergonomics only after the agent workflow is strong.

Possible additions:

- [ ] `plumbref init` to create config and examples.
- [ ] HTML report rendering.
- [ ] Local report viewer.
- [ ] CLI smoke-test helpers for templates, only if they make development and
      regression testing easier.

Non-goals unless the product direction changes:

- hosted service
- production data inspection
- replacing human review
- automatic truth decisions through an LLM

## Near-Term Priority

Recommended next work:

1. Fix baseline hygiene.
2. Make MCP/agent workflow examples the canonical usage path.
3. Add verification templates as data structures.
4. Add stricter snippet and character budgets.
5. Add template-specific report sections for unchecked areas.
6. Build one complete example around a realistic field migration question.

This sequence keeps the project aligned with the original reason it exists:
fewer repeated "are you sure?" loops, better source-backed answers, and lower
token spend.
