from __future__ import annotations

import subprocess
import time
from pathlib import Path

from plumbref.budgets import (
    BudgetExceededError,
    ensure_can_search,
    ensure_reference_depth,
)
from plumbref.cache import read_json, repo_state_fingerprint, stable_cache_key, write_json
from plumbref.config import PlumbrefConfig
from plumbref.models import SearchMatch, SearchTrace, SessionState
from plumbref.privacy import redact_text


def search_repo(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    claim_id: str,
    query: str,
    max_results: int = 20,
    reference_depth: int = 0,
) -> SearchTrace:
    claim = state.claims[claim_id]
    command = build_rg_command(state.session.repo_root, config, query, max_results)
    cache_key = search_cache_key(
        state=state,
        config=config,
        query=query,
        max_results=max_results,
    )
    cache_path = config.cache_path / "search" / f"{cache_key}.json"
    started = time.monotonic()
    try:
        ensure_can_search(claim, state.budget)
        ensure_reference_depth(claim, state.budget, reference_depth)
    except BudgetExceededError:
        trace = SearchTrace(
            claim_id=claim_id,
            query=query,
            command=command,
            elapsed_ms=0,
            budget_exhausted=True,
            cache_key=cache_key,
        )
        state.traces.append(trace)
        return trace

    if cached_payload := read_json(cache_path):
        trace = SearchTrace.model_validate(
            {
                **cached_payload,
                "claim_id": claim_id,
                "command": command,
                "cache_hit": True,
                "cache_key": cache_key,
            }
        )
        state.cache_stats.search_hits += 1
        state.traces.append(trace)
        return trace

    state.cache_stats.search_misses += 1
    completed = subprocess.run(
        command,
        cwd=state.session.repo_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    claim.usage.searches += 1
    claim.usage.reference_depth = max(claim.usage.reference_depth, reference_depth)

    matches: list[SearchMatch] = []
    for line in completed.stdout.splitlines():
        match = parse_rg_line(state.session.repo_root, line, config)
        if match:
            matches.append(match)
        if len(matches) >= max_results:
            break
    matched_files = unique_matched_files(matches)

    trace = SearchTrace(
        claim_id=claim_id,
        query=query,
        command=command,
        matched_files=matched_files,
        matches=matches,
        elapsed_ms=elapsed_ms,
        truncated=len(matches) >= max_results,
        cache_key=cache_key,
    )
    write_json(
        cache_path,
        {
            "claim_id": claim_id,
            "query": trace.query,
            "command": trace.command,
            "matched_files": trace.matched_files,
            "matches": [match.model_dump(mode="json") for match in trace.matches],
            "elapsed_ms": trace.elapsed_ms,
            "truncated": trace.truncated,
            "budget_exhausted": trace.budget_exhausted,
            "cache_hit": False,
            "cache_key": cache_key,
        },
    )
    state.traces.append(trace)
    return trace


def build_rg_command(
    repo_root: Path,
    config: PlumbrefConfig,
    query: str,
    max_results: int,
) -> list[str]:
    command = [
        "rg",
        "--line-number",
        "--fixed-strings",
        "--color",
        "never",
        "--max-count",
        str(max_results),
    ]
    for ignored_path in config.ignored_paths:
        command.extend(["--glob", f"!{ignored_path}/**"])
    command.append("--")
    command.append(query)
    command.append(str(repo_root))
    return command


def relative_match_path(repo_root: Path, file_path: str) -> str:
    path = Path(file_path)
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return file_path


def parse_rg_line(repo_root: Path, line: str, config: PlumbrefConfig) -> SearchMatch | None:
    file_path, line_number, preview = split_rg_line(line)
    if not file_path or not line_number:
        return None
    return SearchMatch(
        file=relative_match_path(repo_root, file_path),
        line=line_number,
        preview=redact_text(preview.strip(), config.privacy_patterns),
    )


def split_rg_line(line: str) -> tuple[str, int | None, str]:
    parts = line.split(":", 2)
    if len(parts) < 3:
        return "", None, ""
    try:
        return parts[0], int(parts[1]), parts[2]
    except ValueError:
        return "", None, ""


def unique_matched_files(matches: list[SearchMatch]) -> list[str]:
    matched_files: list[str] = []
    for match in matches:
        if match.file not in matched_files:
            matched_files.append(match.file)
    return matched_files


def search_cache_key(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    query: str,
    max_results: int,
) -> str:
    if state.repo_state_fingerprint is None:
        state.repo_state_fingerprint = repo_state_fingerprint(state.session.repo_root, config.ignored_paths)
    return stable_cache_key(
        {
            "version": 1,
            "kind": "search",
            "query": query,
            "max_results": max_results,
            "ignored_paths": sorted(config.ignored_paths),
            "privacy_patterns": config.privacy_patterns,
            "repo_state": state.repo_state_fingerprint,
        }
    )
