from __future__ import annotations

from pathlib import Path

from groundcheck.config import load_config
from groundcheck.evidence import read_evidence
from groundcheck.judgments import record_judgment
from groundcheck.models import (
    BudgetMode,
    ChangeContext,
    ChangedSymbol,
    ChangeSource,
    ClaimStatus,
    ClaimType,
    ClaimWorkItem,
    OutputMode,
    RiskLevel,
    VerificationMode,
)
from groundcheck.reports import render_report
from groundcheck.sessions import GroundcheckHarness


def test_report_renders_markdown_and_json(tmp_path: Path) -> None:
    """Reports include verdict, claims, evidence, and support-safe summary."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.NORMAL,
        output_modes=[OutputMode.ENGINEER, OutputMode.SUPPORT],
    )
    claim = ClaimWorkItem(
        text="The scheduled job skips work when provider_id is missing.",
        claim_type=ClaimType.BEHAVIOR,
        risk=RiskLevel.MEDIUM,
    )
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_path = tmp_path
    snippet = read_evidence(
        state=state,
        config=config,
        claim_id=claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
        summary="run_scheduled_job returns skipped when provider_id is missing.",
    )
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.SUPPORTED,
        evidence_ids=[snippet.id],
        reasoning_summary="The function returns a skipped status for missing provider_id.",
        contradiction_searched=True,
    )

    report = render_report(state=state, config=config)

    assert report.json_report["verdict"] == "Supported"
    assert "Support-Safe Summary" in report.markdown
    assert "```text" in report.markdown
    assert '"reason": "missing provider_id"' in report.markdown


def test_json_report_redacts_sensitive_text(tmp_path: Path) -> None:
    """JSON reports redact sensitive claim and judgment text."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="Is the token exposed?",
        answer="No.",
        budget_mode=BudgetMode.NORMAL,
    )
    claim = ClaimWorkItem(text='The api_key = "secret-value" appears in code.')
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_path = tmp_path
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.UNCERTAIN,
        reasoning_summary='Found token = "abc123".',
    )

    report = render_report(state=state, config=config)

    assert "secret-value" not in str(report.json_report)
    assert "abc123" not in str(report.json_report)


def test_scenario_report_labels_predicted_outcomes(tmp_path: Path) -> None:
    """Scenario reports show scenario context and a safe conclusion."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        mode=VerificationMode.SCENARIO,
        scenario="run_scheduled_job receives provider_id=None.",
        budget_mode=BudgetMode.NORMAL,
    )
    claim = ClaimWorkItem(
        text="run_scheduled_job returns skipped when provider_id is missing.",
        expected_outcome="The scheduled job is skipped.",
        assumptions=["provider_id is None."],
        claim_type=ClaimType.BEHAVIOR,
    )
    broad_claim = ClaimWorkItem(
        text="If provider_id is missing, every job in the system is skipped.",
        expected_outcome="All scheduled jobs are skipped.",
        assumptions=["The sample function represents every scheduled job."],
        claim_type=ClaimType.BEHAVIOR,
    )
    harness.store_claims([claim, broad_claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_path = tmp_path
    snippet = read_evidence(
        state=state,
        config=config,
        claim_id=claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
        summary="run_scheduled_job returns skipped when provider_id is missing.",
    )
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.SUPPORTED,
        evidence_ids=[snippet.id],
        reasoning_summary="The return value directly supports the predicted outcome.",
        contradiction_searched=True,
    )
    broad_snippet = read_evidence(
        state=state,
        config=config,
        claim_id=broad_claim.id,
        file="app.py",
        start_line=8,
        end_line=12,
        summary="Only run_scheduled_job behavior is shown; this does not cover every scheduled job.",
    )
    record_judgment(
        state=state,
        claim_id=broad_claim.id,
        status=ClaimStatus.TOO_BROAD,
        evidence_ids=[broad_snippet.id],
        reasoning_summary="The evidence supports a narrower outcome for run_scheduled_job only.",
        limits="Say run_scheduled_job is skipped when provider_id is missing; do not generalize to every job.",
    )

    report = render_report(state=state, config=config)

    assert "Verification mode: scenario" in report.markdown
    assert "## Predicted Outcomes" in report.markdown
    assert "Scenario: run_scheduled_job receives provider_id=None." in report.markdown
    assert "Predicted outcome: The scheduled job is skipped." in report.markdown
    assert "## Safe Conclusion" in report.markdown
    assert "Supported outcome(s):" in report.markdown
    assert "- The scheduled job is skipped." in report.markdown
    assert "Needs qualification:" in report.markdown
    assert "too_broad: All scheduled jobs are skipped." in report.markdown
    assert (
        "Limits: Say run_scheduled_job is skipped when provider_id is missing; do not generalize to every job."
        in report.markdown
    )
    assert report.json_report["mode"] == "scenario"


def test_change_impact_report_renders_scope_and_safe_statement(tmp_path: Path) -> None:
    """Change impact reports show scope, impact claims, and safer wording."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What does this change affect?",
        answer="This change only affects report wording.",
        mode=VerificationMode.CHANGE_IMPACT,
        budget_mode=BudgetMode.NORMAL,
    )
    harness.record_change_context(
        ChangeContext(
            source=ChangeSource.FILES,
            changed_files=["app.py"],
            changed_symbols=[
                ChangedSymbol(name="update_report_wording", kind="function", file="app.py", start_line=19)
            ],
        ),
        session_id=state.session.id,
    )
    supported_claim = ClaimWorkItem(
        text="The change affects report wording from items to records.",
        claim_type=ClaimType.IMPACT,
    )
    broad_claim = ClaimWorkItem(
        text="This change only affects report wording.",
        claim_type=ClaimType.IMPACT,
        absolute_language=["only"],
    )
    harness.store_claims([supported_claim, broad_claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_path = tmp_path
    supported_snippet = read_evidence(
        state=state,
        config=config,
        claim_id=supported_claim.id,
        file="app.py",
        start_line=19,
        end_line=20,
        summary="update_report_wording replaces items with records.",
    )
    record_judgment(
        state=state,
        claim_id=supported_claim.id,
        status=ClaimStatus.SUPPORTED,
        evidence_ids=[supported_snippet.id],
        reasoning_summary="The changed symbol only rewrites report wording.",
        contradiction_searched=True,
    )
    broad_snippet = read_evidence(
        state=state,
        config=config,
        claim_id=broad_claim.id,
        file="app.py",
        start_line=15,
        end_line=20,
        summary="The file also contains title rendering that controls report wording.",
    )
    record_judgment(
        state=state,
        claim_id=broad_claim.id,
        status=ClaimStatus.TOO_BROAD,
        evidence_ids=[broad_snippet.id],
        reasoning_summary="The evidence supports a narrower impact statement.",
        limits=(
            "Say the shown changed symbol affects report wording; verify callers before claiming it is the only effect."
        ),
    )

    report = render_report(state=state, config=config)

    assert "## Change Scope" in report.markdown
    assert "## Safer Impact Statement" in report.markdown
    assert report.json_report["change_context"]["changed_files"] == ["app.py"]
