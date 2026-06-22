Scope: I did not read `reviews/out/`.

**Actual User**
The real user is an engineer already using a coding agent on a real repo, at the moment before they repeat or act on a risky claim: “only affects onboarding,” “safe to rename,” “SSO only depends on Okta.” The README supports that moment in the example prompts at [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:18), but it still speaks too much to “coding agents” as the subject rather than the engineer deciding whether to trust an answer.

Not the actual user: generic developers, support teams, people looking for static analysis, or people wanting an autonomous verifier.

**Claim Assessment**

| Claim | Status | Why |
| --- | --- | --- |
| “Plumbref verifies AI codebase claims before you rely on them” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:10) | partially proven | Repo proves a local workflow for recording searches, evidence, judgments, and reports. It does not independently extract claims or decide truth; README admits this later at [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:321). |
| “It gives coding agents an evidence gate” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:12) | partially proven / too broad | Supported judgments require evidence and contradiction passes in code, but the agent still chooses claims/searches/judgments. Template evidence-category gate coverage is not uniformly strict for every supported claim; see gate logic around [plumbref/reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:694). |
| “Local-first… no model API, no upload, no database/vector store/hosted service” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:35) | proven by repo | Dependencies are local CLI/MCP/Pydantic/Typer only in [pyproject.toml](/Users/facundotaboada/Documents/GitHub/plumbref/pyproject.toml:26); code search does not show model/API clients. |
| “MCP server for agent-driven verification” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:95) | proven by repo | MCP tools exist in [plumbref/mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:33). |
| “Any MCP-capable client can launch Plumbref” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:147) | unproven | Generic stdio config is shown, but there is no captured first-run transcript for a named client. |
| “You should not need to manually run verification commands during normal use” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:79) | unproven / aspirational | Depends on agent integration and behavior. Repo has tools and instructions, not proof of smooth normal use. |
| Dogfood metrics: 3 sessions, 12 claims, 29 searches, etc. [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:260) | proven but narrow | Backed by [docs/real-workflow-test-results.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/real-workflow-test-results.md:17), but all are Plumbref-on-Plumbref runs. |
| “Reports are inspectable receipts” [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:201) | proven | Example reports show claims, evidence, limits, contradiction passes, and measurement; e.g. [examples/reports/reliance-check-overclaim-demo.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/reliance-check-overclaim-demo.md:19). |
| “Living/diffable facts” implied by report diffs [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:232) | partially proven | Diff machinery and examples exist, e.g. [examples/reports/sso-eligibility-drift-diff.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/sso-eligibility-drift-diff.md:1), but rerun is currently a packet/instruction flow, not automatic re-verification. |

**Language That Sounds Inflated Or Internal**
- “verifies” is too strong as the lead verb. Better supported: “helps coding agents check and record.”
- “evidence gate” sounds like hard enforcement. Current proof supports “evidence trail” or “claim-check workflow.”
- “safe to rely on” is motivating but legally/semantically heavy. It needs the trust boundary immediately beside it.
- “source-grounded workflow,” “status semantics,” “report artifacts,” “verification playbooks,” and “reliance decisions” read founder-internal.
- “Batteries Included” is generic and makes the project sound broader than the narrow value moment.

**Missing Proof**
The biggest missing artifact is a clean public first-run transcript in one named MCP client, from install/config to user prompt to inline answer to report path. The current first-run example is labeled as intended/expected output, not captured execution: [examples/first-run/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/README.md:3).

Also missing:
- public external-repo example, not Plumbref checking Plumbref
- comparison against careful prompting plus `rg`
- proof that required template checks cannot be bypassed for all “safe” claims
- an example where a user would actually change code differently because of the output

**Clearest Supported One-Sentence Description**
Plumbref is a local MCP/CLI harness that makes a coding agent record repo searches, bounded evidence snippets, contradiction checks, and conservative claim judgments before returning a source-backed answer.

**Remove, Narrow, Or Move Lower**
- Narrow the headline from “verifies AI codebase claims” to “helps agents check and record risky repo claims.”
- Replace “evidence gate” unless every safe claim is strictly blocked without required traces.
- Move dogfood metrics lower and label them as self-dogfood only.
- Move “Batteries Included” below the concrete example.
- Remove or narrow “Any MCP-capable client” until a named-client transcript exists.
- Keep the three user prompts high; they are the best positioning in the README.

**Concrete Moment**
Partially. The prompts at [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:20) create a real “check this before I trust it” moment. The README does not yet fully create “I want this before changing risky code,” because the proof is mostly self-referential reports and expected examples rather than a captured workflow on a recognizable risky engineering change.

**Verdict**
would try once

Single artifact that would most change my mind: a captured, reproducible first-run transcript in one named MCP client showing a risky claim downgraded or contradicted, with the exact inline answer and generated report artifact.