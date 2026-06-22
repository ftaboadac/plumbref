**1. Top 5 Adoption Blockers**

| Rank | Blocker | Reviewers | Type | Smallest Artifact To Reduce It |
|---:|---|---|---|---|
| 1 | No live named-client proof. Current proof is fixture-based or stale, not a captured Codex/Claude/Cursor run. | 00, 01, 02, 03, 04, 05 | Missing proof | Captured first-run transcript from clean install through MCP tool calls, inline answer, JSON/Markdown report, using one named client. |
| 2 | “Verification” still depends on the agent choosing claims, searches, evidence, and judgments correctly. Omitted risky claims are invisible. | 00, 01, 02, 03, 04, 05 | Technical trust / positioning | Adversarial test suite showing Plumbref downgrades weak searches, missing claims, fake categories, skipped placeholders, cache-only evidence, and budget exhaustion. |
| 3 | Not yet proven better than careful prompting plus `rg`, citations, contradiction searches, and unchecked-areas prompts. | 00, 02, 03, 04 | Product value / missing proof | Public benchmark with raw transcripts: careful baseline vs Plumbref on same repo/tasks, scored for unsupported claims, auditability, reviewer time, and missed contradictions. |
| 4 | First-run friction is real: MCP config, repo-specific setup, agent instructions, restart/reload, and possible client noncompliance. | 00, 02, 03, 05 | First-run friction | One clean “fresh user” install/config transcript per target client, starting from `pipx install` and ending with a successful first answer. |
| 5 | Gate semantics can create false confidence: missing checks may still allow answering, and JSON `verdict: Supported` can diverge from gate qualifications. | 01, 02, 03, 04, 05 | Technical trust | Fix or document JSON/gate semantics, then add tests proving qualified gated answers cannot be consumed as fully supported by integrations. |

**2. Contradictions Between Reviewers**

There are few direct contradictions. The main tension is wording:

- Some reviewers call the gate “proven” because real downgrade logic and tests exist.
- Technical-trust reviewers object that it is not a hard reliance block and can still produce `can_answer: true` or JSON `verdict: Supported`.

That is not a factual contradiction. It means the gate exists, but the public wording should not imply complete enforcement.

All reviewers converge on the same adoption verdict: **would try once**.

**3. Claims To Narrow Immediately**

- “verifies claims” → “records and gates agent-checked local evidence for risky repo claims.”
- “safe-to-rely-on” → “safer to rely on within checked local evidence.”
- “report gate blocks unsupported confidence” → “downgrades or qualifies answers when required recorded checks are missing.”
- “works naturally in Codex/Claude/Cursor” → “can be configured for MCP-capable clients; live client proof is pending.”
- “replaces vague ‘are you sure?’ loops” → “turns some ‘are you sure?’ checks into recorded claim/evidence workflows.”
- “beats prompting plus `rg`” → do not claim until benchmarked.
- “reduces token spend” → keep low and caveated; not a primary adoption claim.
- “CI/PR risk checks” → describe as advisory wording/path checks, not full verification.

**4. Claims Currently Supported**

- Plumbref is local-first, with no hosted service or model API dependency shown in the repo.
- MCP and CLI surfaces exist.
- It stores structured sessions: claims, searches, evidence, judgments, reports.
- Supported judgments require evidence and contradiction-pass metadata.
- Reports provide inspectable Markdown/JSON receipts.
- Built-in templates and tests exist.
- The SSO fixture demonstrates the intended workflow shape.
- Export/diff/rerun artifacts exist, though rerun is still agent-instructed.

**5. What To Ask Real Users**

Ask at least these:

1. What risky repo claims do you currently repeat to support, PMs, PRs, releases, or customers?
2. What do you do today instead: `rg`, tests, code review, prompts, AGENTS rules, static tools?
3. Would you configure MCP for this, or is that already too much tax?
4. Did Plumbref change the final wording you would have used?
5. Did the report make the answer more trustworthy, or just more ceremonial?
6. What part felt least trustworthy: claim extraction, search adequacy, judgment labels, or setup?
7. Would you want this in chat only, PR review, CI, release-note review, or support-answer review?
8. After one use, would you run it again next week without being reminded?

**6. Two-Week Feedback Plan**

Week 1:

- Recruit 5 real target users: engineers already using Codex, Claude Code, Cursor, or similar on active repos.
- Use only real repos, not Plumbref fixtures.
- Give them one setup path and one risky prompt pattern.
- Observe install/config without intervening unless blocked.
- Capture: time to first successful run, config failures, whether the agent calls Plumbref, final answer quality, and whether they trust the report.
- Run one task per user where they would normally use careful prompting plus `rg`.

Week 2:

- Run the same or similar task with Plumbref.
- Ask users to compare Plumbref against their normal workflow.
- Collect raw transcripts, generated reports, and user comments.
- Score each run on: unsupported final claims, useful qualifications, evidence clarity, setup pain, and likelihood of reuse.
- Identify whether the winning use case is support-facing answers, PR summaries, migration risk, downstream-consumer checks, or release notes.
- Update README claims based only on observed results.

**Most honest current one-sentence pitch**

Plumbref is a local MCP tool that helps coding agents turn risky repo claims into recorded searches, cited snippets, conservative judgments, and safer wording before you rely on them.

**Most important next artifact**

A captured named-client first-run transcript on a non-Plumbref repo, including setup, real tool calls, final inline answer, generated report, and comparison against careful prompting plus `rg`.

**Current verdict**

would try once.