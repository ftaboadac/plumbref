I avoided `reviews/packet/` and `reviews/out/`.

**1. What I Think It Is**
Plumbref is a local MCP/CLI verification harness for coding agents. It makes an agent turn a risky repo answer into atomic claims, search the local repo, read bounded source snippets, record conservative judgments, and return an inline answer plus optional Markdown/JSON report.

Important distinction: it is not an independent verifier. The README says the agent still extracts claims, chooses searches, reads evidence, and records judgments ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:39), [docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:11)).

**2. Who It Is For**
Engineers using MCP-capable coding agents, especially Codex, Claude Code, Cursor, or similar tools, who need to rely on repo claims before saying something to support, merging a change, renaming a field, or estimating impact ([docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:15), [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:18)).

It does not read like a tool for nontechnical PMs, support teams directly, or people not already using coding agents.

**3. Concrete Job**
It helps a developer ask: “The agent said X. Can I rely on that?” Then it forces a documented source check before the developer repeats the claim.

Examples are clear: “SSO only depends on Okta,” “this only affects onboarding,” “this field is safe to rename” ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:20)). The first-run example shows a narrow support-facing claim being contradicted and rewritten with safer wording ([examples/first-run/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/README.md:40)).

**4. Strongest Supported Claim**
Strongest claim: Plumbref gives agents a structured, local, source-backed evidence trail.

Marked: **proven by repo/demo**.

Support:
- MCP tools exist for start, template lookup, claim storage, repo search, evidence read, judgment recording, report diffing, and report rendering ([plumbref/mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:33)).
- CLI setup commands exist: `plumbref init`, `plumbref doctor`, `plumbref mcp` ([plumbref/cli.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/cli.py:102)).
- Tests cover report rendering, inline answers, evidence locations, contradiction passes, report policies, search traces, caching, and templates ([tests/test_reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/tests/test_reports.py:26), [tests/test_search_and_evidence.py](/Users/facundotaboada/Documents/GitHub/plumbref/tests/test_search_and_evidence.py:15), [tests/test_templates.py](/Users/facundotaboada/Documents/GitHub/plumbref/tests/test_templates.py:14)).
- The local-first/no model API posture is supported by package dependencies: `mcp`, `pydantic`, `typer`; no OpenAI/Anthropic/http client dependency in metadata ([pyproject.toml](/Users/facundotaboada/Documents/GitHub/plumbref/pyproject.toml:26)).

**5. Vague, Inflated, Or Not Proven**
Claim: “replaces vague ‘are you sure?’ loops.”
Marked: **partially proven**. The workflow can replace a loop in one fixture, but there is no user study, no external repo benchmark, and no live-client transcript.

Claim: “safe-to-rely-on statements.”
Marked: **too vague to evaluate** unless the reader notices the trust boundary. “Supported by checked local evidence” is precise; “safe to rely on” sounds stronger than the mechanism.

Claim: “Plumbref can reduce token spend.”
Marked: **partially proven**. There are dogfood measurements with estimated reductions ([docs/real-workflow-test-results.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/real-workflow-test-results.md:28)), but the benchmark scaffold explicitly says not to publish benchmark claims yet ([examples/benchmark/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/benchmark/README.md:3)).

Claim: “works naturally in Codex/Claude/Cursor.”
Marked: **unproven**. Docs give setup instructions, but the README says the first-run fixture is not a captured live client transcript ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:181), [docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:123)).

Claim: “templates make common questions reliable.”
Marked: **partially proven**. Built-in templates and tests exist, but roadmap items for repo structure intelligence, better agent errors, benchmarks, and richer workflows remain open ([ROADMAP.md](/Users/facundotaboada/Documents/GitHub/plumbref/ROADMAP.md:97), [ROADMAP.md](/Users/facundotaboada/Documents/GitHub/plumbref/ROADMAP.md:252)).

**6. What I Still Would Not Understand After Five Minutes**
I would not understand how much better this is than giving my agent a strong prompt plus “cite exact lines.” The repo shows structure and reports, but not a before/after comparison against a careful baseline.

I would also not understand the live UX in a real client. The public first-run path is an expected fixture, not a captured Codex/Claude/Cursor session ([examples/first-run/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/README.md:75)).

I would not know how often agents misuse the tool: bad claim extraction, shallow searches, false `supported` judgments, missing template values, or incomplete contradiction passes.

**7. What Would Make Me Leave Without Trying It**
The biggest exit reason is proof gap: the product depends on agent behavior, but the current public proof is small, self-referential, and partly fixture-based. Historical reports are explicitly not current proof ([examples/reports/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/README.md:3)).

Second reason: setup friction. I need MCP config, repo-specific server setup, ripgrep, and agent instructions before I see value ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:145)).

Third reason: the word “verification” may overpromise. The limitations are honest, but a serious user may conclude this is a disciplined evidence logger, not a verifier ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:340)).

**Verdict**
would try once