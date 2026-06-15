# Return To The Groundcheck Angle

This note recenters Plumbref around the original problem: the moment before an
engineer repeats an AI-generated codebase answer to a PM, support teammate,
customer, reviewer, or merge decision.

The user is not looking for a verification framework. They are asking:

> What can I safely say?

## Core User Moment

The original pain was the repeated loop:

1. Agent gives a confident repo answer.
2. User distrusts it.
3. User asks, "Are you sure?"
4. Agent gives more confident prose.
5. User still has to inspect source before relaying or merging.

Plumbref should break that loop by turning an AI repo answer into:

- statements that are safe to repeat
- statements that need qualification
- statements that should not be said as written
- exact source lines behind the supported parts
- unchecked areas that still matter

The product is not the process. Claims, searches, snippets, judgments,
contradiction checks, reports, templates, and cache metrics are machinery. The
user-facing value is a safer answer.

## Sharper Positioning

Primary positioning:

> Before you repeat an AI answer about your codebase, Plumbref tells you what is
> supported, what is too broad, and what not to say.

Alternative:

> Plumbref turns AI repo answers into safe-to-repeat statements with
> source-backed limits.

Technical positioning, for docs:

> Plumbref is a local evidence gate for coding agents.

Do not lead with:

- templates
- MCP
- token savings
- cache metrics
- report generation
- careful-agent workflow

Those can remain supporting details, but they should not be the first thing a
new user sees.

## Primary Output

The main output should be an inline, sendable answer:

```text
Safe to say:
- ...

Say with qualification:
- ...

Do not say:
- ...

Evidence:
- file.py:12-28
- tests/test_file.py:44-61

Unchecked:
- ...
```

This is the artifact the user can paste into a PM thread, support escalation,
customer note, PR review, or implementation plan.

The full report is still useful, but it is the receipt behind the answer. If
the user must read the full report to get value, the product is backwards.

## Product Modes

Plumbref should support two modes, with "audit this answer" as the wedge.

### Mode A: Audit This Answer

Input:

```text
Question: How does SSO eligibility work?
Agent answer: SSO only starts when Rippling or Okta is enabled.
```

Output:

```text
Do not say that as written. Source also allows company.sso_enabled.

Safe wording:
SSO can start through Rippling, Okta, or company.sso_enabled in the checked
implementation.

Evidence:
- app/sso.py:10-19
- checks/sso_checks.py:1-15
```

This mode maps most directly to the original "are you sure?" reflex.

### Mode B: Answer This Safely

Input:

```text
How does SSO eligibility work?
```

Output:

```text
Safe to say:
- ...

Unchecked:
- ...

Evidence:
- ...
```

This mode is useful, but the stronger emotional wedge is auditing an answer the
user is already about to trust.

## Why This Beats "Are You Sure?"

Asking "are you sure?" usually produces more prose. Plumbref should visibly
provide things reassurance does not:

- exact source lines
- claims split apart
- unsupported parts called out
- safer replacement wording
- unchecked areas
- stale or changed evidence when rerun

If Plumbref only says "I checked," it loses. It must return an actionable answer
and a receipt.

## Translate Internal Terms Into User Actions

Avoid exposing process language as the main UX.

Use:

- "Safe to say"
- "Say with qualification"
- "Do not say"
- "Source lines"
- "Unchecked"
- "Checked for conflicting code paths"

Instead of leading with:

- claims
- judgments
- contradiction passes
- evidence snippets
- template checklist
- quality score

The internal ledger can retain precise technical terms. The inline answer
should speak in user actions.

## Make Too Broad The Killer Feature

The most useful status is often not `supported`; it is `too_broad`.

This is where the user's distrust usually comes from:

- "This only affects the frontend."
- "Every customer goes through this path."
- "This is safe to rename."
- "No downstream consumers use this."
- "This flag is only checked server-side."
- "This migration only touches the model."

Plumbref should aggressively detect absolute or broad language and force safer
wording.

Every unsupported, contradicted, uncertain, or too-broad claim should produce a
first-class replacement:

```text
Original:
"This only affects report wording."

Safer wording:
"The checked changed symbol affects report wording, but callers were not fully
traced."
```

This replacement wording is the product moment. It is what the user can repeat.

## Report Role

The report should exist for:

- PR attachment
- support escalation
- customer-sensitive explanations
- high-risk merge decisions
- later rerun/diff checks
- debugging why Plumbref qualified something

But the inline answer should carry the main value for normal use.

Recommended hierarchy:

1. Safe answer
2. Qualified answer
3. Do-not-say claims
4. Evidence
5. Unchecked areas
6. Full ledger/report

## Rerun And Diff

Rerun/diff should serve the original staleness problem, not become a product of
its own.

User story:

> Is the thing I told support last week still true after this PR?

Output:

```text
Previously safe statement is no longer safe:
- Old: SSO only starts from Rippling or Okta.
- New: company.sso_enabled also enables SSO.
- Updated wording: SSO can start through Rippling, Okta, or company.sso_enabled.

Evidence changed:
- app/sso.py:10-19
```

Avoid framing this as "compare report JSON files" in public UX. That is an
implementation detail.

## Template Role

Templates are useful internally, but they should not dominate the product
surface.

Users care about:

- Can I say this?
- What source supports it?
- What is risky?
- What should I check next?

Templates should help the agent produce better answers. They should not make
the product feel like a framework the user must understand before receiving
value.

## Demo Shape

The strongest demo is not a comprehensive report. It is a before/after trust
check.

Example:

```text
Agent answer:
"This change only affects onboarding docs."

Plumbref:
Do not say "only." The checked diff also changes inline report wording.

Safe wording:
"This change updates onboarding docs and inline report wording. No runtime path
was checked beyond the recorded changed files."

Evidence:
- docs/agent-usage.md:...
- plumbref/reports.py:...

Unchecked:
- Downstream users of the rendered report were not fully traced.
```

What the demo should communicate in five seconds:

> This is the answer I want before changing a risky flow or repeating an AI
> explanation.

## Success Metrics

Measure success by user outcomes, not process volume.

Good metrics:

- Did Plumbref catch an overclaim?
- Did it produce safer wording?
- Did the user avoid asking "are you sure?"
- Could the answer be pasted to another person?
- Could a reviewer inspect the evidence in under 30 seconds?
- Did rerun/diff catch a statement that became stale?

Less useful primary metrics:

- number of claims checked
- number of searches run
- cache hit rate
- report length
- template coverage percentage

Those may support diagnostics, but they are not the reason users care.

## What To De-Emphasize

Do not delete these necessarily, but stop leading with them:

- token optimization
- cache hit rates
- template packs
- report indexes
- measurement sections
- broad roadmap language
- "careful-agent workflow"

The angle is trust before repetition.

## Concrete Product Direction

Recenter the implementation and docs around this question:

> What can I safely say?

Practical next steps:

1. Rename the main inline sections to `Safe to say`, `Say with qualification`,
   `Do not say`, `Evidence`, and `Unchecked`.
2. Make safer wording a first-class field for qualified and rejected claims.
3. Add an explicit "audit this answer" path to docs and examples.
4. Demote template/checklist/report terminology from the README opening.
5. Build the primary demo around an overclaim being rewritten into safe wording.
6. Keep the full report as an inspectable receipt, not the primary artifact.

