# Private Repo Paired Agent Validation

Date: 2026-06-13

This was a paired validation run against a private production monorepo. The
target repository was treated as read-only. Plumbref config, cache, and report
artifacts were written under `/tmp/plumbref-unbiased-validation-20260613/`, not
inside the target repository.

The raw Plumbref reports contain private file paths and source excerpts, so this
document keeps the results at the workflow level. It records what happened in
the run, including where Plumbref added auditability rather than a different
answer.

## Protocol

Five realistic repo-investigation questions were selected before running the
paired tests:

1. How external API requests are authenticated and authorized before changing
   token validation.
2. How third-party webhooks are validated and routed before changing webhook
   authentication.
3. How chat history access is controlled before changing authorization or
   visibility.
4. How feature flags are evaluated and exposed to the frontend before changing
   flag targeting.
5. How a frontend leave-management flow gates access and chooses URL-driven
   tabs before changing routing.

Each question was run two ways:

- Baseline agent: a fresh agent with no forked context, using normal repo
  search and source reading.
- Plumbref agent: a fresh agent with no forked context, using the Plumbref
  verification workflow and writing reports outside the target repo.

The baseline was not intentionally weakened. It was allowed to search broadly,
read source ranges, cite files, and state caveats. That made this a strong
baseline, closer to a careful senior engineer than to a casual prompt.

## Limitations

- This is a credible internal validation, not a scientific benchmark.
- The coordinator knew the project and had prior thread context, but the paired
  subagents were launched without forked context.
- Baseline runs reported approximate snippets and searches, not full provider
  token accounting.
- Plumbref token estimates are source-text estimates using the report metrics,
  not total model reasoning tokens or billing records.
- Some Plumbref runs used cache hits within their own artifact directory. Those
  cases are noted in the metrics rather than normalized away.

## Observed Outcomes Across Five Cases

| Case | Baseline source read estimate | Plumbref metrics | Differential value |
| --- | --- | --- | --- |
| External API auth | About 34 source snippets plus 7 targeted search result sets | 54 search traces, 35 evidence snippets, 18 unique files, about 10,894 source tokens | Plumbref made the migration boundary and contradiction checks auditable, even though the final answer matched the careful baseline. |
| Webhook validation | About 22 focused snippets plus searches | 41 searches, 48 traces, 23 snippets, 13 unique files, about 7,625 source tokens | Core answer matched baseline. Plumbref forced an explicit "not established" qualification for retry/idempotency. |
| Chat history access | About 25 source snippets plus searches | 45 searches, 48 traces, 25 snippets, 9 unique files, about 9,839 source tokens | Core answer matched baseline. Plumbref forced contradiction checks around the create-only API claim and separated API visibility from admin visibility. |
| Feature flags | About 30 snippets plus searches | 33 searches, 34 traces, 20 snippets, 15 unique files, about 9,622 source tokens | Plumbref contradicted an internal draft assumption that the repo used a different flag platform, then corrected the answer before final. |
| Leave-management routing | About 25 snippets, roughly 2,000-2,500 displayed lines, plus searches | 24 searches, 24 traces, 19 snippets, 13 unique files, about 4,585 source tokens | Clear Plumbref win: it separated the list `view` tab from the drawer `tab`, and separated the old list-page gate from the newer detail-route gate. |

Plumbref report-side totals across the five cases:

- Claim statuses: 34 supported, 1 contradicted, 1 not found
- Evidence snippets: 122
- Unique evidence files, summed per report: 68
- Source tokens returned, summed per report: about 42,565
- Search traces, summed per report: 208

The main quality signal was not a high count of baseline failures. The stronger
signal was that Plumbref produced five final answers with no observed
unsupported final claims, one visible self-correction before final answer,
several explicit qualifications, and one clear material improvement over the
careful baseline.

## Case Notes

### External API Auth

Both runs found the important architecture: public REST traffic is validated at
the ingress boundary before Django handles the request, while Django-side OAuth
handling is currently advisory for the relevant migration path. Both runs also
identified webhook exceptions and the lack of active per-endpoint scope
enforcement.

