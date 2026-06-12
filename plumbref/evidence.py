from __future__ import annotations

import hashlib
from pathlib import Path

from plumbref.budgets import (
    BudgetExceededError,
    ensure_can_open_file,
    ensure_can_read_snippet,
)
from plumbref.cache import file_sha256, read_json, stable_cache_key, write_json
from plumbref.config import PlumbrefConfig
from plumbref.models import EvidenceSnippet, SessionState
from plumbref.privacy import redact_text


class EvidenceReadError(ValueError):
    pass


def read_evidence(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    claim_id: str,
    file: str,
    start_line: int,
    end_line: int,
    summary: str = "",
    evidence_category: str | None = None,
    include_excerpt: bool | None = None,
) -> EvidenceSnippet:
    claim = state.claims[claim_id]

    repo_root = state.session.repo_root
    target = safe_repo_path(repo_root, file)
    source_sha256 = file_sha256(target)
    cache_key = evidence_cache_key(
        repo_root=repo_root,
        target=target,
        source_sha256=source_sha256,
        start_line=start_line,
        end_line=end_line,
        privacy_patterns=config.privacy_patterns,
    )
    stable_id = f"ev-{cache_key[:24]}"
    cache_path = config.cache_path / "evidence" / f"{cache_key}.json"
    if stable_id in state.evidence:
        snippet = state.evidence[stable_id]
        attach_claim_to_snippet(snippet, claim_id, evidence_category)
        state.cache_stats.evidence_reuses += 1
        if include_excerpt is True and not snippet.excerpt_returned:
            hydrate_cached_excerpt(snippet, cache_path)
        returned = returned_snippet(snippet, claim_id, include_excerpt=include_excerpt)
        if returned.excerpt_returned:
            state.cache_stats.source_text_chars_returned += len(returned.excerpt)
        return returned

    if cached_payload := read_json(cache_path):
        should_include_excerpt = include_excerpt is True
        snippet = EvidenceSnippet.model_validate(
            {
                **cached_payload,
                "claim_id": claim_id,
                "claim_ids": [claim_id],
                "excerpt": cached_payload.get("excerpt", "") if should_include_excerpt else "",
                "excerpt_returned": should_include_excerpt,
                "summary": redact_text(summary, config.privacy_patterns),
                "evidence_category": redact_text(evidence_category, config.privacy_patterns)
                if evidence_category
                else cached_payload.get("evidence_category"),
                "cache_hit": True,
                "cache_key": cache_key,
            }
        )
        state.evidence[snippet.id] = snippet
        state.cache_stats.evidence_hits += 1
        if snippet.excerpt_returned:
            state.cache_stats.source_text_chars_returned += len(snippet.excerpt)
        return snippet

    try:
        ensure_can_open_file(claim, state.budget)
        ensure_can_read_snippet(claim, state.budget)
    except BudgetExceededError as exc:
        raise EvidenceReadError(str(exc)) from exc

    state.cache_stats.evidence_misses += 1
    lines = target.read_text(encoding="utf-8").splitlines()
    if start_line < 1 or end_line < start_line:
        raise EvidenceReadError("invalid line range")
    selected = lines[start_line - 1 : end_line]
    excerpt = redact_text("\n".join(selected), config.privacy_patterns)
    should_include_excerpt = include_excerpt is not False
    snippet = EvidenceSnippet(
        id=stable_id,
        claim_id=claim_id,
        claim_ids=[claim_id],
        file=str(target.relative_to(repo_root)),
        start_line=start_line,
        end_line=min(end_line, len(lines)),
        excerpt=excerpt if should_include_excerpt else "",
        excerpt_returned=should_include_excerpt,
        summary=redact_text(summary, config.privacy_patterns),
        evidence_category=redact_text(evidence_category, config.privacy_patterns) if evidence_category else None,
        sha256=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        cache_key=cache_key,
    )
    claim.usage.files += 1
    claim.usage.snippets += 1
    state.evidence[snippet.id] = snippet
    write_json(cache_path, {**snippet.model_dump(mode="json"), "excerpt": excerpt, "excerpt_returned": True})
    if snippet.excerpt_returned:
        state.cache_stats.source_text_chars_returned += len(snippet.excerpt)
    return snippet


def safe_repo_path(repo_root: Path, file: str) -> Path:
    target = (repo_root / file).resolve()
    if not target.is_file():
        raise EvidenceReadError("evidence file does not exist")
    if repo_root.resolve() not in target.parents and target != repo_root.resolve():
        raise EvidenceReadError("evidence file must be inside repo root")
    return target


def evidence_cache_key(
    *,
    repo_root: Path,
    target: Path,
    source_sha256: str,
    start_line: int,
    end_line: int,
    privacy_patterns: list[str],
) -> str:
    return stable_cache_key(
        {
            "version": 1,
            "kind": "evidence",
            "file": target.relative_to(repo_root).as_posix(),
            "start_line": start_line,
            "end_line": end_line,
            "source_sha256": source_sha256,
            "privacy_patterns": privacy_patterns,
        }
    )


def attach_claim_to_snippet(
    snippet: EvidenceSnippet,
    claim_id: str,
    evidence_category: str | None,
) -> None:
    if claim_id not in snippet.claim_ids:
        snippet.claim_ids.append(claim_id)
    if not snippet.evidence_category and evidence_category:
        snippet.evidence_category = evidence_category


def returned_snippet(
    snippet: EvidenceSnippet,
    claim_id: str,
    *,
    include_excerpt: bool | None,
) -> EvidenceSnippet:
    if include_excerpt is True:
        return snippet
    return EvidenceSnippet.model_validate(
        {
            **snippet.model_dump(mode="json"),
            "claim_id": claim_id,
            "excerpt": "",
            "excerpt_returned": False,
        }
    )


def hydrate_cached_excerpt(snippet: EvidenceSnippet, cache_path: Path) -> None:
    cached_payload = read_json(cache_path)
    if not cached_payload:
        return
    snippet.excerpt = cached_payload.get("excerpt", "")
    snippet.excerpt_returned = bool(snippet.excerpt)
