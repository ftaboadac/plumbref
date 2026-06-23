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
