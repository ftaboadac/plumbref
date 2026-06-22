**Alternatives Review**

Core finding: Plumbref’s best case is not “better search.” It is a structured receipt and downgrade mechanism around a careful-agent workflow. The repo proves part of that, but not yet enough to beat cheaper substitutes for most routine cases.

| Claim | Status | Notes |
| --- | --- | --- |
| Plumbref still depends on the agent to extract claims, choose searches, read evidence, and judge | proven by repo/demo | README states this directly in the Trust Boundary: [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:39). MCP tools also accept agent-supplied claims/searches/judgments: [plumbref/mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:100). |
| It is more than raw `rg` | partially proven | It wraps `rg` search with claim IDs, budgets, cache, traces, snippets, and reports: [plumbref/search.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/search.py:18). But the core discovery remains lexical search. |
| It enforces some answer-gate rules | proven by repo/demo | Supported judgments require evidence and contradiction passes: [plumbref/models.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/models.py:267). Broad supported claims require contradiction notes: [plumbref/judgments.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/judgments.py:23). |
| The gate is a hard block for all missing checks | contradicted | Missing template checks produce `answer_with_qualifications` with `can_answer: true`, not a full block: [plumbref/reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:680). |
| It has a real named-client first-run proof | contradicted | README and agent guide say the current first-run artifact is not a captured live Codex/Claude/Cursor transcript: [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:181), [docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:123). |
| It beats careful prompting plus `rg` | unproven | The benchmark plan exists, but is explicitly a scaffold and “do not use as public benchmark”: [docs/claim-check-benchmark-plan.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/claim-check-benchmark-plan.md:1). |
| It improves auditability | partially proven | JSON/Markdown reports, checked-claim export, diffs, and rerun packets exist: [plumbref/checked_claims.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/checked_claims.py:25). But rerun remains instructions for another agent pass, not automatic verification: [plumbref/checked_claims.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/checked_claims.py:193). |

**Where Substitutes Are Good Enough**

For one-off questions about a known symbol, `rg` plus manual reading is cheaper and simpler. If I can search the identifier, inspect two files, and cite lines, Plumbref adds setup and report ceremony.

For behavior claims already covered by tests, tests/CI are better. They prove executable invariants rather than producing a source-evidence narrative. Plumbref is useful only when the question is about what can safely be said, not whether code still passes.

For known bug/security/policy patterns, Semgrep/static analysis is better. Plumbref’s advisory PR check is intentionally shallow and path/wording based: [plumbref/claim_checks.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/claim_checks.py:91).

For type/API compatibility claims, type checking and linters are cheaper. The repo has normal pytest/ruff setup: [pyproject.toml](/Users/facundotaboada/Documents/GitHub/plumbref/pyproject.toml:32). Plumbref does not replace those checks.

For team norms like “never say only/no downstream without checking callers/tests/docs,” a code review checklist or `AGENTS.md` rule may be enough. The README’s own differentiator is making that behavior explicit and inspectable, not inventing a new reasoning capability: [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:53).

For careful users of Codex/Claude/Cursor, asking for file citations, contradiction searches, and unchecked areas is the strongest substitute. The benchmark plan correctly identifies this as the main baseline: [docs/claim-check-benchmark-plan.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/claim-check-benchmark-plan.md:6).

**What Plumbref Adds**

The real additions are structured state, per-claim evidence links, template-required checks, broad-language detection, conservative status labels, report artifacts, cache metrics, and checked-claim export/diff. The dogfood report shows 3 sessions, 12 claims, 29 searches, 28 snippets, and 3 unsupported/over-broad claims caught: [docs/real-workflow-test-results.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/real-workflow-test-results.md:17).

That difference matters only when the cost of an unsupported claim is high enough to justify installing/configuring a tool: support-facing statements, PR summaries, migration risk, downstream-consumer claims, and broad “only/safe/no downstream/always” wording. It does not matter enough for routine local understanding, normal review, or claims that tests/static tools already cover.

**README Gap**

The README should explicitly acknowledge the strongest alternative: “a careful agent prompt or `AGENTS.md` rule that requires `rg`, file/line citations, contradiction searches, and unchecked areas.” Right now the README mentions prompts generally, but it does not directly compare against that workflow as the serious baseline.

**Benchmark That Would Prove It**

Run the planned benchmark with raw outputs: same model, same repo state, baseline prompt requiring `rg`/citations/contradictions/unchecked areas versus Plumbref MCP inline answer. Score unsupported final claims, broad claims qualified, auditability, files read, search count, and reviewer time. The single artifact that would most change my mind is a public benchmark report where Plumbref catches or downgrades claims that the careful baseline leaves unsupported, with raw transcripts attached.

Verdict: would try once.