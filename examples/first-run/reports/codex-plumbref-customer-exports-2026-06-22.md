# Plumbref Report

Verdict: Contradicted claims found - Do not claim as written
Verification mode: explanation
Budget mode: normal
Template: Explain flow (`explain_flow` v1.0)

## Verification Outcome
- Answer gate: Do not claim as written
- Why: At least one claim is contradicted by source evidence.
- Reliance outcome: 0 safe, 0 qualified, 4 avoid
- Do not rely on:
  - contradicted: Customer exports are CSV-only. Safer wording: Customer exports support CSV and JSON; enterprise accounts with beta PDF exports enabled can also export PDF.
  - contradicted: Customer exports are available to all paid accounts. Safer wording: Customer exports are available to eligible pro and enterprise accounts, except accounts under legal hold.
  - contradicted: Customer exports never include deleted records. Safer wording: Customer exports exclude deleted records by default, but enterprise admin exports can include deleted records.
  - contradicted: Customer exports only go to S3. Safer wording: Customer exports can go to S3; verified non-EU accounts can also use email delivery.

## Answer Under Review
Customer exports are CSV-only, available to all paid accounts, never include deleted records, and only go to S3.

## Issues That Need Action

### contradicted: Customer exports are CSV-only.
- Type: business_rule
- Risk: medium
- Reasoning: The claim uses CSV-only absolute language, but both implementation and docs show JSON support, plus PDF for enterprise beta accounts.
- Limits: This verification is based on the local repository fixture evidence, not production configuration outside the repo.
- Safer wording: Customer exports support CSV and JSON; enterprise accounts with beta PDF exports enabled can also export PDF.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:1-56` [main implementation path] cache_hit: Export policy defines output format based on account and JSON request, eligibility, deleted-record inclusion, and job destination.

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
  - `docs/customer-exports.md:1-8` [docs] cache_hit reused: Docs warn older CSV-only and S3-only help-center copy is stale because of PDF, JSON, and email delivery support.

    ```text
    # Customer Exports
    
    Support can tell customers to use CSV exports for most account reviews.
    
    Older help-center copy says exports are CSV-only and S3-only. That copy is
    stale for beta PDF exports, JSON exports, and verified-email delivery.
    
    Legal hold accounts must not export customer records until the hold is removed.
    ```
  - `checks/export_policy_checks.py:1-31` [tests]: Checks cover CSV for pro, beta PDF for enterprise, and email/JSON for a verified pro account.

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
    ```

### contradicted: Customer exports are available to all paid accounts.
- Type: business_rule
- Risk: medium
- Reasoning: If paid accounts means pro and enterprise, the plan gate is close, but the absolute 'all paid accounts' is too broad because legal hold accounts cannot export and the repo does not define all paid plan names.
- Limits: The repository evidence uses plan names, not a general 'paid accounts' concept.
- Safer wording: Customer exports are available to eligible pro and enterprise accounts, except accounts under legal hold.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:18-22` [main implementation path] cache_hit: Eligibility is limited to pro and enterprise accounts and excludes accounts under legal hold.

    ```text
    
    
    def can_export_customer_records(account: Account) -> bool:
        return account.plan in {"pro", "enterprise"} and not account.legal_hold
    ```
  - `checks/export_policy_checks.py:46-56` [tests]: Checks expect legal hold to block customer exports even for enterprise accounts.

    ```text
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

### contradicted: Customer exports never include deleted records.
- Type: behavior
- Risk: medium
- Reasoning: The 'never' claim is directly contradicted by enterprise admin behavior.
- Limits: The repository does not show separate product copy for this behavior beyond implementation and checks.
- Safer wording: Customer exports exclude deleted records by default, but enterprise admin exports can include deleted records.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:31-56` [main implementation path] cache_hit: Deleted records are included for enterprise accounts when requested by an admin, and that flag is returned in export jobs.

    ```text
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
  - `checks/export_policy_checks.py:33-44` [tests]: Checks expect enterprise admin exports to include deleted records.

    ```text
    
    
    def enterprise_admin_export_can_include_deleted_records():
        job = build_export_job(
            Account(plan="enterprise"),
            requested_format="csv",
            destination="s3",
            requested_by_admin=True,
        )
    
        assert job["include_deleted"] is True
    ```

### contradicted: Customer exports only go to S3.
- Type: business_rule
- Risk: medium
- Reasoning: S3 is a supported destination, but it is not the only supported destination.
- Limits: The repository evidence shows email support but does not indicate whether other out-of-repo destinations exist.
- Safer wording: Customer exports can go to S3; verified non-EU accounts can also use email delivery.
- Contradiction pass: yes
- Evidence:
  - `app/export_policy.py:24-29` [main implementation path] cache_hit: Destinations include S3, and verified non-EU accounts may also use email.

    ```text
    def allowed_destinations(account: Account) -> set[str]:
        destinations = {"s3"}
        if account.verified_email and account.region != "eu":
            destinations.add("email")
        return destinations
    ```
  - `docs/customer-exports.md:1-8` [docs] cache_hit reused: Docs warn older CSV-only and S3-only help-center copy is stale because of PDF, JSON, and email delivery support.
    - Excerpt already shown for this reused evidence reference.
  - `checks/export_policy_checks.py:24-32` [tests]: Checks expect verified non-EU accounts to export by email.

    ```text
    
    def verified_non_eu_accounts_can_export_to_email():
        job = build_export_job(
            Account(plan="pro", region="us", verified_email=True),
            requested_format="csv",
            destination="email",
        )
    
        assert job["destination"] == "email"
    ```

## Supported Claims
None recorded.

## What Wasn't Checked And Why It Matters
Not checked - may affect confidence: Required claim type: definition, Required claim type: api, Required search: {flow_name}, Required search: {entry_point}, Required search: {main_entity}, Required search: {external_system}, Contradiction search: {flow_name} test, Contradiction search: {flow_name} error.
Risk: broader answers may miss required claim types, contradiction paths, or evidence categories until these checks are completed.
8 more unchecked item(s) are in the JSON report.

## Measurement
- **Token reduction from bounded evidence: 0% vs full cited files; 0% vs full matched files.**
- Claims: 4 (contradicted=4)
- Searches: 5 run, 9 trace(s) recorded
- Search results: 26 match(es) across 3 matched file(s)
- Evidence read: 4 file read(s), 4 snippet(s), 3 unique evidence file(s)
- Source text returned: 1271 estimated token(s) from 5084 character(s)
- Contradiction passes: 4/4 judged claim(s)
- Unsupported or qualified claims caught: 4 (too_broad=0)
- Cache reuse: searches 44% hit rate; evidence 56% hit rate; 1 in-session evidence reuse(s)
- Source-token estimate details:
  - Returned evidence excerpts: 1192 estimated token(s)
  - Search previews: 347 estimated token(s)
  - Full cited files baseline: 832 estimated token(s) (0% reduction from bounded evidence)
  - Full matched files baseline: 832 estimated token(s) (0% reduction from bounded evidence)
  - Method: estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing

## JSON / Full Trace
Full checklist details, per-claim budgets, and search trace: [b2090ade-dfa9-4844-abcb-de579a4fcb88.json](b2090ade-dfa9-4844-abcb-de579a4fcb88.json).

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
