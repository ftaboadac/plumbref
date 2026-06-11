from __future__ import annotations

from pathlib import Path

import pytest

from plumbref.config import load_config
from plumbref.models import BudgetMode, ClaimType, VerificationMode
from plumbref.reports import render_report
from plumbref.sessions import PlumbrefHarness
from plumbref.template_registry import TemplateLoadError, get_template, load_templates


def test_builtin_templates_load() -> None:
    """Built-in templates provide the Phase 1 verification playbooks."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"

    templates = load_templates(repo_root)

    assert {
        "generic_verification",
        "explain_flow",
        "field_migration",
        "change_impact",
        "downstream_consumers",
        "external_integration",
    }.issubset(templates)
    assert ClaimType.IMPACT in templates["change_impact"].required_claim_types


def test_repo_local_template_overrides_builtin(tmp_path: Path) -> None:
    """Repo-local templates can override built-ins without changing package code."""
    template_dir = tmp_path / ".plumbref" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "change_impact.toml").write_text(
        """
id = "change_impact"
version = "2.0"
name = "Repo change impact"
description = "Repo-specific override."
required_searches = ["{changed_symbol} owner"]
""".strip(),
        encoding="utf-8",
    )

    template = get_template("change_impact", repo_root=tmp_path)

    assert template.version == "2.0"
    assert template.source.endswith(".plumbref/templates/change_impact.toml")


def test_configured_template_path_loads_custom_templates(tmp_path: Path) -> None:
    """Template directories can be supplied through config for shared template packs."""
    pack_dir = tmp_path / "template-pack"
    pack_dir.mkdir()
    (pack_dir / "billing_webhook.toml").write_text(
        """
id = "billing_webhook"
version = "1.0"
name = "Billing webhook"
description = "Verify billing webhook behavior."
required_claim_types = ["behavior", "api"]
required_searches = ["{webhook_name}", "{event_name}"]
contradiction_searches = ["{webhook_name} test"]
evidence_categories = ["webhook entry point", "tests"]
report_sections = ["supported behavior", "unchecked areas"]
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".plumbref.toml").write_text(
        'template_paths = ["template-pack"]\n',
        encoding="utf-8",
    )

    templates = load_templates(tmp_path, load_config(tmp_path))

    assert "billing_webhook" in templates


def test_invalid_custom_template_fails_validation(tmp_path: Path) -> None:
    """Invalid template files fail fast instead of becoming ambiguous prompts."""
    template_dir = tmp_path / ".plumbref" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "bad.toml").write_text(
        """
id = "Bad Template"
version = "1.0"
name = "Bad"
description = "Invalid ID."
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError):
        load_templates(tmp_path)


def test_session_can_start_with_template_and_template_budget() -> None:
    """Sessions record the selected template and use its budget for the selected mode."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()

    state = harness.start_session(
        repo_root=repo_root,
        question="What does this change affect?",
        answer="It changes report wording.",
        mode=VerificationMode.CHANGE_IMPACT,
        budget_mode=BudgetMode.NORMAL,
        template_id="change_impact",
    )

    assert state.session.template
    assert state.session.template.id == "change_impact"
    assert state.budget.searches_per_claim == state.session.template.budgets[BudgetMode.NORMAL].searches_per_claim


def test_session_rejects_template_for_wrong_mode() -> None:
    """Templates declare which verification modes they support."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()

    with pytest.raises(TemplateLoadError):
        harness.start_session(
            repo_root=repo_root,
            question="What does this change affect?",
            answer="It changes report wording.",
            mode=VerificationMode.CHANGE_IMPACT,
            template_id="explain_flow",
        )


def test_report_includes_template_checklist(tmp_path: Path) -> None:
    """Reports cite the template playbook used for verification."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="How does this flow work?",
        answer="It skips missing providers.",
        template_id="explain_flow",
    )
    config = load_config(repo_root)
    config.report_path = tmp_path

    report = render_report(state=state, config=config)

    assert "Template: Explain flow (`explain_flow` v1.0)" in report.markdown
    assert "## Template Checklist" in report.markdown
    assert report.json_report["template"]["id"] == "explain_flow"
