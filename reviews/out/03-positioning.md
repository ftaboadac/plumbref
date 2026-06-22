**Verdict: would try once**

Plumbref’s README is much clearer than broad “AI verifier” positioning, but it still leans on a trust promise that is stronger than the public proof. The real user is an engineer already using Codex/Claude/Cursor on a real repo, right before repeating or acting on a risky claim: “only affects onboarding,” “SSO only depends on Okta,” “safe to rename.” That moment is concrete in [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:18), [demo-transcript.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/mcp-stdio-transcript.md:17), and the expected inline answer at [inline-answer.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/expected/inline-answer.md:1).

**Claim Status**

- `Plumbref helps coding agents check risky repo claims before you rely on them` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:10)): **partially proven**. MCP tools, reports, examples, and tests exist; the missing piece is a captured named-client run.
- `report gate` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:12)): **partially proven**. The gate logic is real in [reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:634), but the agent still controls extraction/search/judgment.
- `downgrades answers when required recorded checks are missing` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:44)): **proven by repo/tests**. See missing-gate handling in [reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:680) and tests such as [tests/test_reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/tests/test_reports.py:502).
- `safe-to-rely-on claims` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:68)): **partially proven**. Better as “safe within checked local evidence,” because Plumbref does not independently know whether the claim set/searches were sufficient.
- `You should not need to manually run verification commands during normal use` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:91)): **unproven publicly** until a real Codex/Claude/Cursor transcript exists.
- `Plumbref is local-first... no model API... no hosted service` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:35)): **proven by repo**. Package deps are local Python/MCP/Pydantic/Typer in [pyproject.toml](/Users/facundotaboada/Documents/GitHub/plumbref/pyproject.toml:26).
- `Current demo artifacts` / historical reports ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:269)): **credible because caveated**. The README correctly says historical reports may be stale at [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:274).
- Checked-claim rerun/living-fact direction: **partially proven**. Export/diff/rerun packet exists in [checked_claims.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/checked_claims.py:25), but rerun is still agent-instructed, not automatic.

**Words That Sound Inflated Or Founder-Internal**

- “report gate” is useful but loaded. It implies enforcement at answer time; the actual gate is only as good as the recorded claims and traces.
- “safe-to-rely-on” is motivating, but dangerous unless always paired with “within checked local evidence.”
- “source-grounded workflow,” “status semantics,” “broad-claim detection,” and “checked claims” are internally meaningful, but the README needs to keep translating them into user moments.
- “replace vague ‘are you sure?’ loops” ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:32)) is good positioning, but still needs a direct before/after proof.

**Too Broad For Current Proof**

The most overextended claim is not in the limits section; it is the implied product flow: install once, ask naturally, agent uses Plumbref, and you get a reliable reliance answer. The repo proves the tool protocol and gate mechanics. It does not yet prove that a normal MCP client reliably follows the workflow without handholding. The first-run example explicitly admits this gap at [examples/first-run/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/README.md:75) and [mcp-stdio-transcript.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/mcp-stdio-transcript.md:3).

**Missing Proof**

The missing artifact is a clean live transcript from one named MCP client. It should show install/config, the exact user prompt, visible tool calls, final inline answer, and generated report path. Right now the README points to a fixture, not a captured client session ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:181)).

Also missing: a comparison against the substitutes in the packet: careful prompting plus `rg`, asking the agent for citations, and contradiction-search instructions. Without that, the differentiation claim is plausible but not proven.

**Clearest One-Sentence Description**

Plumbref is a local MCP tool that makes coding agents turn risky repo claims into recorded searches, cited source snippets, conservative judgments, and safer wording before you rely on the answer.

**Remove, Narrow, Or Move Lower**

- Narrow “safe-to-rely-on” everywhere to “safe to rely on within checked local evidence.”
- Move token-reduction material lower or keep it caveated; the strongest public reason is trust, not token savings.
- Keep historical reports lower, as currently done; their stale-reference warning is necessary.
- Do not lead with “verified” unless the sentence names the evidence trail and the agent’s role.

**Concrete User Moment**

Yes, the README creates a concrete “I want this before changing risky code” moment. The examples at [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:18) are the strongest public copy. The weak point is proof of the smooth first run.

**Single Artifact That Would Change My Mind**

A captured Codex or Claude Code first-run transcript on a fresh checkout: one risky claim, Plumbref MCP tool calls, final inline answer, report path, and a short comparison showing what a careful prompt plus `rg` missed or left unrecorded.