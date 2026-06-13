# SSO Business-Rule Drift Demo

Date: 2026-06-13

This demo shows Plumbref's rerun/diff workflow on a small public fixture. The
story is:

> Verified knowledge drifted because the code changed.

The fixture is intentionally tiny so anyone can inspect it. There are no private
repository paths or private implementation details.

## Question

> How does SSO eligibility work?

## Before State

Fixture: [examples/fixtures/sso-before](../examples/fixtures/sso-before)

The original eligibility rule has two paths:

```python
def is_sso_eligible(company: Company) -> bool:
    return has_rippling_integration(company) or company.okta_enabled
```

Plumbref verified this claim as supported:

> SSO only starts when Rippling integration exists or Okta is enabled.

Report:
[examples/reports/sso-eligibility-before.json](../examples/reports/sso-eligibility-before.json)

## After State

Fixture: [examples/fixtures/sso-after](../examples/fixtures/sso-after)

The code adds a third eligibility path:

```python
def is_sso_eligible(company: Company) -> bool:
    return (
        has_rippling_integration(company)
        or company.okta_enabled
        or company.sso_enabled
    )
```

Because the original claim used `only`, the added `company.sso_enabled` branch
contradicts the old verified claim.

Report:
[examples/reports/sso-eligibility-after.json](../examples/reports/sso-eligibility-after.json)

## Diff Result

Diff artifact:
[examples/reports/sso-eligibility-drift-diff.md](../examples/reports/sso-eligibility-drift-diff.md)

Screenshot candidate:

```text
# Plumbref Report Diff

Question: How does SSO eligibility work?
Template: Explain flow (`explain_flow`)

## What Changed
1 claim changed status.

- Claims compared: 2
- Status changes: 1
- Evidence drift: 0
- Location-only drift: 1
- Added claims: 0
- Removed claims: 0

## Status Changes

### `claim-002`
- Claim: SSO only starts when Rippling integration exists or Okta is enabled.
- Status: `supported` -> `contradicted`
- Evidence: changed
- Limits changed: `This fixture does not claim anything about production configuration.` -> `Say SSO can start through Rippling, Okta, or company.sso_enabled.`
```

The unchanged entry-point claim moved line numbers only, so Plumbref classifies
it separately as `location_only_drift` and keeps it out of the material-change
count.

## Reproduce

Run the checked-in diff artifact:

```shell
plumbref diff-reports \
  examples/reports/sso-eligibility-before.json \
  examples/reports/sso-eligibility-after.json
```

Or write it to a file:

```shell
plumbref diff-reports \
  examples/reports/sso-eligibility-before.json \
  examples/reports/sso-eligibility-after.json \
  --output examples/reports/sso-eligibility-drift-diff.md
```

The primary product surface is the MCP tool `plumbref_diff_reports`, which
returns the same Markdown plus structured claim changes for the agent to
summarize in chat.

## Why It Matters

This is not an "agent was wrong" demo. The original claim was supported by the
before-state code. The claim became false because the code changed.

That is the product direction:

> Your team's verified claims about how the codebase works, updated when the
> code changes.
