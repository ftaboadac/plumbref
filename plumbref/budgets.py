from __future__ import annotations

from plumbref.models import BudgetMode, ClaimWorkItem, SearchBudget

BUDGETS: dict[BudgetMode, SearchBudget] = {
    BudgetMode.FAST: SearchBudget(
        max_claims=5,
        searches_per_claim=3,
        files_per_claim=4,
        snippets_per_claim=10,
        reference_depth=1,
    ),
    BudgetMode.NORMAL: SearchBudget(
        max_claims=8,
        searches_per_claim=5,
        files_per_claim=6,
        snippets_per_claim=10,
        reference_depth=2,
    ),
    BudgetMode.DEEP: SearchBudget(
        max_claims=20,
        searches_per_claim=8,
        files_per_claim=12,
        snippets_per_claim=20,
        reference_depth=3,
    ),
}


class BudgetExceededError(ValueError):
    pass


def budget_for_mode(mode: BudgetMode) -> SearchBudget:
    return BUDGETS[mode]


def can_search(claim: ClaimWorkItem, budget: SearchBudget) -> bool:
    return claim.usage.searches < budget.searches_per_claim


def can_open_file(claim: ClaimWorkItem, budget: SearchBudget) -> bool:
    return claim.usage.files < budget.files_per_claim


def can_read_snippet(claim: ClaimWorkItem, budget: SearchBudget) -> bool:
    return claim.usage.snippets < budget.snippets_per_claim


def can_follow_reference(claim: ClaimWorkItem, budget: SearchBudget) -> bool:
    return claim.usage.reference_depth < budget.reference_depth


def ensure_claim_capacity(existing_claim_count: int, budget: SearchBudget) -> None:
    if existing_claim_count >= budget.max_claims:
        raise BudgetExceededError("claim budget exhausted")


def ensure_can_search(claim: ClaimWorkItem, budget: SearchBudget) -> None:
    if not can_search(claim, budget):
        raise BudgetExceededError("search budget exhausted for claim")


def ensure_can_open_file(claim: ClaimWorkItem, budget: SearchBudget) -> None:
    if not can_open_file(claim, budget):
        raise BudgetExceededError("file-read budget exhausted for claim")


def ensure_can_read_snippet(claim: ClaimWorkItem, budget: SearchBudget) -> None:
    if not can_read_snippet(claim, budget):
        raise BudgetExceededError("snippet budget exhausted for claim")


def ensure_reference_depth(claim: ClaimWorkItem, budget: SearchBudget, reference_depth: int) -> None:
    if reference_depth > budget.reference_depth:
        raise BudgetExceededError("reference-depth budget exhausted for claim")
