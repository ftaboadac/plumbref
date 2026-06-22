I did not read `reviews/out/`.

**Adoption Review**

The concrete moment where I would run Plumbref is narrow: an agent gives me an absolute or externally repeated claim like “SSO only depends on Okta” or “this only affects onboarding,” and I am about to tell support, merge a PR, or write a release note. That moment is **proven by repo/demo** as the intended use case in [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:18) and [examples/first-run/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/README.md:9). Outside that moment, I probably keep using `rg`, tests, and direct agent prompting.

The report is not just ceremony when it catches a bad absolute claim. The SSO inline answer is short and actionable: contradicted claim, safer wording, evidence, unchecked areas, verification counts ([inline-answer.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/expected/inline-answer.md:1)). The larger reports are useful receipts, especially when they show template checklist, evidence snippets, search trace, limits, and contradiction pass counts ([real-template-loading-mcp.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/real-template-loading-mcp.md:8)). But the repo itself warns historical reports may have stale line refs ([examples/reports/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/README.md:5)), so as proof they are weaker than they look.

Important claims:

- **“Plumbref verifies claims before users rely on them”**: **partially proven**. It structures sessions, claims, searches, evidence, judgments, and reports through MCP tools ([mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:33)). But the agent still extracts claims and records judgments, which the README admits ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:41)).
- **“The gate blocks unsupported confidence”**: **partially proven**. The implementation downgrades supported claims with missing required searches, contradiction searches, evidence categories, unlinked evidence, and budget exhaustion ([reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:705); [test_reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/tests/test_reports.py:502)). Still unproven in a real named-agent transcript.
- **“Normal users should not need CLI verification commands”**: **partially proven**. Docs position MCP chat as primary ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:91)), but first-run setup still requires MCP config placement and agent instructions.
- **“First-run proof exists for Codex/Claude/Cursor”**: **contradicted**. The repo explicitly says the transcript is a reproducible stdio fixture, not a captured Codex/Claude/Cursor transcript ([mcp-stdio-transcript.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/first-run/mcp-stdio-transcript.md:3)).
- **“CI/PR checks are ready”**: **partially proven / too vague to evaluate**. There is an advisory diff claim checker ([claim_checks.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/claim_checks.py:15)), but it mostly flags broad wording and “docs only” contradictions from changed file paths, not full Plumbref verification.
- **“Better than careful prompting plus `rg`”**: **unproven**. The benchmark directory is only a scaffold and explicitly says not to publish benchmark claims yet ([examples/benchmark/README.md](/Users/facundotaboada/Documents/GitHub/plumbref/examples/benchmark/README.md:5)).

Main friction:

- Install is acceptable: `pipx install plumbref`, `plumbref init`, `plumbref doctor` ([README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:117)).
- MCP setup is the real tax: users must add repo-specific config and restart/reload the agent ([docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:95)).
- Prompt discipline remains high: docs tell the user to explicitly say “Use Plumbref” when the agent skips it ([docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:135)).
- Trust calibration is hard because the agent still chooses claims, searches, summaries, and judgments ([docs/agent-usage.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/agent-usage.md:11)).
- CLI use is not compelling for normal workflow because `verify` does not extract claims automatically and asks for `--claims` JSON ([cli.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/cli.py:253)).
- Team adoption needs shared templates and shared expectations; otherwise this becomes another local ritual.

Where I would use it: inside an agent chat for risky reliance checks. I would not use the CLI except setup/debug/export. I would not yet use it in CI except as advisory noise on explicit claims files.

What would make me uninstall after one try: the agent fails to call Plumbref unless nagged, the MCP setup breaks, the report mostly restates obvious `rg` results, or the first “safe to rely on” answer feels dependent on agent-entered metadata rather than enforced traces.

This is worth it only if my codebase has local textual evidence for important behavior, my team uses MCP-capable agents heavily, and we regularly make risky claims about auth, integrations, field migrations, downstream consumers, or “only/no/safe” changes.

Verdict: **would try once**.

Single artifact that would most change my mind: a captured end-to-end Codex or Claude Code transcript on a non-Plumbref repo, from install/config through real chat prompt, tool calls, inline answer, generated JSON report, and one failure case where careful prompting plus `rg` gets the claim wrong or less inspectably right.