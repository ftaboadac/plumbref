from __future__ import annotations

from pathlib import Path

import pytest

from plumbref.models import BudgetMode
from plumbref.sessions import PlumbrefHarness


def test_start_session_replaces_previous_session() -> None:
    """Plumbref keeps only one active verification session."""
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    harness = PlumbrefHarness()
    first = harness.start_session(
        repo_root=repo_root,
        question="First?",
        answer="First.",
        budget_mode=BudgetMode.FAST,
    )

    second = harness.start_session(
        repo_root=repo_root,
        question="Second?",
        answer="Second.",
        budget_mode=BudgetMode.FAST,
    )

    assert harness.get_state().session.id == second.session.id
    with pytest.raises(KeyError):
        harness.get_state(first.session.id)
