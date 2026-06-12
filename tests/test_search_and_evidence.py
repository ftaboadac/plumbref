from __future__ import annotations

from pathlib import Path

import pytest

from plumbref.config import load_config
from plumbref.evidence import EvidenceReadError, read_evidence
from plumbref.models import BudgetMode, ClaimWorkItem
from plumbref.reports import render_report
from plumbref.search import search_repo
from plumbref.sessions import PlumbrefHarness


def test_search_repo_records_trace(tmp_path: Path) -> None:
    """Repo search records matched files and increments search usage."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.cache_path = tmp_path / "cache"

    trace = search_repo(state=state, config=config, claim_id=claim.id, query="provider_id")

    assert "app.py" in trace.matched_files
    app_match = next(match for match in trace.matches if match.file == "app.py")
    assert app_match.line > 0
    assert "provider_id" in app_match.preview
    assert state.claims[claim.id].usage.searches == 1


def test_search_repo_reuses_cached_results(tmp_path: Path) -> None:
    """Repeated searches with the same repo state use the search cache."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.cache_path = tmp_path / "cache"

    first = search_repo(state=state, config=config, claim_id=claim.id, query="provider_id")
    second = search_repo(state=state, config=config, claim_id=claim.id, query="provider_id")

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.matched_files == first.matched_files
    assert state.cache_stats.search_hits == 1
    assert state.cache_stats.search_misses == 1
    assert state.claims[claim.id].usage.searches == 1


def test_search_repo_handles_queries_that_start_with_dash(tmp_path: Path) -> None:
    """CLI flag strings are treated as search patterns, not rg options."""
    repo_root = tmp_path
    (repo_root / "README.md").write_text(
        "Use plumbref templates --template-id field_migration.\n",
        encoding="utf-8",
    )
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="Where is the template flag documented?",
        answer="In the README.",
        budget_mode=BudgetMode.FAST,
    )
    claim = ClaimWorkItem(text="The README documents --template-id.")
    harness.store_claims([claim], session_id=state.session.id)
    config = load_config(repo_root)

    trace = search_repo(state=state, config=config, claim_id=claim.id, query="--template-id")

    assert "README.md" in trace.matched_files
    assert any("--template-id" in match.preview for match in trace.matches)


def test_report_includes_search_trace_matched_files(tmp_path: Path) -> None:
    """Reports show matched files so searches are inspectable."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
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
    harness = PlumbrefHarness()
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
    harness = PlumbrefHarness()
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
        include_excerpt=True,
    )

    assert snippet.file == "app.py"
    assert "missing provider_id" in snippet.excerpt


def test_read_evidence_reuses_duplicate_snippets_with_stable_ids(tmp_path: Path) -> None:
    """Duplicate snippets are stored once and linked to each claim that uses them."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    first_claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    second_claim = ClaimWorkItem(text="The missing provider branch returns a skipped status.")
    harness.store_claims([first_claim, second_claim], session_id=state.session.id)
    config = load_config(repo_root)
    config.cache_path = tmp_path / "cache"

    first = read_evidence(
        state=state,
        config=config,
        claim_id=first_claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
    )
    second = read_evidence(
        state=state,
        config=config,
        claim_id=second_claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
    )

    assert first.id == second.id
    assert first.id.startswith("ev-")
    assert second_claim.id in second.claim_ids
    assert second.excerpt == ""
    assert second.excerpt_returned is False
    assert len(state.evidence) == 1
    assert state.cache_stats.evidence_reuses == 1
    assert state.cache_stats.source_text_chars_returned == len(first.excerpt)
    assert state.claims[second_claim.id].usage.snippets == 0


def test_read_evidence_reuses_disk_cache_across_sessions(tmp_path: Path) -> None:
    """Evidence cache entries survive across sessions while source file hashes match."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    cache_path = tmp_path / "cache"
    first_harness = PlumbrefHarness()
    first_state = first_harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    first_claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    first_harness.store_claims([first_claim], session_id=first_state.session.id)
    first_config = load_config(repo_root)
    first_config.cache_path = cache_path
    first = read_evidence(
        state=first_state,
        config=first_config,
        claim_id=first_claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
    )

    second_harness = PlumbrefHarness()
    second_state = second_harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
    )
    second_claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    second_harness.store_claims([second_claim], session_id=second_state.session.id)
    second_config = load_config(repo_root)
    second_config.cache_path = cache_path
    second = read_evidence(
        state=second_state,
        config=second_config,
        claim_id=second_claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
    )

    assert second.id == first.id
    assert second.cache_hit is True
    assert second.excerpt == ""
    assert second.excerpt_returned is False
    assert second_state.cache_stats.evidence_hits == 1
    assert second_state.cache_stats.evidence_misses == 0
    assert second_state.cache_stats.source_text_chars_returned == 0
    assert second_state.claims[second_claim.id].usage.snippets == 0

    expanded = read_evidence(
        state=second_state,
        config=second_config,
        claim_id=second_claim.id,
        file="app.py",
        start_line=9,
        end_line=11,
        include_excerpt=True,
    )
    assert expanded.excerpt_returned is True
    assert "missing provider_id" in expanded.excerpt
    assert second_state.cache_stats.source_text_chars_returned == len(expanded.excerpt)


def test_read_evidence_records_template_category() -> None:
    """Evidence snippets can be tagged with template evidence categories."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=repo_root,
        question="What happens if provider_id is missing?",
        answer="The scheduled job is skipped.",
        budget_mode=BudgetMode.FAST,
        template_id="generic_verification",
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
        evidence_category="direct implementation",
    )

    assert snippet.evidence_category == "direct implementation"


def test_read_evidence_rejects_paths_outside_repo() -> None:
    """Evidence reads cannot escape the repository root."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
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
