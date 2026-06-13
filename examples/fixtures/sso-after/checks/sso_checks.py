from app.sso import Company, start_sso_login


def rippling_company_uses_sso():
    assert start_sso_login(Company(rippling_integration_id="ri_123")) == "sso-login"


def okta_company_uses_sso():
    assert start_sso_login(Company(okta_enabled=True)) == "sso-login"


def default_company_uses_password_login():
    assert start_sso_login(Company()) == "password-login"


def company_flag_can_enable_sso():
    assert start_sso_login(Company(sso_enabled=True)) == "sso-login"