Plumbref's value here was process evidence: the report shows the required
searches, contradiction checks, evidence snippets, and final supported claims.
The useful public claim from this case is repeatability, not correctness
superiority.

Report:
`/tmp/plumbref-unbiased-validation-20260613/external-api/reports/2026-06-13/be939dcd-382e-4ac1-9a7c-effd20a88919.md`

### Webhook Validation

Both runs found the route, signature validation, debug/no-secret bypasses,
separate ingress path, and forwarding behavior. The baseline was already strong.

Plumbref added a useful qualification: retry/idempotency behavior for the
Django webhook layer was not established by the checked evidence. That is the
kind of unsupported implication Plumbref is meant to make visible.

Report:
`/tmp/plumbref-unbiased-validation-20260613/twilio-webhooks/reports/2026-06-13/32158904-7269-4f6d-a251-b53b0d3dd4d6.md`

### Chat History Access

Both runs found that the checked API surface is create-only, requires
authentication, enforces user ownership on message creation, returns 404 for
cross-user conversation access, and exposes a separate read-only admin surface.

Plumbref added discipline: contradiction searches for the "create-only/no read
API" claim surfaced the docs/code mismatch, and admin visibility had to be
handled as a separate surface instead of being collapsed into "users only see
their own chats." The final facts matched the strong baseline, but the
verification trail made the support and limits inspectable.

Report:
`/tmp/plumbref-unbiased-validation-20260613/chat-history/reports/2026-06-13/7af68a47-f602-47b2-a798-829b8e37ee37.md`

### Feature Flags

The baseline found the local Django/Waffle flag system, backend services,
frontend API exposure, admin-editing limits, caching behavior, and operational
gotchas.

The Plumbref run initially carried a wrong draft assumption that the repo used
a different flag platform. Plumbref marked that claim contradicted, found no
supporting evidence for it, and forced the answer back to the local Waffle-based
implementation. The final answer was not better than the baseline, but the
correction is visible in the report instead of hidden in the agent's private
reasoning.

Report:
`/tmp/plumbref-unbiased-validation-20260613/flags/reports/2026-06-13/3cbd91d1-5252-4a46-94e6-1693e99676df.md`

### Leave-Management Routing

This was the clearest differential case.

The baseline correctly described the drawer `tab` query parameter and the newer
detail route gate, but it did not clearly separate all of the routing concepts.
Plumbref separated:

- The old list page's lightweight logged-in gate.
- The newer detail route's server-side auth-token and feature-flag gate.
- The list Active/Pending tab, controlled by `view`.
- The drawer's internal tab, controlled by `tab`.
- The docs/code mismatch where docs mention an older dynamic route name while
  current source uses the newer route parameter.

This is the strongest example from the run of Plumbref getting a materially
useful distinction that the baseline did not fully surface.

Report:
`/tmp/plumbref-unbiased-validation-20260613/leave-management/reports/2026-06-13/d27e8690-9f26-4597-b884-62bb2f92cb31.md`

## Cost Takeaway

This run does not support a public claim that Plumbref is always cheaper than a
careful agent. Against this strong baseline, Plumbref usually read a comparable
number of snippets and often ran more searches because it performed explicit
claim and contradiction passes.

The better-supported cost claim is narrower:

Plumbref bounds and records the source context used to support an answer. In
some cases, especially the frontend routing case, it used tighter evidence than
the baseline. Across the full run, the larger value was not raw token savings;
it was that every answer came with source-token accounting, claim statuses,
contradiction checks, and a repeatable report.

## Value Claim Supported By This Run

The strongest honest claim is:

Plumbref helps coding agents produce more trustworthy repo answers by forcing
source checks, contradiction checks, and explicit qualifications before the
answer is treated as supported.

Against a strong normal-agent baseline, Plumbref produced five final answers
with no observed unsupported final claims, one clear material improvement,
several explicit qualifications, one visible contradicted draft assumption, and
five inspectable verification reports. It did not prove that agents are bad,
and it did not prove universal token savings. It showed the kind of
verification artifact a careful engineer would want before touching a risky
flow.

## Target Repo Hygiene

The target repository remained clean at the end of the run. Artifacts were kept
under `/tmp/plumbref-unbiased-validation-20260613/`.
