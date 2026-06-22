**Technical Trust Review**

I would not trust the current verification claim as stated: “Plumbref verifies AI codebase claims before you rely on them” in [README.md](/Users/facundotaboada/Documents/GitHub/plumbref/README.md:10). The repo supports “Plumbref records a structured evidence trail,” but not yet “Plumbref enforces verification.”

**Claim Statuses**

| Claim | Mark |
|---|---|
| Local-first, repo-local search and evidence reads | proven by repo/demo |
| Supported judgments require evidence and a contradiction pass | partially proven |
| Templates define required searches, contradiction searches, evidence categories, and budgets | proven by repo |
| Required template checks are strictly enforced before safe output | partially proven |
| Plumbref blocks unsupported confidence | partially proven |
| Living checked claims that can be rerun when code changes | partially proven / mostly unproven |
| PR/CI risk checks | partially proven as advisory only |
| “Verification gate” as a trust boundary independent of agent judgment | unproven |
| Current examples prove the strict gate | contradicted |

**Strongest Trust Problems**

1. False confidence can still enter through the agent boundary. The MCP API lets the coding agent extract claims, choose searches, choose snippets, tag evidence categories, summarize evidence, and record judgments: [mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:100), [mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:133), [mcp_server.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/mcp_server.py:160). Plumbref validates structure, not truth. `record_judgment` only checks evidence IDs exist and broad supported claims have notes; it does not verify the notes correspond to a real contradiction search: [judgments.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/judgments.py:18).

2. `supported` is stricter than nothing, but still too weak. The model requires supported judgments to have evidence and `contradiction_searched=True`: [models.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/models.py:277). But `contradiction_searched` is a boolean supplied by the agent, not derived from recorded search traces.

3. Required search completion is syntactic. `search_pattern_completion` marks a required search complete when template tokens appear in a recorded query; it does not require matches, useful result coverage, or evidence tied to that query: [reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:782). A trace for the right words can satisfy the checklist even if it found nothing relevant.

4. Template checks are not uniformly gate-enforced. `build_gate_coverage` applies failed required searches to supported claims, but failed contradiction searches and evidence categories are only added for claims with broad language: [reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:731). A non-broad supported claim can still be safe with missing template contradiction searches or categories.

5. Required claim types are checklist-only. `build_quality_summary` records missing template claim types, but `build_gate_coverage` does not use them as blockers: [reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:486). That makes template completeness broader than the answer gate.

6. Budget exhaustion is only partially enforced. Search budget exhaustion returns a trace with `budget_exhausted=True`: [search.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/search.py:37). Evidence budget exhaustion raises an exception: [evidence.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/evidence.py:82). The implementation plan admits structured evidence-read exhaustion is still remaining work: [checked-claims-implementation-plan.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/checked-claims-implementation-plan.md:39).

7. Reports are not always inspectable enough. Markdown now points users to JSON for full trace rather than printing search details: [reports.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/reports.py:994). That is reasonable for size, but examples include stale Markdown reports with old sections and line numbers, weakening audit confidence.

8. The SSO drift demo contradicts the strict-gate story. The “before” JSON says `safe_to_answer` while `search_traces_recorded` is `0`: [sso-eligibility-before.json](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/sso-eligibility-before.json:144), [sso-eligibility-before.json](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/sso-eligibility-before.json:166). The same report lists missing required searches and contradiction searches: [sso-eligibility-before.json](/Users/facundotaboada/Documents/GitHub/plumbref/examples/reports/sso-eligibility-before.json:274). As a demo artifact, this is damaging.

9. Checked claims are export artifacts, not living facts yet. `export_checked_claims` copies report data into JSON: [checked_claims.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/checked_claims.py:25). `rerun` only emits instructions for an agent workflow: [checked_claims.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/checked_claims.py:193). That is honest, but the “living repo facts” claim is not implemented as an automated verifier.

10. The advisory PR check is very narrow. It flags risky language and obvious “only docs/copy” contradictions from changed file paths: [claim_checks.py](/Users/facundotaboada/Documents/GitHub/plumbref/plumbref/claim_checks.py:91). It does not run full Plumbref verification, which the implementation plan also states: [checked-claims-implementation-plan.md](/Users/facundotaboada/Documents/GitHub/plumbref/docs/checked-claims-implementation-plan.md:344).

**Verdict**

would star but not use

The single test that would most change my mind: an end-to-end MCP or harness regression proving `safe_to_answer` is impossible unless all selected-template required searches, contradiction searches, claim-linked evidence categories, evidence snippets, and budget checks are recorded and tied to the supported claim.