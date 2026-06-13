from __future__ import annotations

from pathlib import Path

from plumbref.config import load_config
from plumbref.evidence import read_evidence
from plumbref.judgments import record_judgment
from plumbref.models import (
    BudgetMode,
    ChangeContext,
    ChangedSymbol,
    ChangeSource,
    ClaimStatus,
    ClaimType,
    ClaimWorkItem,
    OutputMode,
    ReportPolicy,
    RiskLevel,
    SearchTrace,
    VerificationMode,
)
from plumbref.reports import estimate_tokens, format_excerpt, render_report
from plumbref.sessions import PlumbrefHarness


def test_report_renders_markdown_and_json(tmp_path: Path) -> None:
    """Reports include verdict, claims, evidence, and support-safe summary."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
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
    config.cache_path = tmp_path / "cache"
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
    assert "## Measurement" in report.markdown
    assert "```text" in report.markdown
    assert '"reason": "missing provider_id"' in report.markdown
    assert report.json_report["measurement"]["claims_total"] == 1
    assert report.json_report["measurement"]["evidence_snippets_read"] == 1
    assert report.json_report["measurement"]["source_text_chars_returned"] > 0
    assert "Source-token estimate:" in report.markdown
    assert report.json_report["measurement"]["token_estimate"]["returned_evidence_estimated_tokens"] > 0
    assert report.json_report["measurement"]["token_estimate"]["full_cited_files_estimated_tokens"] > 0


def test_on_demand_policy_keeps_low_risk_supported_result_inline(tmp_path: Path) -> None:
    """The default policy does not create files for low-risk fully supported answers."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.cache_path = tmp_path / "cache"
    config.report_path = tmp_path / "reports"
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

    assert report.report_written is False
    assert report.markdown_path is None
    assert not config.report_path.exists()


def test_on_demand_policy_writes_qualified_result_to_dated_report_path(tmp_path: Path) -> None:
    """Qualified results create durable local report files and an index entry."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="Does every job skip missing providers?",
        answer="Every job skips missing providers.",
    )
    claim = ClaimWorkItem(text="Every job skips missing providers.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_path = tmp_path / "reports"
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.TOO_BROAD,
        reasoning_summary="Evidence supports one function, not every job.",
        limits="Say run_scheduled_job skips missing provider_id.",
    )

    report = render_report(state=state, config=config)

    assert report.report_written is True
    assert report.report_write_reason == "auto_report_due_to_too_broad"
    dated_report_path = config.report_path / state.session.created_at.date().isoformat()
    assert report.markdown_path == dated_report_path / f"{state.session.id}.md"
    assert report.json_path == dated_report_path / f"{state.session.id}.json"
    assert report.markdown_path.is_file()
    assert report.json_path.is_file()
    index = (config.report_path / "index.json").read_text(encoding="utf-8")
    assert state.session.id in index
    assert "auto_report_due_to_too_broad" in index


def test_manual_policy_requires_explicit_report_write(tmp_path: Path) -> None:
    """Manual policy suppresses automatic files but still allows forced reports."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="Does every job skip missing providers?",
        answer="Every job skips missing providers.",
    )
    claim = ClaimWorkItem(text="Every job skips missing providers.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_policy = ReportPolicy.MANUAL
    config.report_path = tmp_path / "reports"
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.TOO_BROAD,
        reasoning_summary="Evidence supports one function, not every job.",
    )

    inline_report = render_report(state=state, config=config)
    forced_report = render_report(
        state=state,
        config=config,
        write_files=True,
        report_write_reason="user_requested",
    )

    assert inline_report.report_written is False
    assert forced_report.report_written is True
    assert forced_report.report_write_reason == "user_requested"
    assert forced_report.markdown_path and forced_report.markdown_path.is_file()


def test_estimate_tokens_rounds_up_from_character_count() -> None:
    """Token estimates use a simple conservative chars/4 approximation."""
    assert estimate_tokens(0) == 0
    assert estimate_tokens(1) == 1
    assert estimate_tokens(4) == 1
    assert estimate_tokens(5) == 2


