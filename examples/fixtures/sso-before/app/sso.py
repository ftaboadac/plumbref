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
