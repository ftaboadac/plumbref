from __future__ import annotations

from pathlib import Path

import pytest

from groundcheck.config import load_config
from groundcheck.evidence import EvidenceReadError, read_evidence
from groundcheck.models import BudgetMode, ClaimWorkItem
from groundcheck.reports import render_report
from groundcheck.search import search_repo
from groundcheck.sessions import GroundcheckHarness


def test_search_repo_records_trace() -> None:
    """Repo search records matched files and increments search usage."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)

    trace = search_repo(state=state, config=config, claim_id=claim.id, query="provider_id")

    assert "app.py" in trace.matched_files
    app_match = next(match for match in trace.matches if match.file == "app.py")
    assert app_match.line > 0
    assert "provider_id" in app_match.preview
    assert state.claims[claim.id].usage.searches == 1


def test_report_includes_search_trace_matched_files(tmp_path: Path) -> None:
    """Reports show matched files so searches are inspectable."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.report_path = tmp_path
    search_repo(state=state, config=config, claim_id=claim.id, query="provider_id")

    report = render_report(state=state, config=config)

    assert "Files:" in report.markdown
    assert "app.py" in report.markdown
    assert "Matches:" in report.markdown
    assert "provider_id" in report.markdown


def test_search_repo_enforces_reference_depth_budget() -> None:
    """Repo search rejects reference following beyond the claim budget."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)

    trace = search_repo(
        state=state,
        config=config,
        claim_id=claim.id,
        query="provider_id",
        reference_depth=state.budget.reference_depth + 1,
    )

    assert trace.budget_exhausted


def test_read_evidence_returns_redacted_line_snippet() -> None:
    """Evidence reads return stable line numbers and redacted excerpts."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)

    snippet = read_evidence(
        state=state,
        config=config,
        claim_id=claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
        summary="run_scheduled_job returns skipped when provider_id is missing.",
    )

    assert snippet.file == "app.py"
    assert "missing provider_id" in snippet.excerpt


def test_read_evidence_rejects_paths_outside_repo() -> None:
    """Evidence reads cannot escape the repository root."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = GroundcheckHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="Can it escape?",
        answer="No.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="Evidence reads stay inside the repo.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)

    with pytest.raises(EvidenceReadError):
        read_evidence(
            state=state,
            config=config,
            claim_id=claim.id,
            file="../../../../../../etc/hosts",
            start_line=1,
            end_line=1,
        )
