from __future__ import annotations

import pytest

from plumbref.budgets import BudgetExceededError, budget_for_mode, ensure_can_search
from plumbref.models import BudgetMode, ClaimWorkItem


def test_budget_modes_scale_limits() -> None:
    """Deep mode allows more searches than fast mode."""
    fast = budget_for_mode(BudgetMode.FAST)
    deep = budget_for_mode(BudgetMode.DEEP)

    assert deep.searches_per_claim > fast.searches_per_claim


def test_search_budget_exhaustion_is_enforced() -> None:
    """Search budget checks fail once the per-claim limit is reached."""
    budget = budget_for_mode(BudgetMode.FAST)
    claim = ClaimWorkItem(text="The scheduled job skips work when provider_id is missing.")
    claim.usage.searches = budget.searches_per_claim

    with pytest.raises(BudgetExceededError):
        ensure_can_search(claim, budget)
