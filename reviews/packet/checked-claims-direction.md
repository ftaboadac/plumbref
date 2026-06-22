# Proposed Direction: Checked Claims

This is the reviewed direction to use before implementation.

Plumbref would combine:

1. Real answer-gate enforcement.
2. Living repo facts that can be rerun when code changes.
3. PR/CI risk checks for risky claims in PR summaries, release notes, commit
   messages, and agent summaries.

Proposed product statement:

> Plumbref turns risky engineering claims into checked repo facts, blocks
> unsupported confidence, and tells you when code changes make those facts
> stale.

Review result:

> would try once

The review found that this direction is stronger than broad "AI verifier"
positioning, but it is not yet a "would use weekly" product. The blocker is
technical trust: the current safe/evidence gate is not strict enough.

Core object:

> A checked claim: claim text, stable ID, repo state, template, required checks,
> searches, contradiction searches, evidence snippets, missing categories,
> budget status, judgment, limits, safer wording, and rerun instructions.

Key product rule:

> A claim cannot be marked safe to rely on unless the required evidence trail is
> present.

This rule is not fully true in the current implementation. It is the first build
target. Until implemented, public language should say "evidence trail" or
"claim-check workflow," not "real gate."

Proposed surfaces:

- Real gate: downgrade or block unsupported confidence.
- Living facts: rerun checked claims after code changes and show drift.
- PR/CI checks: inspect risky PR/release/agent-summary claims against diffs,
  initially as advisory Markdown or PR comments.

Build order from the review:

1. Strict answer-gate enforcement.
2. Public first-run transcript for one named MCP client.
3. Checked-claim JSON schema.
4. Claim rerun and claim diff.
5. Advisory PR checks from explicit claim files.
6. Benchmark against careful prompting plus `rg`.

Do not build hard-failing CI, a UI, fuzzy PR prose extraction, or token-saving
features before the strict gate and first-run proof exist.

Review this direction, not only the current implementation. The most important
question is whether strict gate enforcement plus living checked claims could
become a "would use weekly" product for engineers who already use coding agents
on real codebases.
