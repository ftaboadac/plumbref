# Positioning And Rerun/Diff Implementation Plan

Date: 2026-06-13

This plan tracks the next product and messaging work after the paired private
repo validation. The current conclusion is:

> Plumbref gives you a careful-agent workflow even when you cannot trust that
> the agent will naturally behave like a careful senior engineer.

The larger product direction to validate is:

> Your team's verified claims about how the codebase works, updated when the
> code changes.

## Goals

- Move Plumbref away from "agent mistake catcher" positioning.
- Lead with careful, repeatable repo-answer verification.
- Treat the report as proof of verification work, not the product itself.
- Validate whether rerun/diff can become a second product mode: a claim test
  suite for institutional knowledge.
- Avoid public token-savings claims until repeated-workflow savings are
  measured.

## Non-Goals

- Do not claim Plumbref always beats a careful agent.
- Do not claim Plumbref always uses fewer tokens.
- Do not build a broad report UI before validating the rerun/diff screenshot.
- Do not publish a "careless agent vs Plumbref" comparison as the primary
  public proof yet.

## Phase 1: Tighten Current Materials

Status: completed

Deliverables:

- Update `docs/product-strategy.md` with the careful-agent workflow line.
- Add repeatability as a first-class value pillar, separate from correctness
  and token optimization.
- Update `docs/private-repo-paired-agent-validation-2026-06-13.md`:
  - Rename "Aggregate Readout" to "Observed Outcomes Across Five Cases".
  - Replace repeated "no material baseline miss" phrasing with auditability and
    verification-trail language.
  - Emphasize zero hallucinated supported final claims, one visible
    self-correction, and one clear material improvement.
- Update `docs/launch-checklist.md` so public demo requirements mention:
  - claim statuses
  - contradiction checks
  - rerun/repeatability potential
  - explicit qualifications

Definition of done:

- A reader can understand that Plumbref is workflow enforcement for careful
  repo answers.
- The validation doc no longer feels like a statistical benchmark.
- Token savings are framed as future/repeated-workflow upside, not the current
  primary proof.

## Phase 2: Public Example Extraction

Status: completed

Audience and distribution target:

- Primary target: a short README or blog-style example that can later become a
  Show HN post.
- Timing: do not publish it as the main launch artifact until Phase 3 proves
  the rerun/diff output is compelling.
- Purpose: make the current validation understandable while teeing up the
  larger "verified claims that stay true" story.

Deliverables:

- Create a short public-safe writeup from the private validation.
- Feature only the two strongest cases:
  - Routing distinction: Plumbref separated concepts the baseline blurred.
  - Visible self-correction: Plumbref contradicted a wrong draft assumption
    before final answer.
- Abstract private implementation names and paths.
- Produce one short screenshot brief for the current report-style demo.

Definition of done:

- The example does not require saying agents are bad.
- The reader can see the artifact they would want for their own risky repo
  question.
- The strongest examples are visible in the first screen or first few
  paragraphs.

## Phase 3: Rerun/Diff Product Spike

Status: completed MVP

Goal:

Prove Plumbref can compare the same verified repo question across two code
states and show which claims changed status or evidence.

Timebox:

- Spend one to two implementation days on a plain Markdown diff before building
  any UI or demo layer.
- If the Markdown diff is not readable and screenshot-worthy by then, stop and
  rethink the output format before continuing.

Early product decision:

- Stable claim IDs are required for rerun/diff.
- Do not make fuzzy claim matching the core of the proof.
- MVP approach:
  - The first report assigns stable claim IDs scoped to the report identity.
  - A rerun preserves those IDs by rechecking the previous report's claim texts
    against the new code state.
  - New claims can be added later, but the first diff mode focuses on whether
    previously verified claims still hold.

Candidate demo shape:

```text
Question: How does SSO eligibility work?

March report:
- Claim A: supported
- Claim B: supported
- Claim C: qualified

June rerun:
- Claim A: supported, evidence changed
- Claim B: contradicted
- Claim C: supported

Summary:
Business rule changed: SSO no longer depends on condition X; it now depends on
condition Y.
```

Preferred claim type:

- Business rules, because they drift when product requirements change.

Good candidate domains:

- SSO eligibility and provider selection.
- Payroll or leave closure rules.
- Feature flag targeting rules.
- External API auth boundary.

Deliverables:

- Define a report identity key:
  - normalized question
  - template id
  - repo identifier
  - git commit or tree hash
- Define stable claim IDs before implementing the diff:
  - report identity hash
  - sequential claim id, for example `claim-001`
  - persisted claim text
  - optional claim kind, such as behavior, business rule, integration, or limit
- Add a comparison model for:
  - claim id
  - claim text
  - claim status
  - evidence files
  - evidence line ranges
  - contradiction checks
  - final answer summary
- Implement an MCP-first diff tool:
  - tool name: `plumbref_diff_reports`
  - input: old report JSON, new report JSON
  - output: structured summary, structured claim changes, and Markdown diff
- Keep a local CLI wrapper for development and debugging:
  - command: `plumbref diff-reports OLD.json NEW.json`
  - output: Markdown diff report
- Include status transitions:
  - supported -> contradicted
  - supported -> qualified
  - supported -> not found
  - not found -> supported
  - evidence changed, status unchanged
- Include a short "what changed" summary.

Definition of done:

- Given two Plumbref JSON reports for the same question, the tool generates a
  readable diff without inspecting the repo again.
- The diff can identify at least status changes and evidence changes without
  fuzzy matching.
- The output is screenshot-worthy without a custom UI.

Implemented MVP:

- JSON reports now include `report_identity`, `question`, `created_at`,
  `stable_id`, and `stable_id_scope`.
- `plumbref_diff_reports` returns structured summary, structured changes, and a
  Markdown diff through MCP.
