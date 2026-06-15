# Reliance Check Implementation Plan

This plan pivots Plumbref toward the sharper promise:

> Plumbref verifies codebase claims before you rely on them.

The product should help an engineer decide what parts of an AI-generated repo
answer are safe to repeat, safe to act on, too broad, contradicted, or not
verifiable from local repository evidence.

This is not a plan to prove general truth. It is a plan to make reliance on AI
codebase claims more auditable and less dependent on a vague "are you sure?"
loop.

## Product Boundary

In scope:

- claims about code behavior
- claims about where logic lives
- claims about downstream consumers
- claims about migration/refactor impact
- claims about diff/change impact
- claims about what local code, tests, docs, and config support

Out of scope:

- legal, medical, financial, or general internet fact verification
- production-data verification
- hosted repo indexing
- automatic proof of runtime behavior
- replacing human code review
- a standalone local UI as the primary product

The safest language is:

> Supported by checked evidence.

Not:

> True.

## Target User Flow

### Explicit Use

User:

```text
The agent said this only affects onboarding. Check that with Plumbref.
```

Agent with Plumbref:

```text
Safe to rely on:
- The checked docs changes affect onboarding instructions.

Do not rely on:
- "This only affects onboarding." The checked diff also changes inline report wording.

Safer wording:
- This change updates onboarding docs and inline report wording. No runtime path was fully traced in this check.

Evidence:
- docs/agent-usage.md:...
- plumbref/reports.py:...

Unchecked:
- Downstream users of rendered reports were not fully traced.
```

### Automatic Use

The agent should call Plumbref automatically when a repo answer is risky:

- the user asks "are you sure?"
- the answer is about a PM/support/customer-facing statement
- the answer is about merge safety or implementation scope
- the answer uses `only`, `always`, `never`, `all`, `every`, `safe`, or
  `no downstream consumers`
- the topic is migration, auth, billing, data movement, external integrations,
  background jobs, or API contracts

Automatic use should be trigger-based, not every repo question by default.

## Current Assets To Keep

The current repo already has useful machinery:

- MCP server tools
- CLI setup and doctor commands
- claim model and statuses
- broad-language detection
- bounded repo search and evidence reads
- judgments and contradiction-pass tracking
- inline answer rendering
- Markdown/JSON reports
- report diff support
- tests around report behavior

The pivot should reshape the user-facing output and docs before adding major
new infrastructure.

## Phase 1: Rename The UX Around Reliance

Goal:

Make the inline answer answer the user's actual question: "what can I rely on?"

Changes:

- Replace inline section names:
  - `What Plumbref checked` -> `Safe to rely on` or `Safe to say`
  - `Important limits` -> split into `Say with qualification` and `Do not rely on`
  - `Evidence checked` -> `Evidence`
  - add `Unchecked` when quality checks or template checks are missing
- Keep report internals as claims/evidence/judgments where useful.
- Make the inline answer the primary user-facing surface in README examples.

Implementation notes:

- Update `build_inline_answer` in `plumbref/reports.py`.
- Split `inline_limit_lines` into status-aware sections:
  - qualified: `too_broad`, `uncertain`, `not_found`, `not_verifiable`
  - avoid: `contradicted`
  - supported limits that materially affect reliance
- Add an `inline_unchecked_lines` helper using `quality["next_checks"]`,
  missing evidence categories, missing required searches, and unjudged claims.
- Keep the output short: maximum 3-5 bullets per section.

Acceptance criteria:

- A supported answer clearly says what is safe to rely on.
- A too-broad claim appears under a section that tells the user not to rely on
  it as written.
- A contradicted claim is visibly separated from qualified claims.
- Missing checks appear as user-readable unchecked areas, not as template
  implementation details.
- Existing tests pass.

## Phase 2: Make Safer Wording First-Class

Goal:

Every risky claim should produce replacement wording the user can repeat or act
on.

Changes:

- Add a first-class `safer_wording` field to judgments or claim output.
- Continue accepting `limits`, but do not rely on `limits` as the only source
  of replacement text.
- Render safer wording prominently in inline answers.
- For backward compatibility, infer safer wording from `limits` when the new
  field is absent.

Implementation options:

1. Add `safer_wording: str = ""` to `Judgment`.
2. Update `plumbref_record_judgment` MCP tool to accept it.
3. Update report JSON and Markdown rendering.
4. Update tests to check safer wording appears once and in the correct section.

Acceptance criteria:

- Too-broad claims can show:

  ```text
  Do not rely on:
  - "This only affects reports."

  Safer wording:
  - The checked symbol affects report wording, but callers were not fully traced.
  ```

- Contradicted claims can show corrected wording when available.
- Inline output gives the user a pasteable replacement without opening the full
  report.

## Phase 3: Add An Explicit Audit Path

Goal:

Make "check this agent answer before I rely on it" a first-class documented
workflow.

