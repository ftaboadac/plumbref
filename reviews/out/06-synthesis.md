## 1. Top 5 Adoption Blockers

| Rank | Blocker | Reviewers | Type | Smallest artifact that reduces it |
|---:|---|---|---|---|
| 1 | The lead claim “verifies AI codebase claims” is stronger than the product can honestly support. Plumbref structures and records a checking workflow; the agent still extracts claims, chooses searches, summarizes evidence, and records judgments. | 00, 01, 02, 03, 04, 05 | Technical trust / positioning | Rename the core claim everywhere to “helps agents check and record risky repo claims,” plus one short trust-boundary box explaining what Plumbref enforces and what remains agent judgment. |
| 2 | No captured real first-run in a named MCP client. The current demo is expected output, not proof that Codex/Claude/Cursor reliably uses the tool from install to answer. | 00, 02, 03, 04, 05 | First-run friction / missing proof | A public transcript: install, config location, `doctor`, exact prompt, MCP tool calls, final inline answer, generated report path. Use one named client. |
| 3 | The “gate” is not strict enough for the strongest trust language. Required searches can be syntactic, contradiction checks are agent-supplied, some missing checks still allow qualified output, and one demo artifact shows `safe_to_answer` with zero search traces. | 01, 02, 03, 04, 05 | Technical trust | One regression test and fixture proving `safe_to_answer` is impossible unless required searches, contradiction searches, evidence snippets, categories, and budget checks are recorded and tied to the supported claim. |
| 4 | Value over careful prompting plus `rg` is unproven. Reviewers agree the real value is audit trail and discipline, not better code discovery. That is useful, but narrow. | 02, 04, 03, 00, 05 | Product value / missing proof | A side-by-side benchmark on 5-10 realistic repo-claim tasks: careful prompt + `rg` vs Plumbref-guided agent, judged by missed contradictions, unsupported final claims, unchecked areas, and auditability. |
| 5 | Positioning implies broader maturity than exists: “any MCP-capable client,” “living checked claims,” CI/PR checks, token savings, field migration/downstream consumers, and “safe to rely on” all outrun current proof. | 00, 01, 02, 03, 04, 05 | Positioning / missing proof | A claim table in README with three labels only: proven, partial, not yet. Move partial claims below the first concrete demo. |

## 2. Claims To Narrow Immediately

- “Plumbref verifies AI codebase claims before you rely on them.”
  Narrow to: “Plumbref helps coding agents check risky repo claims and leave an evidence trail.”

- “Evidence gate.”
  Narrow to: “Evidence workflow” or “recorded claim-check workflow” until the gate is truly non-bypassable.

- “Safe to rely on.”
  Narrow to: “Supported by checked local evidence” and say it is not global truth.

- “Any MCP-capable client can launch Plumbref.”
  Narrow to named clients only after captured transcripts exist.

- “Living checked claims.”
  Narrow to: “Exportable checked-claim artifacts with rerun instructions.”

- “PR/CI risk checks.”
  Narrow to: “Advisory explicit-claim checks for changed files.”

- “Reduce token spend.”
  Narrow to: “Dogfood runs suggest lower source-token volume; benchmark not done.”

## 3. Claims Currently Supported

- Local-first repo search and bounded evidence reads.
- MCP server and CLI exist.
- Reports can include claims, evidence, judgments, unchecked areas, limits, and safer wording.
- Supported judgments require evidence and a contradiction-pass flag.
- Templates define required searches, contradiction searches, categories, and budgets.
- The SSO fixture demonstrates a useful contradicted-claim flow.
- The product is best used inside an agent chat, not as a manual CLI-first tool.
- Plumbref is not an autonomous verifier and does not inspect production data, external systems, or runtime truth.

## 4. What To Ask Real Users

Ask target users after they try the actual first-run flow:

1. What risky agent claim would you have wanted checked this week?
2. Would this output change what you said in a PR, ticket, support note, or merge decision?
3. Was the report clearer than asking the agent to cite files and run `rg`?
4. Did you trust the final wording more, less, or the same?
5. Where did setup or agent behavior fail?
6. Which unchecked areas were useful versus noise?
7. Would you run this weekly, only before risky claims, or not again?
8. What artifact would make this acceptable for your team: inline answer, report, PR comment, CI warning, or checked-claim file?

## 5. Two-Week Feedback Plan

Week 1:

- Day 1: Narrow README claims and add the trust-boundary box.
- Day 2: Produce one captured first-run transcript in a named client using the SSO fixture.
- Day 3: Fix or quarantine stale/damaging demo artifacts, especially any `safe_to_answer` report with zero searches.
- Day 4: Recruit five real target users: engineers who already use Codex, Claude Code, Cursor, or similar agents on active repos.
- Day 5: Run two observed sessions. Give them the install docs, not live coaching except for blocking setup failures.

Week 2:

- Day 6-7: Run three more observed sessions.
- Day 8: Compare each session against a baseline prompt: “cite files, search contradictions, list unchecked areas.”
- Day 9: Summarize where Plumbref changed the answer, added friction, or produced no extra value.
- Day 10: Decide whether the next artifact is a stricter gate test, better first-run docs, or benchmark report. Do not add new claims until one of those lands.

- most honest current one-sentence pitch: Plumbref is a local MCP/CLI harness that makes a coding agent record repo searches, bounded evidence snippets, contradiction checks, and conservative judgments before returning a source-backed answer.

- most important next artifact: a captured, reproducible first-run transcript in one named MCP client.

- current verdict: would try once.