- `plumbref diff-reports OLD.json NEW.json` remains as a development/debugging
  wrapper.
- The diff shows status changes, evidence-only changes, added claims, removed
  claims, and unchanged claims.
- Older reports without `stable_id` can be compared by deterministic claim
  order, but that fallback cannot reliably identify added or removed claims.

Phase 3.1 polish:

- Markdown output now has a top summary and separate sections for status
  changes, new claims, removed claims, evidence drift, location-only drift, and
  unchanged claims.
- Status-unchanged evidence drift is labeled as `Status unchanged` instead of
  rendering noisy `supported -> supported` transitions.
- Line-range-only movement is classified as `location_only_drift`, kept out of
  the main material-change count, and shown in a lower-priority section.
- The MCP response keeps structured details for the agent while Markdown stays
  focused on the human artifact.
- Real older reports were diffed after the polish pass. The output was readable
  enough to proceed to Phase 4, but those old reports are not screenshot
  candidates because they predate the new `question` and `stable_id` schema and
  contain private paths.

## Phase 4: Business-Rule Demo

Status: completed fixture proof of concept

Goal:

Create a demo where a meaningful business-rule claim changes across two code
states.

Protocol:

1. Choose one business-rule-heavy question.
2. Run Plumbref against current code.
3. Create a temporary branch or fixture copy with a small, realistic rule
   change.
4. Run the same Plumbref question again.
5. Generate the report diff.
6. Verify the diff does not overstate the change.

Constraints:

- Do not use private repo details in public output.
- If a private repo is used for validation, abstract the demo copy before
  sharing.
- Prefer a small controlled fixture for public screenshots if private details
  would leak.

Definition of done:

- A claim changes status or evidence in a way that an engineer would care
  about.
- The screenshot shows the value without needing a negative agent comparison.
- The demo supports the line: "documentation that stays true."

Completed first pass:

- Ran a controlled public-safe SSO eligibility fixture.
- Before-state claim: SSO only starts when Rippling integration exists or Okta
  is enabled.
- After-state code added `company.sso_enabled` as a third eligibility path.
- `plumbref_diff_reports` produced one material status change:
  `supported -> contradicted`.
- A stable entry-point claim moved line numbers only and was classified as
  `location_only_drift`, outside the material-change count.
- Demo notes are recorded in `docs/sso-business-rule-drift-demo.md`.

Remaining polish:

- Checked-in public fixture files now live under `examples/fixtures/sso-before`
  and `examples/fixtures/sso-after`.
- Stable report artifacts now live under:
  - `examples/reports/sso-eligibility-before.json`
  - `examples/reports/sso-eligibility-after.json`
  - `examples/reports/sso-eligibility-drift-diff.md`
- The checked-in diff reproduces with:
  `plumbref diff-reports examples/reports/sso-eligibility-before.json examples/reports/sso-eligibility-after.json --output /tmp/reproduced-sso-drift-output.md`
- Private-path scans found no private paths in the fixture, reports, diff, or
  demo doc.
- Remaining screenshot polish: crop or omit local report path rows if they
  distract from the status change.

## Phase 5: CI / Scheduled Mode Design

Status: intentionally deferred until the rerun/diff demo has been run several
times

Goal:

Assess whether rerun/diff should become a scheduled workflow.

Design questions:

- How does a team define the claims or questions it wants to monitor?
- Should monitored questions live in a `plumbref.yml` file?
- What should fail CI? Keep this open until after repeated diff demos:
  - contradicted claim?
  - missing evidence?
  - changed evidence only?
  - broad claim now unsupported?
- How should expected drift be acknowledged?
- Should report diffs be committed, attached to CI, or posted as artifacts?

Possible interface:

```yaml
checks:
  - id: sso-eligibility
    question: "How does SSO eligibility work?"
    template: explain_flow
    mode: business_rule
    fail_on:
      - contradicted
      - not_found
  - id: external-api-auth-boundary
    question: "Where is external API auth enforced?"
    template: change_impact
    fail_on:
      - contradicted
```

Definition of done:

- A short design doc explains local CLI, CI, and scheduled usage.
- The failure semantics are based on observed rerun/diff behavior, not guessed
  upfront.
- Intentional business-rule changes have a clear acknowledgment/update path.
- The workflow is conservative and does not create noisy false alarms.
- The workflow still feels like repo-local engineering infrastructure, not a
  hosted AI monitoring product.

## Phase 6: Measurement Plan

Status: not started

Track these separately:

- Answer quality:
  - material baseline misses found
  - visible self-corrections
  - unsupported claims blocked
  - claims qualified before final answer
- Repeatability:
  - rerun reports generated successfully
  - claim status changes detected
  - evidence-only changes detected
  - stale docs/business rules surfaced
- Cost and source context:
  - searches run
  - snippets read
  - unique evidence files
  - source tokens returned
  - cache hit rate
  - reused evidence count
- Usability:
  - time to run first report
  - time to understand report
  - whether screenshot communicates value without explanation

Public claims should only use measurements this plan can support.

## Suggested Build Order

1. Update positioning docs.
2. Clean up the paired validation doc.
3. Extract a short public-safe validation story.
4. Implement JSON-report diff as a small local tool.
5. Run one controlled business-rule rerun/diff demo.
6. Turn the diff output into the primary screenshot candidate.
7. Design CI/scheduled checks only after the diff demo feels compelling.

## Open Questions

- Should rerun/diff ever compare independently generated claims semantically, or
  should rerun mode always recheck the previous report's persisted claims?
- How much evidence text should the diff include versus linking back to the
  two reports?
- Should a changed line range count as drift if the claim remains supported?
- Is the best public demo based on a real abstracted repo or a purpose-built
  fixture?
