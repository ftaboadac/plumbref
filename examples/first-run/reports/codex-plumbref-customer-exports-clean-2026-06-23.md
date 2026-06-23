# Plumbref Report

Verdict: Contradicted claims found - Do not claim as written
Verification mode: explanation
Budget mode: normal
Template: Explain flow (`explain_flow` v1.0)

## Verification Outcome
- Answer gate: Do not claim as written
- Why: At least one claim is contradicted by source evidence.
- Reliance outcome: 0 safe, 1 qualified, 3 avoid
- Say with qualification:
  - uncertain: Customer exports are available to all paid accounts. Safer wording: Customer exports are available to pro and enterprise accounts unless the account is on legal hold.
- Do not rely on:
  - contradicted: Customer exports are CSV-only. Safer wording: Customer exports support CSV and JSON; enterprise beta PDF exports are also available when enabled.
  - contradicted: Customer exports never include deleted records. Safer wording: Deleted records are excluded by default, but enterprise admin exports can include deleted records.
  - contradicted: Customer exports only go to S3. Safer wording: Customer exports can go to S3; verified-email accounts outside the EU can also receive exports by email.

## Answer Under Review
Customer exports are CSV-only, available to all paid accounts, never include deleted records, and only go to S3.

## Issues That Need Action

### contradicted: Customer exports are CSV-only.
- Type: behavior
- Risk: medium
- Reasoning: The implementation allows csv and json for all eligible accounts, and adds pdf for enterprise accounts with beta_pdf_exports. Checks cover pro JSON exports and enterprise beta PDF exports. Docs explicitly say older CSV-only wording is stale for JSON and beta PDF exports.
- Limits: No broader product docs beyond this fixture were checked.
- Safer wording: Customer exports support CSV and JSON; enterprise beta PDF exports are also available when enabled.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:1-56` [main implementation path] cache_hit reused: Export policy implementation including allowed formats, destinations, include-deleted logic, and job creation.

    ```text
    from dataclasses import dataclass
    
    
    @dataclass
    class Account:
        plan: str
        region: str = "us"
        beta_pdf_exports: bool = False
        legal_hold: bool = False
        verified_email: bool = False
    
    
    def allowed_export_formats(account: Account) -> set[str]:
        formats = {"csv", "json"}
        if account.beta_pdf_exports and account.plan == "enterprise":
            formats.add("pdf")
        return formats
    
    
    def can_export_customer_records(account: Account) -> bool:
        return account.plan in {"pro", "enterprise"} and not account.legal_hold
    
    
    def allowed_destinations(account: Account) -> set[str]:
        destinations = {"s3"}
        if account.verified_email and account.region != "eu":
            destinations.add("email")
        return destinations
    
    
    def include_deleted_records(account: Account, *, requested_by_admin: bool) -> bool:
        return account.plan == "enterprise" and requested_by_admin
    
    
    def build_export_job(
        account: Account,
        *,
        requested_format: str,
        destination: str,
        requested_by_admin: bool = False,
    ) -> dict[str, object]:
        if not can_export_customer_records(account):
            raise PermissionError("account is not eligible for customer exports")
        if requested_format not in allowed_export_formats(account):
            raise ValueError("unsupported export format")
        if destination not in allowed_destinations(account):
            raise ValueError("unsupported export destination")
    
        return {
            "format": requested_format,
            "destination": destination,
            "include_deleted": include_deleted_records(
                account,
                requested_by_admin=requested_by_admin,
            ),
        }
    ```
  - `checks/export_policy_checks.py:1-56` [tests] cache_hit: Policy checks exercise JSON/CSV formats, destinations, and deleted-record handling.

    ```text
    from app.export_policy import Account, build_export_job
    
    
    def pro_accounts_can_export_json_to_s3():
        job = build_export_job(
            Account(plan="pro"),
            requested_format="json",
            destination="s3",
        )
    
        assert job["format"] == "json"
        assert job["include_deleted"] is False
    
    
    def enterprise_beta_accounts_can_export_pdf():
        job = build_export_job(
            Account(plan="enterprise", beta_pdf_exports=True),
            requested_format="pdf",
            destination="s3",
        )
    
        assert job["format"] == "pdf"
    
    
    def verified_non_eu_accounts_can_export_to_email():
        job = build_export_job(
            Account(plan="pro", region="us", verified_email=True),
            requested_format="csv",
            destination="email",
        )
    
        assert job["destination"] == "email"
    
    
    def enterprise_admin_export_can_include_deleted_records():
        job = build_export_job(
            Account(plan="enterprise"),
            requested_format="csv",
            destination="s3",
            requested_by_admin=True,
        )
    
        assert job["include_deleted"] is True
    
    
    def legal_hold_blocks_exports():
        try:
            build_export_job(
                Account(plan="enterprise", legal_hold=True),
                requested_format="csv",
                destination="s3",
            )
        except PermissionError:
            return
    
        raise AssertionError("legal hold should block customer exports")
    ```
  - `docs/customer-exports.md:1-8` [docs] reused: Customer export documentation note says the legacy CSV-only/S3-only wording is stale for JSON, beta PDF, and verified-email delivery.

    ```text
    # Customer Exports
    
    Support can tell customers to use CSV exports for most account reviews.
    
    Older help-center copy says exports are CSV-only and S3-only. That copy is
    stale for beta PDF exports, JSON exports, and verified-email delivery.
    
    Legal hold accounts must not export customer records until the hold is removed.
    ```

### contradicted: Customer exports never include deleted records.
- Type: behavior
- Risk: medium
- Reasoning: The implementation includes deleted records when the account is enterprise and the request is made by an admin. Checks assert that an enterprise admin export has include_deleted set to True.
- Limits: The evidence covers policy construction, not downstream export file materialization.
- Safer wording: Deleted records are excluded by default, but enterprise admin exports can include deleted records.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:1-56` [main implementation path] cache_hit reused: Export policy implementation including allowed formats, destinations, include-deleted logic, and job creation.
    - Excerpt already shown for this reused evidence reference.
  - `checks/export_policy_checks.py:1-56` [tests] reused: Checks cover pro and enterprise export cases and legal-hold blocking.

    ```text
    from app.export_policy import Account, build_export_job
    
    
    def pro_accounts_can_export_json_to_s3():
        job = build_export_job(
            Account(plan="pro"),
            requested_format="json",
            destination="s3",
        )
    
        assert job["format"] == "json"
        assert job["include_deleted"] is False
    
    
    def enterprise_beta_accounts_can_export_pdf():
        job = build_export_job(
            Account(plan="enterprise", beta_pdf_exports=True),
            requested_format="pdf",
            destination="s3",
        )
    
        assert job["format"] == "pdf"
    
    
    def verified_non_eu_accounts_can_export_to_email():
        job = build_export_job(
            Account(plan="pro", region="us", verified_email=True),
            requested_format="csv",
            destination="email",
        )
    
        assert job["destination"] == "email"
    
    
    def enterprise_admin_export_can_include_deleted_records():
        job = build_export_job(
            Account(plan="enterprise"),
            requested_format="csv",
            destination="s3",
            requested_by_admin=True,
        )
    
        assert job["include_deleted"] is True
    
    
    def legal_hold_blocks_exports():
        try:
            build_export_job(
                Account(plan="enterprise", legal_hold=True),
                requested_format="csv",
                destination="s3",
            )
        except PermissionError:
            return
    
        raise AssertionError("legal hold should block customer exports")
    ```
  - `docs/customer-exports.md:1-8` [docs] reused: Customer export documentation note says the legacy CSV-only/S3-only wording is stale for JSON, beta PDF, and verified-email delivery.
    - Excerpt already shown for this reused evidence reference.

