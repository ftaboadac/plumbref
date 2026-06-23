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
