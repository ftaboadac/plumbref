# Product Strategy

Plumbref has three related but distinct product tracks.

## Track 1: Verification Outcome

Goal:

> Make the agent's answer pass through an evidence gate before it is stated with
> confidence.

This is the track that makes Plumbref meaningfully better than an `AGENTS.md`
instruction file. `AGENTS.md` can ask an agent to be careful. Plumbref should
show whether the agent actually did the verification work.

Implemented features:

- answer gate: safe to answer, answer with qualifications, do not claim, or not
  ready
- template scope tracking without presenting a percentage grade
- required searches marked done or missing
- required evidence categories marked found or missing
- automatic broad-claim detection for words like `only`, `always`, `never`,
  `all`, `every`, and `guarantee`
- stricter `supported` rules when a claim uses broad or absolute language
- scoped follow-up checks only when a broader claim needs broader evidence
- safer-answer generation from supported and qualified claims
- clearer report summary for what can be said, what must be qualified, and what
  should not be claimed

Expected effect:

- more trust
- fewer unsupported claims
- better reviewability
- stronger differentiation from prompt-only workflows
- possibly slightly more source-token usage, because more checks are enforced

Best public framing:

> Plumbref gives you a careful-agent workflow even when you cannot trust that
> the agent will naturally behave like a careful senior engineer.

## Track 2: Token Optimization

Goal:

> Avoid rereading or repasting source text when Plumbref already has enough
> stable evidence.

This is the track that could make Plumbref cheaper than a careful expert agent,
especially across repeated questions, iterative sessions, or recurring
workflows.

Potential features:

- deduplicate evidence snippets across claims
- cache searches by query, ignored paths, and repo state
- cache evidence snippets by file path, line range, and file hash
- reuse previous reports when relevant files have not changed
- store stable evidence IDs so agents can cite prior evidence without rereading
  the source text
- return compact chat summaries plus report paths instead of full excerpts
- auto-stop when template coverage is sufficient
- track repeated workflow savings over time
- expose cache hit, cache miss, and reused-evidence metrics in reports

Expected effect:

- lower source-token usage over repeated workflows
- faster follow-up investigations
- less duplicate evidence in reports
- stronger cost/speed claims once measured

Best public framing:

> Plumbref can reuse verified evidence when the source has not changed, so
> repeated repo investigations do not have to start from zero.

## Track 3: Repeatability And Drift

Goal:

> Keep verified claims about the codebase checkable after the code changes.

This is the track that could make Plumbref more than a one-shot answer
verification harness. A report should become a durable artifact: a set of
claims, statuses, evidence, and limits that can be rerun later and compared
against a new repo state.

Potential features:

- stable claim IDs in generated reports
- rerun mode that rechecks a previous report's claims against a new commit
- report diffs that show status changes, evidence changes, and new limits
- business-rule claim tracking for flows that drift with product requirements
- Markdown diff reports that are useful without a custom UI
- optional scheduled or CI checks after the diff workflow is validated

Expected effect:

- engineering knowledge is less trapped in one chat session
- stale assumptions become visible when the code changes
- teams can monitor risky flows without relying on tribal memory
- public positioning can move from "better agent answer" to "documentation that
  stays true"

Best public framing:

> Your team's verified claims about how the codebase works, updated when the
> code changes.

## Build Order

Prioritize Track 1 first.

Reason:

Plumbref's core differentiation is trust, auditability, and repeatability. Token
savings are useful, but the current validation shows Plumbref is not always
cheaper than a careful expert agent reading tight snippets in a single fresh
investigation.

Recommended order:

1. Add claim-gated verification outcomes.
2. Add automatic broad-claim detection.
3. Add scoped follow-up checks for broader claims.
4. Add a verification outcome summary.
5. Improve safer-answer generation.
6. Add stable claim IDs.
7. Add report rerun/diff for previously verified claims.
8. Add evidence and search caching.
9. Add reused-evidence reporting.
10. Measure repeated-workflow token savings.

## Positioning

Do not lead with:

> Plumbref always saves tokens.

Do not frame the product as:

> Agents are bad and Plumbref catches them.

Lead with:

> Plumbref gives you a careful-agent workflow even when you cannot trust that
> the agent will naturally behave like a careful senior engineer.

The aspirational framing is stronger than the defensive one: Plumbref is a
verification harness for careful agent work. It helps coding agents give more
complete repo answers by forcing the source checks to happen before the answer
is trusted. The report is not the product; it is the visible proof that the
agent decomposed the answer, searched the right areas, checked source snippets,
considered limits, and qualified broad claims. Nobody has to be wrong for the
product to be valuable. The value is that risky repo questions come back with
higher confidence because the agent was pushed through the checks a careful
engineer would expect.

The repeatability framing is the longer-term product category:

> Plumbref turns risky repo answers into verified claims your team can rerun
> when the code changes.

For public screenshots, prefer a real report excerpt answering a hard,
relevant repository question. The screenshot should show that the answer went
through verification: the question, selected template, required searches,
source evidence, supported or qualified claims, limits, and final wording. A
comparison graph can support the story later, but the primary "I want this"
moment is realizing the answer is more trustworthy because the agent had to
verify and consider the important paths before responding.

Then make the token claim narrower:

> Plumbref can reduce source context when it prevents broad file reading, and a
> future evidence-reuse layer can reduce repeated investigation cost.
