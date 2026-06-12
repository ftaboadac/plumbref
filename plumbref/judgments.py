from __future__ import annotations

from plumbref.models import ClaimStatus, Judgment, SessionState


def record_judgment(
    *,
    state: SessionState,
    claim_id: str,
    status: ClaimStatus,
    evidence_ids: list[str] | None = None,
    reasoning_summary: str = "",
    limits: str = "",
    contradiction_searched: bool = False,
    contradiction_notes: str = "",
) -> Judgment:
    resolved_evidence_ids = evidence_ids or []
    missing_evidence = [evidence_id for evidence_id in resolved_evidence_ids if evidence_id not in state.evidence]
    if missing_evidence:
        raise ValueError(f"unknown evidence ids: {', '.join(missing_evidence)}")
    claim = state.claims[claim_id]
    if status == ClaimStatus.SUPPORTED and claim.absolute_language and not contradiction_notes.strip():
        terms = ", ".join(claim.absolute_language)
        raise ValueError(
            "supported judgments for broad claims require contradiction_notes "
            f"explaining coverage for: {terms}"
        )

    judgment = Judgment(
        claim_id=claim_id,
        status=status,
        evidence_ids=resolved_evidence_ids,
        reasoning_summary=reasoning_summary,
        limits=limits,
        contradiction_searched=contradiction_searched,
        contradiction_notes=contradiction_notes,
    )
    state.judgments[claim_id] = judgment
    claim.status = status
    return judgment