### contradicted: Customer exports only go to S3.
- Type: behavior
- Risk: medium
- Reasoning: S3 is always an allowed destination, but verified-email accounts outside the EU can also export to email. Checks cover a verified US pro account exporting to email, and docs say S3-only wording is stale for verified-email delivery.
- Limits: The evidence covers allowed destinations in policy, not delivery infrastructure internals.
- Safer wording: Customer exports can go to S3; verified-email accounts outside the EU can also receive exports by email.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:1-56` [main implementation path] cache_hit reused: Export policy implementation including allowed formats, destinations, include-deleted logic, and job creation.
    - Excerpt already shown for this reused evidence reference.
  - `checks/export_policy_checks.py:1-56` [tests] reused: Checks cover pro and enterprise export cases and legal-hold blocking.
    - Excerpt already shown for this reused evidence reference.
  - `docs/customer-exports.md:1-8` [docs] reused: Customer export documentation note says the legacy CSV-only/S3-only wording is stale for JSON, beta PDF, and verified-email delivery.
    - Excerpt already shown for this reused evidence reference.

### uncertain: Customer exports are available to all paid accounts.
- Type: business_rule
- Risk: medium
- Reasoning: The implementation allows customer exports for pro and enterprise accounts, but only when the account is not on legal hold. The phrase all paid accounts is broader than the code evidence and ignores the legal-hold exclusion.
- Limits: The fixture does not define a complete paid-plan taxonomy beyond pro and enterprise examples.
- Safer wording: Customer exports are available to pro and enterprise accounts unless the account is on legal hold.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:1-56` [main implementation path]: Export policy shows account eligibility depends on plan in pro/enterprise and excludes legal hold.

    ```text
    from dataclasses import dataclass
    
    
    @dataclass
    class Account:
        plan: str
        region: str = "us"
        beta_pdf_exports: bool = False
        legal_hold: bool = False
        verified_email: bool = False
    
    
    def allowed_export_formats(account: Account) -> set[str]:
        formats = {"csv", "json"}
        if account.beta_pdf_exports and account.plan == "enterprise":
            formats.add("pdf")
        return formats
    
    
    def can_export_customer_records(account: Account) -> bool:
        return account.plan in {"pro", "enterprise"} and not account.legal_hold
    
    
    def allowed_destinations(account: Account) -> set[str]:
        destinations = {"s3"}
        if account.verified_email and account.region != "eu":
            destinations.add("email")
        return destinations
    
    
    def include_deleted_records(account: Account, *, requested_by_admin: bool) -> bool:
        return account.plan == "enterprise" and requested_by_admin
    
    
    def build_export_job(
        account: Account,
        *,
        requested_format: str,
        destination: str,
        requested_by_admin: bool = False,
    ) -> dict[str, object]:
        if not can_export_customer_records(account):
            raise PermissionError("account is not eligible for customer exports")
        if requested_format not in allowed_export_formats(account):
            raise ValueError("unsupported export format")
        if destination not in allowed_destinations(account):
            raise ValueError("unsupported export destination")
    
        return {
            "format": requested_format,
            "destination": destination,
            "include_deleted": include_deleted_records(
                account,
                requested_by_admin=requested_by_admin,
            ),
        }
    ```
  - `checks/export_policy_checks.py:1-56` [tests] reused: Checks cover pro and enterprise export cases and legal-hold blocking.
    - Excerpt already shown for this reused evidence reference.
  - `docs/customer-exports.md:1-8` [docs] reused: Customer export documentation note says the legacy CSV-only/S3-only wording is stale for JSON, beta PDF, and verified-email delivery.
    - Excerpt already shown for this reused evidence reference.

