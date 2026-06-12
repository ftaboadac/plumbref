# Changelog

All notable changes to Plumbref are tracked here.

## Unreleased

- Align package version metadata across `pyproject.toml`, `plumbref/__init__.py`, and `uv.lock`.
- Document the baseline architecture in the README.
- Add checked-in example reports for explanation, scenario, and change-impact modes.
- Add versioned verification templates with built-in, user, repo-local, and configured template-pack loading.
- Add an agent usage guide with MCP setup, recommended instructions, and neutral conversational examples.
- Add report-level measurement summaries and a dogfood demo for public launch readiness.
- Add `plumbref init` and `plumbref doctor` onboarding commands.
- Add verification-quality reporting with checklist completion, broad-claim detection,
  recommended next checks, and stricter support rules for absolute language.
- Add search and evidence caching with stable evidence IDs, in-session snippet
  reuse, and cache hit/miss metrics in reports.

## 0.1.1

- Position the README around one-time MCP setup and natural chat usage.
- Document local development setup and test commands with `python -m pytest`.

## Release Checklist

- Confirm `pyproject.toml`, `plumbref/__init__.py`, and `uv.lock` use the same version.
- Run `python -m pytest`.
- Run `ruff check .`.
- Review `README.md`, `ROADMAP.md`, and checked-in examples for behavior changes.
- Build the package from a clean checkout before publishing.
