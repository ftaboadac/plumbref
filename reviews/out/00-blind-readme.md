**1. What I Think It Is**

Plumbref is a local-first MCP/CLI harness that helps a coding agent turn a repo answer into checked claims, local `rg` searches, bounded evidence snippets, conservative judgments, and an inline/report artifact.

Important distinction: it is not an autonomous verifier. The README admits “the agent still extracts claims and reasons over evidence” ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:46)), and the MCP tool stores “atomic claims extracted by the agent” ([plumbref/mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:100)).

**2. Who It Is For**

Engineers using MCP-capable coding agents: Codex, Claude Code, Cursor, etc. The clearest target is someone about to rely on an AI answer about repo behavior, change impact, downstream consumers, field migration risk, or support-facing wording ([docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:91)).

Not obviously for casual CLI users. The README says the CLI is mainly setup/debug/reporting, not the primary product surface ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:79)).

**3. Concrete Job**

It helps answer: “The agent said X about this codebase. What can I safely repeat or act on?”

Concrete examples:
- “SSO only depends on Okta” gets marked contradicted by local fixture evidence ([examples/first-run/expected/inline-answer.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/expected/inline-answer.md:1)).
- Field migration and change-impact checks have templates with required searches, contradiction searches, evidence categories, and budgets ([plumbref/templates/field_migration.toml](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/templates/field_migration.toml:8), [plumbref/templates/change_impact.toml](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/templates/change_impact.toml:8)).

**4. Strongest Supported Claim**

“Plumbref gives agents a repeatable, local evidence trail for repo claims.”

Status: proven by repo/demo.

The repo contains MCP tools for starting sessions, storing claims, searching, reading bounded evidence, recording judgments, rendering reports, and diffing reports ([plumbref/mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:33)). Reports include measurements, claim statuses, evidence, quality checks, and inline answers ([plumbref/reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:165)). The first-run example demonstrates a narrow contradicted-claim flow ([examples/first-run/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/README.md:47)).

**5. Vague, Inflated, Or Not Proven**

- “Plumbref verifies AI codebase claims before you rely on them” ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:10)): partially proven. It verifies workflow artifacts and enforces some gates, but the agent chooses claims, searches, summaries, and judgments.
- “Ask natural reliance-check questions” ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:18)): partially proven. Natural chat depends on the host agent following a long instruction block.
- “Reduce token spend”: partially proven. There are three dogfood MCP runs and estimated source-token reductions ([docs/real-workflow-test-results.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/real-workflow-test-results.md:28)), but not a broad benchmark.
- “Field migration,” “downstream consumers,” “external integrations”: partially proven. The templates exist, but deeper repo intelligence is still roadmap work.
- “Supported means safe to rely on”: too vague to evaluate unless the user understands it means “supported by checked evidence,” not globally true ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:321)).

**6. Still Unclear After Five Minutes**

I would still not understand how reliable this is when the agent is lazy or wrong while extracting claims or choosing searches. The tool blocks `supported` judgments without evidence and contradiction passes ([plumbref/models.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/models.py:277)), but it cannot know whether the agent searched the right concepts.

I would also want one complete real transcript from user prompt to MCP tool calls to final answer. The examples describe expected tool flow, but most are illustrative.

**7. What Would Make Me Leave Without Trying It**

The biggest reason: setup and payoff both depend on MCP client behavior plus agent discipline. The README gives generic MCP JSON ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:153)), but the actual value depends on the agent following a fairly complex workflow ([docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:106)).

Second reason: “verifies” sounds stronger than the implementation. If I expected an autonomous codebase verifier, I would dismiss it once I saw “Plumbref does not extract claims by itself” ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:323)).

**Verdict**

would try once