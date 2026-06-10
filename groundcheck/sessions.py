from __future__ import annotations

from pathlib import Path

from groundcheck.budgets import budget_for_mode, ensure_claim_capacity
from groundcheck.config import GroundcheckConfig, load_config
from groundcheck.models import (
    BudgetMode,
    ChangeContext,
    ClaimWorkItem,
    OutputMode,
    SessionState,
    VerificationMode,
    VerificationSession,
)


class GroundcheckHarness:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._configs: dict[str, GroundcheckConfig] = {}
        self.active_session_id: str | None = None

    def start_session(
        self,
        *,
        repo_root: Path,
        question: str,
        answer: str,
        mode: VerificationMode = VerificationMode.EXPLANATION,
        scenario: str | None = None,
        config_path: Path | None = None,
        budget_mode: BudgetMode | None = None,
        output_modes: list[OutputMode] | None = None,
    ) -> SessionState:
        resolved_repo_root = repo_root.expanduser().resolve()
        config = load_config(resolved_repo_root, config_path)
        resolved_budget_mode = budget_mode or config.default_budget_mode
        resolved_output_modes = output_modes or config.default_output_modes
        session = VerificationSession(
            repo_root=resolved_repo_root,
            question=question,
            answer=answer,
            mode=mode,
            scenario=scenario,
            budget_mode=resolved_budget_mode,
            output_modes=resolved_output_modes,
        )
        state = SessionState(session=session, budget=budget_for_mode(resolved_budget_mode))
        self._sessions.clear()
        self._configs.clear()
        self._sessions[session.id] = state
        self._configs[session.id] = config
        self.active_session_id = session.id
        return state

    def get_state(self, session_id: str | None = None) -> SessionState:
        resolved_session_id = session_id or self.active_session_id
        if not resolved_session_id:
            raise KeyError("no active Groundcheck session")
        return self._sessions[resolved_session_id]

    def get_config(self, session_id: str | None = None) -> GroundcheckConfig:
        state = self.get_state(session_id)
        return self._configs[state.session.id]

    def store_claims(
        self,
        claims: list[ClaimWorkItem],
        *,
        session_id: str | None = None,
    ) -> list[ClaimWorkItem]:
        state = self.get_state(session_id)
        stored: list[ClaimWorkItem] = []
        for claim in claims:
            ensure_claim_capacity(len(state.claims), state.budget)
            state.claims[claim.id] = claim
            stored.append(claim)
        return stored

    def record_change_context(
        self,
        change_context: ChangeContext,
        *,
        session_id: str | None = None,
    ) -> ChangeContext:
        state = self.get_state(session_id)
        state.session.change_context = change_context
        return change_context


HARNESS = GroundcheckHarness()