def test_format_excerpt_uses_longer_fence_when_excerpt_contains_backticks() -> None:
    """Markdown evidence snippets remain readable when source contains code fences."""
    lines = format_excerpt("```shell\nplumbref init\n```")

    assert lines[1] == "    ````text"
    assert lines[-1] == "    ````"


def test_json_report_redacts_sensitive_text(tmp_path: Path) -> None:
    """JSON reports redact sensitive claim and judgment text."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
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
    harness = PlumbrefHarness()
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
    assert "## Answer" in report.markdown
    assert "## Safe Conclusion" not in report.markdown
    assert (
        "Based on the checked evidence, the expected outcome is: "
        "run_scheduled_job returns skipped when provider_id is missing."
        in report.markdown
    )
    assert (
        "Important qualification: Say run_scheduled_job is skipped when provider_id is missing; "
        "do not generalize to every job."
        in report.markdown
    )
    assert (
        "Limits: Say run_scheduled_job is skipped when provider_id is missing; do not generalize to every job."
        in report.markdown
    )
    assert report.markdown.index("## Answer") < report.markdown.index("## Predicted Outcomes")
    assert report.json_report["mode"] == "scenario"


def test_change_impact_report_renders_scope_and_safe_statement(tmp_path: Path) -> None:
    """Change impact reports show scope, impact claims, and safer wording."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
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

    assert "## Answer" in report.markdown
    assert "## Change Scope" in report.markdown
    assert "## Safer Impact Statement" not in report.markdown
    assert (
        "Based on the checked evidence, the impact is: "
        "The change affects report wording from items to records."
        in report.markdown
    )
    assert (
        "Important qualification: Say the shown changed symbol affects report wording; "
        "verify callers before claiming it is the only effect."
        in report.markdown
    )
    assert report.markdown.index("## Answer") < report.markdown.index("## Change Scope")
    assert "Unsupported or qualified claims caught: 1 (too_broad=1)" in report.markdown
    assert report.json_report["change_context"]["changed_files"] == ["app.py"]
    assert report.json_report["measurement"]["too_broad_claims"] == 1
    assert report.json_report["measurement"]["unsupported_or_qualified_claims"] == 1


def test_report_outcome_tracks_answer_gate_and_scope(tmp_path: Path) -> None:
    """Reports lead with answer safety while retaining observable scope checks."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="How does this flow work?",
        answer="The job always skips missing providers.",
        template_id="explain_flow",
        template_values={"flow_name": "run_scheduled_job"},
    )
    claim = ClaimWorkItem(
        text="The job always skips missing providers.",
        claim_type=ClaimType.BEHAVIOR,
    )
    harness.store_claims([claim], session_id=state.session.id)
    state.traces.append(
        SearchTrace(
            claim_id=claim.id,
            query="run_scheduled_job test",
            command=["rg", "run_scheduled_job test"],
            matched_files=["app.py"],
            elapsed_ms=1,
        )
    )
    config = load_config(repo_root)
    config.cache_path = tmp_path / "cache"
    config.report_path = tmp_path
    snippet = read_evidence(
        state=state,
        config=config,
        claim_id=claim.id,
        file="app.py",
        start_line=8,
        end_line=11,
        summary="run_scheduled_job returns skipped when provider_id is missing.",
        evidence_category="main implementation path",
    )
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.SUPPORTED,
        evidence_ids=[snippet.id],
        reasoning_summary="The implementation supports the narrower function behavior.",
        contradiction_searched=True,
        contradiction_notes="Searched for tests; no global guarantee beyond the cited function was established.",
    )

    report = render_report(state=state, config=config)

    quality = report.json_report["quality"]
    assert "## Answer" in report.markdown
    assert "## Verification Outcome" in report.markdown
    assert report.markdown.index("## Answer") < report.markdown.index("## Verification Outcome")
    assert (
        "Based on the checked evidence: The job always skips missing providers."
        in report.markdown
    )
    assert "Answer gate: Safe to answer from checked evidence" in report.markdown
    assert "Score:" not in report.markdown
    assert quality["answer_gate"]["status"] == "safe_to_answer"
    assert quality["score"] < 100
    assert quality["checklist"]["required_searches"][0]["passed"] is True
    assert any(
        item["resolved_pattern"] == "run_scheduled_job error"
        for item in quality["checklist"]["contradiction_searches"]
    )
    assert any(
        item == "Run or record contradiction search: run_scheduled_job error."
        for item in quality["next_checks"]
    )
    assert quality["broad_claims"][0]["terms"] == ["always"]
    assert quality["safe_answer"]["supported"][0]["text"] == "The job always skips missing providers."


def test_report_outcome_qualifies_too_broad_claims(tmp_path: Path) -> None:
    """Too-broad claims make the report answer gate qualified, not low quality."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="Does every job skip missing providers?",
        answer="Every job skips missing providers.",
        template_id="generic_verification",
        template_values={
            "primary_entity": "provider_id",
            "primary_action": "skip",
            "claim_keyword": "job",
        },
    )
    claim = ClaimWorkItem(
        text="Every job skips missing providers.",
        claim_type=ClaimType.BEHAVIOR,
    )
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.cache_path = tmp_path / "cache"
    snippet = read_evidence(
        state=state,
        config=config,
        claim_id=claim.id,
        file="app.py",
        start_line=8,
        end_line=11,
        summary="run_scheduled_job skips missing provider_id.",
        evidence_category="direct implementation",
    )
    record_judgment(
        state=state,
        claim_id=claim.id,
        status=ClaimStatus.TOO_BROAD,
        evidence_ids=[snippet.id],
        reasoning_summary="Evidence supports one function, not every job.",
        limits="Say run_scheduled_job skips missing provider_id.",
    )

    report = render_report(state=state, config=config, write_files=False)

    quality = report.json_report["quality"]
    assert quality["answer_gate"]["status"] == "answer_with_qualifications"
    assert "Answer gate: Answer with qualifications" in report.markdown
    assert "Say with qualification:" in report.markdown
    assert "too_broad: Every job skips missing providers." in report.markdown


