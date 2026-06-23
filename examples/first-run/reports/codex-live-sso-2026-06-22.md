# Plumbref Report

Verdict: Contradicted claims found - Do not claim as written
Verification mode: explanation
Budget mode: normal
Template: Explain flow (`explain_flow` v1.0)

## Verification Outcome
- Answer gate: Do not claim as written
- Why: At least one claim is contradicted by source evidence.
- Reliance outcome: 0 safe, 0 qualified, 1 avoid
- Do not rely on:
  - contradicted: SSO only depends on Okta. Safer wording: SSO can be enabled through Okta or through a Rippling integration; it is not Okta-only.

## Answer Under Review
SSO only depends on Okta.

## Issues That Need Action

### contradicted: SSO only depends on Okta.
- Type: unknown
- Risk: medium
- Reasoning: The absolute claim fails because SSO eligibility is based on Rippling integration OR Okta. Direct Okta references exist, but Rippling is a separate enabling condition for the same SSO login behavior. The sso_enabled field was searched and only appears as an unused dataclass field in app/sso.py.
- Limits: Searched local repository evidence for Okta/okta, sso, rippling, and sso_enabled. Did not inspect external services or runtime configuration outside this fixture repository.
- Safer wording: SSO can be enabled through Okta or through a Rippling integration; it is not Okta-only.
- Contradiction pass: yes
- Evidence:
  - `app/sso.py:1-22` [main implementation path]: SSO eligibility is true when a company has a Rippling integration or Okta is enabled; login returns SSO only if eligible.

    ```text
    from dataclasses import dataclass
    
    
    @dataclass
    class Company:
        rippling_integration_id: str | None = None
        okta_enabled: bool = False
        sso_enabled: bool = False
    
    
    def has_rippling_integration(company: Company) -> bool:
        return bool(company.rippling_integration_id)
    
    
    def is_sso_eligible(company: Company) -> bool:
        return has_rippling_integration(company) or company.okta_enabled
    
    
    def start_sso_login(company: Company) -> str:
        if not is_sso_eligible(company):
            return "password-login"
        return "sso-login"
    ```
  - `checks/sso_checks.py:1-13` [tests]: Checks cover both Rippling-based SSO and Okta-based SSO, plus password fallback when neither is set.

    ```text
    from app.sso import Company, start_sso_login
    
    
    def rippling_company_uses_sso():
        assert start_sso_login(Company(rippling_integration_id="ri_123")) == "sso-login"
    
    
    def okta_company_uses_sso():
        assert start_sso_login(Company(okta_enabled=True)) == "sso-login"
    
    
    def default_company_uses_password_login():
        assert start_sso_login(Company()) == "password-login"
    ```

## Supported Claims
None recorded.

## What Wasn't Checked And Why It Matters
Not checked - may affect confidence: Required claim type: definition, Required claim type: behavior, Required claim type: api, Required claim type: business_rule, Required search: {flow_name}, Required search: {entry_point}, Required search: {main_entity}, Required search: {external_system}.
Risk: broader answers may miss required claim types, contradiction paths, or evidence categories until these checks are completed.
11 more unchecked item(s) are in the JSON report.

## Measurement
- **Token reduction from bounded evidence: 0% vs full cited files; 0% vs full matched files.**
- Claims: 1 (contradicted=1)
- Searches: 5 run, 5 trace(s) recorded
- Search results: 22 match(es) across 2 matched file(s)
- Evidence read: 2 file read(s), 2 snippet(s), 2 unique evidence file(s)
- Source text returned: 226 estimated token(s) from 902 character(s)
- Contradiction passes: 1/1 judged claim(s)
- Unsupported or qualified claims caught: 1 (too_broad=0)
- Cache reuse: searches 0% hit rate; evidence 0% hit rate; 0 in-session evidence reuse(s)
- Source-token estimate details:
  - Returned evidence excerpts: 226 estimated token(s)
  - Search previews: 249 estimated token(s)
  - Full cited files baseline: 226 estimated token(s) (0% reduction from bounded evidence)
  - Full matched files baseline: 226 estimated token(s) (0% reduction from bounded evidence)
  - Method: estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing

## JSON / Full Trace
Full checklist details, per-claim budgets, and search trace: [3235deb8-bc8c-4f7e-9f3d-961c8938353d.json](3235deb8-bc8c-4f7e-9f3d-961c8938353d.json).

## To Make A Broader Claim, Verify
- Provide template value(s) for flow_name before checking required search: {flow_name}.
- Provide template value(s) for entry_point before checking required search: {entry_point}.
- Provide template value(s) for main_entity before checking required search: {main_entity}.
- Provide template value(s) for external_system before checking required search: {external_system}.
- Provide template value(s) for flow_name before checking contradiction search: {flow_name} test.
- Provide template value(s) for flow_name before checking contradiction search: {flow_name} error.
- Provide template value(s) for entry_point before checking contradiction search: {entry_point} disabled.
- Provide template value(s) for external_system before checking contradiction search: {external_system} mock.
- Read evidence for required category: entry point.
- Read evidence for required category: data inputs.
- Read evidence for required category: data outputs.
- Read evidence for required category: external calls.