## Supported Claims
None recorded.

## What Wasn't Checked And Why It Matters
Not checked - may affect confidence: Required claim type: definition, Required claim type: api, Required search: {flow_name}, Required search: {entry_point}, Required search: {main_entity}, Required search: {external_system}, Contradiction search: {flow_name} test, Contradiction search: {flow_name} error.
Risk: broader answers may miss required claim types, contradiction paths, or evidence categories until these checks are completed.
8 more unchecked item(s) are in the JSON report.

## Measurement
- **Token reduction from bounded evidence: 0% vs full cited files; 0% vs full matched files.**
- Claims: 4 (contradicted=3, uncertain=1)
- Searches: 4 run, 12 trace(s) recorded
- Search results: 39 match(es) across 3 matched file(s)
- Evidence read: 3 file read(s), 3 snippet(s), 3 unique evidence file(s)
- Source text returned: 3324 estimated token(s) from 13296 character(s)
- Contradiction passes: 4/4 judged claim(s)
- Unsupported or qualified claims caught: 4 (too_broad=0)
- Cache reuse: searches 67% hit rate; evidence 40% hit rate; 7 in-session evidence reuse(s)
- Source-token estimate details:
  - Returned evidence excerpts: 1583 estimated token(s)
  - Search previews: 368 estimated token(s)
  - Full cited files baseline: 832 estimated token(s) (0% reduction from bounded evidence)
  - Full matched files baseline: 832 estimated token(s) (0% reduction from bounded evidence)
  - Method: estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing

## JSON / Full Trace
Full checklist details, per-claim budgets, and search trace: [17b5e485-a8b4-451a-a855-da1a290366f6.json](17b5e485-a8b4-451a-a855-da1a290366f6.json).

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