Changes:

- Add README examples for:
  - "Audit this answer"
  - "Answer this safely"
- Update agent instructions to include explicit triggers:
  - "audit that with Plumbref"
  - "what can I safely say"
  - "can I rely on this"
  - "check this before I send/merge"
- Keep the MCP start signature as `question` + `answer`; this already supports
  audit mode.
- Optionally add `intent` or `reliance_context` later, but avoid schema churn
  until the output shape is proven.

Acceptance criteria:

- A new user can understand from the README that Plumbref audits AI codebase
  claims before reliance.
- Docs show both explicit and automatic usage.
- Docs do not imply Plumbref proves global truth.

## Phase 4: Better Status Semantics For Reliance

Goal:

Map internal claim statuses to user decisions.

Current statuses can remain:

- `supported`
- `too_broad`
- `uncertain`
- `contradicted`
- `not_found`
- `not_verifiable`

User-facing mapping:

- `supported` -> safe to rely on within checked scope
- `too_broad` -> do not rely on as written; use safer wording
- `uncertain` -> do not rely without more checks
- `contradicted` -> do not say or act on this
- `not_found` -> no support found under this search
- `not_verifiable` -> cannot verify from local repo evidence

Changes:

- Add a small mapping layer in reports, not in core models.
- Use this mapping consistently in inline answers and Markdown reports.
- Avoid presenting `supported` without scope.

Acceptance criteria:

- Inline answers never imply global truth.
- `supported` lines include checked-scope language when needed.
- Risky statuses are actionable, not just labels.

## Phase 5: Make Broad Claims More Aggressive

Goal:

Make the product especially good at catching "only/always/never/no downstream"
style overclaims.

Changes:

- Expand broad-language detection beyond single words:
  - `safe to`
  - `does not affect`
  - `no downstream`
  - `no callers`
  - `no consumers`
  - `just`
  - `only needs`
  - `cannot happen`
  - `all users`
  - `every customer`
- Add tests for these phrases.
- Require stronger contradiction notes or qualification for supported broad
  claims.

Acceptance criteria:

- "This only affects X" cannot be quietly supported without coverage notes.
- "No downstream consumers" is treated as broad/high-risk language.
- "Safe to rename" is treated as broad unless references and boundaries were
  checked.

## Phase 6: Build One Killer Demo

Goal:

Create a demo that makes the value obvious in five seconds.

Demo shape:

```text
Agent answer:
"This change only affects onboarding docs."

Plumbref:
Do not rely on "only." The checked diff also changes inline report wording.

Safer wording:
"This change updates onboarding docs and inline report wording. No runtime path
was fully traced in this check."

Evidence:
- docs/agent-usage.md:...
- plumbref/reports.py:...
```

Changes:

- Add a checked-in example report and inline-answer fixture.
- Update README to show this before lower-level details.
- Avoid leading with token reduction, cache, or template internals.

Acceptance criteria:

- Someone can understand the product without knowing MCP.
- The demo shows an overclaim being caught and rewritten.
- The demo makes "ask are you sure?" look weaker by comparison.

## Phase 7: Rerun/Diff As Staleness Check

Goal:

Preserve the original stale-citation idea without making report diff the main
product.

User story:

> Is the thing I relied on last week still supported after this PR?

Changes:

- Reframe `diff-reports` docs around stale reliance checks.
- Render diff output as:
  - previously safe statement
  - current status
  - updated safer wording
  - changed evidence
- Keep JSON diff support as the internal mechanism.

Acceptance criteria:

- User does not need to understand report JSON comparison.
- A changed supported claim becomes a clear "do not rely on old wording"
  result.

## Phase 8: Optional Local UI

Do not build this yet.

A local UI may be useful later for:

- filtering claims by status
- viewing source snippets side by side
- copying safer wording
- browsing stale claim diffs

But it should only happen after the inline answer is compelling. A UI before
that point risks hiding the product problem behind a dashboard.

## Recommended Build Order

1. Update inline answer sections around reliance.
2. Add tests for supported, too-broad, contradicted, and unchecked inline
   output.
3. Add first-class safer wording.
4. Update README positioning and examples.
5. Expand broad-language detection.
6. Create the killer demo.
7. Reframe report diff as stale reliance checking.
8. Consider UI/plugin packaging only after real usage validates the flow.

## What Success Looks Like

A successful Plumbref run should let the user say:

> I know what I can rely on, what I should not rely on, and where the source
> evidence is.

Good outcome metrics:

- caught an overclaim
- produced safer wording
- reduced the need to ask "are you sure?"
- answer could be pasted to another person
- evidence could be inspected in under 30 seconds
- stale wording could be detected after a code change

Bad primary metrics:

- report length
- number of claims
- number of searches
- cache hit rate
- template coverage percentage

Those are diagnostics, not the product value.

