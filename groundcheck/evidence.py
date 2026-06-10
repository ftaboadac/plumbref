from __future__ import annotations

import hashlib
from pathlib import Path

from groundcheck.budgets import (
    BudgetExceededError,
    ensure_can_open_file,
    ensure_can_read_snippet,
)
from groundcheck.config import GroundcheckConfig
from groundcheck.models import EvidenceSnippet, SessionState
from groundcheck.privacy import redact_text


class EvidenceReadError(ValueError):
    pass


def read_evidence(
    *,
    state: SessionState,
    config: GroundcheckConfig,
    claim_id: str,
    file: str,
    start_line: int,
    end_line: int,
    summary: str = "",
) -> EvidenceSnippet:
    claim = state.claims[claim_id]
    try:
        ensure_can_open_file(claim, state.budget)
        ensure_can_read_snippet(claim, state.budget)
    except BudgetExceededError as exc:
        raise EvidenceReadError(str(exc)) from exc

    repo_root = state.session.repo_root
    target = safe_repo_path(repo_root, file)
    lines = target.read_text(encoding="utf-8").splitlines()
    if start_line < 1 or end_line < start_line:
        raise EvidenceReadError("invalid line range")
    selected = lines[start_line - 1 : end_line]
    excerpt = redact_text("\n".join(selected), config.privacy_patterns)
    snippet = EvidenceSnippet(
        claim_id=claim_id,
        file=str(target.relative_to(repo_root)),
        start_line=start_line,
        end_line=min(end_line, len(lines)),
        excerpt=excerpt,
        summary=redact_text(summary, config.privacy_patterns),
        sha256=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
    )
    claim.usage.files += 1
    claim.usage.snippets += 1
    state.evidence[snippet.id] = snippet
    return snippet


def safe_repo_path(repo_root: Path, file: str) -> Path:
    target = (repo_root / file).resolve()
    if not target.is_file():
        raise EvidenceReadError("evidence file does not exist")
    if repo_root.resolve() not in target.parents and target != repo_root.resolve():
        raise EvidenceReadError("evidence file must be inside repo root")
    return target
