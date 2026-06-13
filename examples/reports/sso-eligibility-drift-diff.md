# Plumbref Report Diff

Question: How does SSO eligibility work?
Summary: `SSO only starts when Rippling integration exists or Okta is enabled.` changed from `supported` to `contradicted`; updated wording: Say SSO can start through Rippling, Okta, or company.sso_enabled.
Template: Explain flow (`explain_flow`)
Old report: `examples/reports/sso-eligibility-before.json`
New report: `examples/reports/sso-eligibility-after.json`

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
- Old evidence: `app/sso.py:10-16` `bd67d05d`, `checks/sso_checks.py:1-12` `0de06fe6`
- New evidence: `app/sso.py:10-19` `58fcbe66`, `checks/sso_checks.py:1-15` `14213f6b`

## New Claims
None.

## Removed Claims
None.

## Evidence Drift
None.

## Location-Only Drift

### `claim-001`
- Claim: SSO login starts from start_sso_login, which calls is_sso_eligible before returning sso-login.
- Status unchanged: `supported`
- Evidence: location changed only
- Old evidence: `app/sso.py:19-22` `ebfd2f53`
- New evidence: `app/sso.py:23-26` `ebfd2f53`

## Unchanged Claims
None.
