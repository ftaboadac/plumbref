# Benchmark And User Validation

This file tracks the validation package for the checked-claims product:

- captured live Codex first-run transcript
- benchmark against careful prompting plus `rg`
- real-user sessions to prove repeat usage

## Benchmark Pair: SSO Fixture

Question:

```text
The agent said SSO only depends on Okta. Check that before I tell support.
Draft answer to check: SSO only depends on Okta.
```

Repository:

```text
examples/fixtures/sso-before
```

### Run A: Codex Plus Plumbref MCP

Artifact:

- [codex-live-first-run-2026-06-22.md](codex-live-first-run-2026-06-22.md)
- [transcripts/codex-live-sso-2026-06-22.jsonl](transcripts/codex-live-sso-2026-06-22.jsonl)
- [reports/codex-live-sso-2026-06-22.md](reports/codex-live-sso-2026-06-22.md)

Result:

- Correctly contradicted the draft.
- Produced a durable Markdown and JSON report.
- Recorded 1 claim, 5 searches, 2 evidence snippets, and 1/1 contradiction
  pass.
- Exposed first-run enum friction before recovering.

### Run B: Codex With Careful Prompting Plus `rg`

Artifact:

- [transcripts/codex-baseline-rg-sso-2026-06-22.jsonl](transcripts/codex-baseline-rg-sso-2026-06-22.jsonl)

Result:

- Also correctly contradicted the draft.
- Used `rg --files`, one broad `rg` query, and two bounded `sed` reads.
- Returned a concise answer with evidence paths and uncertainty.
- Did not create reusable checked-claim state or a structured report.

### Current Read

On this small fixture, careful prompting plus `rg` is enough to reach the same
substantive answer. Plumbref's advantage is not raw correctness on this case; it
is the durable evidence trail, answer gate, report artifact, and repeatable
claim format. The benchmark needs harder cases where those properties matter:

- multiple claims with mixed support
- broad claims that require contradiction passes
- changed code where rerun/diff matters
- larger repos where bounded snippets and cache reuse reduce blind reading
- support-facing answers where a report receipt changes user trust

## Benchmark Pair: Customer Exports Fixture

Question:

```text
Support wants to say customer exports are CSV-only, available to all paid accounts, never include deleted records, and only go to S3. Check that before we update the help center.
Draft answer to check: Customer exports are CSV-only, available to all paid accounts, never include deleted records, and only go to S3.
```

Repository:

```text
examples/fixtures/customer-exports
```

### Run A: Codex Plus Plumbref MCP

Artifacts:

- [transcripts/codex-plumbref-customer-exports-clean-2026-06-23.jsonl](transcripts/codex-plumbref-customer-exports-clean-2026-06-23.jsonl)
- [reports/codex-plumbref-customer-exports-clean-2026-06-23.md](reports/codex-plumbref-customer-exports-clean-2026-06-23.md)
- [reports/codex-plumbref-customer-exports-clean-2026-06-23.json](reports/codex-plumbref-customer-exports-clean-2026-06-23.json)

Earlier friction run:

- [transcripts/codex-plumbref-customer-exports-2026-06-22.jsonl](transcripts/codex-plumbref-customer-exports-2026-06-22.jsonl)

Result:

- Correctly split the draft into 4 atomic claims.
- Recorded 3 contradicted claims and 1 uncertain/qualified claim.
- Recorded 4/4 contradiction passes.
- Recorded 5 evidence records from 3 bounded snippet reads.
- Wrote Markdown and JSON reports.
- Started successfully with first-run aliases: `mode="verify"` and
  `output_modes=["inline_answer","report"]`.
- Accepted natural agent aliases in the clean run: `type="data_outputs"`,
  `status="refuted"`, and `status="partially_supported"`.
- No failed MCP tool calls were found in the clean transcript.

Inline answer:

```text
Plumbref found source evidence against the answer as written.

Say with qualification:
- uncertain: Customer exports are available to all paid accounts. Limits: The fixture does not define a complete paid-plan taxonomy beyond pro and enterprise examples.

Do not rely on:
- contradicted: Customer exports are CSV-only.
- contradicted: Customer exports never include deleted records.
- contradicted: Customer exports only go to S3.

Safer wording:
- Customer exports are available to pro and enterprise accounts unless the account is on legal hold.
- Customer exports support CSV and JSON; enterprise beta PDF exports are also available when enabled.
- Deleted records are excluded by default, but enterprise admin exports include deleted records.
- Customer exports can go to S3; verified-email accounts outside the EU can also receive exports by email.

Verification: 4 claim(s) (contradicted=3, uncertain=1); 5 evidence record(s); 3 bounded snippet read(s); 4/4 contradiction pass(es).
```

### Run B: Codex With Careful Prompting Plus `rg`

Artifact:

- [transcripts/codex-baseline-rg-customer-exports-2026-06-22.jsonl](transcripts/codex-baseline-rg-customer-exports-2026-06-22.jsonl)

Result:

- Also correctly rejected the draft answer.
- Used `rg --files`, one broad `rg` query, and bounded reads of docs, checks,
  and implementation.
- Returned exact evidence paths and a useful uncertainty note.
- Did not produce reusable claim state, a contradiction-pass ledger, or a
  report artifact.

### Current Read

This harder fixture still does not prove Plumbref is more correct than a
careful agent. It does show the product distinction more clearly:

- The baseline is faster and sufficient for a careful one-off answer.
- Plumbref is heavier, but produces a reusable claim/evidence/report object.
- The Plumbref transcript is easier to audit after the fact because each draft
  clause has its own status, evidence, contradiction notes, and safer wording.

Positioning implication: lead with "recorded, rerunnable verification trail for
risky repo claims", not "better than careful prompting plus `rg`."

## Benchmark Scorecard

For each benchmark case, score both runs:

| Dimension | Careful prompt + `rg` | Plumbref MCP |
| --- | --- | --- |
| Final answer correct | yes/no | yes/no |
| Broad claim qualified | yes/no | yes/no |
| Evidence paths cited | count | count |
| Searches visible | shell transcript only | report trace |
| Claim state reusable | no | yes/no |
| Report generated | no | yes/no |
| User can rerun later | manual | yes/no |
| Friction observed | notes | notes |

## Real-User Session Protocol

Do not fabricate this. A repeat-usage claim needs real people using Plumbref on
their own repo or a realistic internal repo.

Minimum useful proof:

- 3 named users or teams
- 2 sessions per user
- at least 1 session on the user's own codebase
- at least 1 repeated/rerun claim per user
- raw transcript or screen-recorded notes with permission
- final answer, report path, and whether they reused the result

Session script:

1. Ask the user for one risky repo answer they would normally double-check.
2. Have them run their normal agent flow first, without Plumbref.
3. Have them run the same question with Plumbref MCP.
4. Capture where they slowed down, trusted it, ignored it, or asked for more.
5. One week later, ask whether they reused the report or reran the claim.

Evidence to collect:

- client name and version: Codex, Claude, Cursor, or other
- repo type and size, without private source disclosure
- question under review
- final inline answer
- generated report path
- number of claims, searches, evidence snippets, and contradiction passes
- whether the user would use it again
- what blocked repeat use

Pass threshold for "would use":

- At least 2 of 3 users voluntarily use it on a second question.
- At least 1 user reruns or references a prior report.
- Users can explain the value without prompting as either "caught an overclaim",
  "gave me a report I could trust/share", or "made the agent check the right
  paths."