def test_report_quality_requires_template_values_for_placeholder_only_searches() -> None:
    """Placeholder-only template checks do not pass from unrelated non-empty searches."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="How does this flow work?",
        answer="The job skips missing providers.",
        template_id="explain_flow",
    )
    claim = ClaimWorkItem(
        text="The job skips missing providers.",
        claim_type=ClaimType.BEHAVIOR,
    )
    harness.store_claims([claim], session_id=state.session.id)
    state.traces.append(
        SearchTrace(
            claim_id=claim.id,
            query="run_scheduled_job",
            command=["rg", "run_scheduled_job"],
            matched_files=["app.py"],
            elapsed_ms=1,
        )
    )
    config = load_config(repo_root)

    report = render_report(state=state, config=config, write_files=False)

    first_required_search = report.json_report["quality"]["checklist"]["required_searches"][0]
    assert first_required_search["pattern"] == "{flow_name}"
    assert first_required_search["passed"] is False
    assert first_required_search["missing_placeholders"] == ["flow_name"]
    assert any(
        item == "Provide template value(s) for flow_name before checking required search: {flow_name}."
        for item in report.json_report["quality"]["next_checks"]
    )


def test_report_quality_skips_not_applicable_template_values() -> None:
    """Template values such as none are treated as explicitly not applicable."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="How does this flow work without an external system?",
        answer="The job has no external system.",
        template_id="explain_flow",
        template_values={
            "flow_name": "run_scheduled_job",
            "entry_point": "run_scheduled_job",
            "main_entity": "Job",
            "external_system": "none",
        },
    )
    claim = ClaimWorkItem(
        text="The job has no external system.",
        claim_type=ClaimType.BEHAVIOR,
    )
    harness.store_claims([claim], session_id=state.session.id)
    state.traces.append(
        SearchTrace(
            claim_id=claim.id,
            query="run_scheduled_job",
            command=["rg", "run_scheduled_job"],
            matched_files=["app.py"],
            elapsed_ms=1,
        )
    )
    config = load_config(repo_root)

    report = render_report(state=state, config=config, write_files=False)

    external_system_check = report.json_report["quality"]["checklist"]["required_searches"][3]
    assert external_system_check["pattern"] == "{external_system}"
    assert external_system_check["passed"] is True
    assert external_system_check["skipped"] is True
    assert external_system_check["not_applicable_placeholders"] == ["external_system"]
    assert "Run or record required search: none." not in report.json_report["quality"]["next_checks"]
