from __future__ import annotations

from pathlib import Path

import pytest

from plumbref.judgments import record_judgment
from plumbref.models import (
    ChangeContext,
    ChangeSource,
    ClaimStatus,
    ClaimWorkItem,
    Judgment,
    SearchBudget,
    VerificationMode,
    VerificationSession,
)
from plumbref.sessions import PlumbrefHarness


def test_search_budget_requires_positive_limits() -> None:
    """Search budgets reject empty claim limits."""
    with pytest.raises(ValueError):
        SearchBudget(
            max_claims=0,
            searches_per_claim=1,
            files_per_claim=1,
            snippets_per_claim=1,
            reference_depth=0,
        )


def test_supported_judgment_requires_evidence_and_contradiction_pass() -> None:
    """Supported judgments require direct evidence and contradiction search."""
    with pytest.raises(ValueError):
        Judgment(claim_id="claim-1", status=ClaimStatus.SUPPORTED)


def test_verification_session_defaults_to_explanation(tmp_path: Path) -> None:
    """Verification sessions stay backward-compatible with explanation mode."""
    session = VerificationSession(repo_root=tmp_path, question="What is this?", answer="It explains code.")

    assert session.mode == VerificationMode.EXPLANATION


def test_scenario_claim_can_store_expected_outcome() -> None:
    """Scenario claims can carry predicted outcome context."""
    claim = ClaimWorkItem(
        text="The manual smoke test writes reports.",
        expected_outcome="Markdown and JSON reports are written.",
        assumptions=["The claims file is valid."],
    )

    assert claim.expected_outcome == "Markdown and JSON reports are written."


def test_claim_detects_broad_language() -> None:
    """Claims automatically record broad or absolute wording."""
    claim = ClaimWorkItem(text="This always updates every downstream job and guarantees success.")

    assert claim.absolute_language == ["always", "every", "guarantees"]


def test_claim_detects_reliance_risk_phrases() -> None:
    """Claims record common overclaim phrases users should not rely on casually."""
    claim = ClaimWorkItem(
        text="This is safe to rename, only needs a model change, and has no downstream consumers."
    )

    assert "safe to" in claim.absolute_language
    assert "only needs" in claim.absolute_language
    assert "only" in claim.absolute_language
    assert "no downstream" in claim.absolute_language
    assert "no consumers" in claim.absolute_language


def test_supported_broad_claim_requires_contradiction_notes(tmp_path: Path) -> None:
    """Broad claims need explicit notes before they can be marked supported."""
    harness = PlumbrefHarness()
    state = harness.start_session(
        repo_root=tmp_path,
        question="What changes?",
        answer="This always updates jobs.",
    )
    claim = ClaimWorkItem(text="This always updates jobs.")
    harness.store_claims([claim], session_id=state.session.id)

    with pytest.raises(ValueError, match="supported judgments for broad claims"):
        record_judgment(
            state=state,
            claim_id=claim.id,
            status=ClaimStatus.SUPPORTED,
            contradiction_searched=True,
        )


def test_change_impact_session_can_store_change_context(tmp_path: Path) -> None:
    """Change impact sessions can carry changed file context."""
    session = VerificationSession(
        repo_root=tmp_path,
        question="What changed?",
        answer="An impact statement.",
        mode=VerificationMode.CHANGE_IMPACT,
        change_context=ChangeContext(source=ChangeSource.FILES, changed_files=["app.py"]),
    )

    assert session.change_context
    assert session.change_context.changed_files == ["app.py"]
