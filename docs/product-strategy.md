# Product Strategy

Plumbref has two related but distinct product tracks.

## Track 1: Verification Quality

Goal:

> Make the agent's verification work observable, repeatable, and hard to fake or
> skip.

This is the track that makes Plumbref meaningfully better than an `AGENTS.md`
instruction file. `AGENTS.md` can ask an agent to be careful. Plumbref should
show whether the agent actually did the verification work.

Potential features:

- report quality or completeness score
- template checklist completion tracking
- required searches marked done or missing
- required evidence categories marked found or missing
- automatic broad-claim detection for words like `only`, `always`, `never`,
  `all`, `every`, and `guarantee`
- stricter `supported` rules when a claim uses broad or absolute language
- recommended next checks when a report is incomplete
- safer-answer generation from supported and qualified claims
- clearer report summary for what was checked, what was not checked, and what
  should not be claimed

Expected effect:

- more trust
- fewer unsupported claims
- better reviewability
- stronger differentiation from prompt-only workflows
- possibly slightly more source-token usage, because more checks are enforced

Best public framing:

> AGENTS.md asks the agent to be careful. Plumbref checks whether the agent
> actually did the verification work.

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

## Build Order

Prioritize Track 1 first.

Reason:

Plumbref's core differentiation is trust, auditability, and repeatability. Token
savings are useful, but the current validation shows Plumbref is not always
cheaper than a careful expert agent reading tight snippets in a single fresh
investigation.

Recommended order:

1. Add checklist completion tracking.
2. Add automatic broad-claim detection.
3. Add recommended next checks.
4. Add a report quality/completeness summary.
5. Improve safer-answer generation.
6. Add evidence and search caching.
7. Add reused-evidence reporting.
8. Measure repeated-workflow token savings.

## Positioning

Do not lead with:

> Plumbref always saves tokens.

Lead with:

> Plumbref turns agent repo answers into source-backed verification reports.

Then make the token claim narrower:

> Plumbref can reduce source context when it prevents broad file reading, and a
> future evidence-reuse layer can reduce repeated investigation cost.
