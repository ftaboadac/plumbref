# Launch Checklist

Use this before dogfooding Plumbref in a normal workflow or posting publicly.

## Ready-To-Use Smoke Test

Run from a clean checkout or fresh virtual environment:

```shell
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
rg --version
plumbref init --repo-root .
plumbref doctor --repo-root .
plumbref templates --repo-root .
plumbref templates --repo-root . --template-id change_impact
python -m pytest
ruff check .
```

For an installed package smoke test:

```shell
python -m venv /tmp/plumbref-smoke
. /tmp/plumbref-smoke/bin/activate
python -m pip install dist/plumbref-0.1.1-py3-none-any.whl
plumbref init --repo-root /path/to/repo
plumbref doctor --repo-root /path/to/repo
plumbref templates --repo-root /path/to/repo
plumbref mcp --repo-root /path/to/repo
```

Stop the MCP process after confirming it starts.

## Public Demo Requirements

Before posting, have one demo that shows:

- the user question
- the selected template and mode
- the initial hypothesis or draft answer
- searches run
- files and snippets read
- supported claims
- a too-broad, uncertain, contradicted, or not-found claim
- safer final wording

The checked-in dogfood demo is:

- [Template loading demo](../examples/reports/plumbref-template-loading-demo.md)

## Honest Public Claims

Good claims:

- Plumbref gives coding agents reusable verification playbooks.
- Plumbref keeps verification local to the repository.
- Plumbref records searches, bounded snippets, judgments, and limits.
- Plumbref helps catch over-broad claims like "only", "always", and "never".
- Plumbref can reduce blind file reading by making the agent search and read
  through a structured protocol.
- Plumbref can reuse cached evidence as compact references when source files
  have not changed.

Avoid claiming:

- Plumbref proves code behavior automatically.
- Plumbref replaces human review.
- Plumbref fully understands every framework or architecture.
- Plumbref guarantees every required template check is complete.
- Plumbref always uses fewer tokens than a careful expert agent.
- Plumbref inspects production data or external systems.

## Current Limitations

- Search is lexical and repo-local.
- The agent still extracts claims and reasons over evidence.
- Template checklist completion depends on concrete `template_values`; missing
  placeholder values are reported as next checks.
- Large repositories may need deeper budgets or narrower questions.
- Reports are Markdown and JSON; there is no local report UI yet.
- No model API, vector store, hosted service, or production data connection is
  included.

## Suggested Post Framing

Short version:

```text
I built Plumbref, a local MCP verification harness for coding agents.

Instead of asking an agent to "be careful", Plumbref gives it a structured
workflow: pick a verification template, extract atomic claims, search the repo,
read bounded snippets, run contradiction checks, and render a report with
supported claims, uncertain areas, and safer wording.

It does not prove behavior automatically. The current value is making the
agent's verification trail visible and catching over-broad claims before they
turn into confident answers.
```

Demo metrics to include:

```text
Demo: template loading in Plumbref itself
- Claims checked: 3
- Searches run: 5
- Evidence snippets read: 4
- Supported claims: 2
- Too-broad claims caught: 1
```
