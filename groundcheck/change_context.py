from __future__ import annotations

import subprocess
from pathlib import Path

from groundcheck.models import ChangeContext, ChangedSymbol, ChangeSource

MAX_DIFF_SUMMARY_CHARS = 12000


class ChangeContextError(ValueError):
    pass


def build_change_context(
    *,
    repo_root: Path,
    source: ChangeSource = ChangeSource.WORKTREE,
    changed_files: list[str] | None = None,
    changed_symbols: list[ChangedSymbol] | None = None,
    diff_text: str | None = None,
    base_ref: str | None = None,
    compare_ref: str | None = None,
    diff_target: str | None = None,
) -> ChangeContext:
    resolved_repo_root = repo_root.resolve()
    files = normalize_changed_files(resolved_repo_root, changed_files or [])
    symbols = normalize_changed_symbols(resolved_repo_root, changed_symbols or [])
    summary = ""
    resolved_source = source

    if diff_text:
        resolved_source = ChangeSource.DIFF
        summary = truncate_diff(diff_text)
        if not files:
            files = normalize_changed_files(resolved_repo_root, parse_diff_changed_files(diff_text))
    elif (
        diff_target or base_ref or compare_ref or (not files and source in {ChangeSource.BRANCH, ChangeSource.WORKTREE})
    ):
        git_files, git_summary = load_git_change_context(
            repo_root=resolved_repo_root,
            base_ref=base_ref,
            compare_ref=compare_ref,
            diff_target=diff_target,
        )
        if git_files:
            files = normalize_changed_files(resolved_repo_root, git_files)
        summary = git_summary
        if diff_target or base_ref or compare_ref:
            resolved_source = ChangeSource.BRANCH

    if changed_files and not diff_text and not diff_target and not base_ref and not compare_ref:
        resolved_source = ChangeSource.FILES

    return ChangeContext(
        source=resolved_source,
        base_ref=base_ref,
        compare_ref=compare_ref,
        diff_target=diff_target,
        changed_files=files,
        changed_symbols=symbols,
        diff_summary=summary,
    )


def load_git_change_context(
    *,
    repo_root: Path,
    base_ref: str | None = None,
    compare_ref: str | None = None,
    diff_target: str | None = None,
) -> tuple[list[str], str]:
    target_args = git_diff_target_args(base_ref=base_ref, compare_ref=compare_ref, diff_target=diff_target)
    files = run_git(repo_root, ["diff", "--name-only", *target_args]).splitlines()
    summary = run_git(repo_root, ["diff", "--unified=0", *target_args])
    return files, truncate_diff(summary)


def git_diff_target_args(
    *,
    base_ref: str | None = None,
    compare_ref: str | None = None,
    diff_target: str | None = None,
) -> list[str]:
    if diff_target:
        return [diff_target]
    if base_ref and compare_ref:
        return [f"{base_ref}...{compare_ref}"]
    if base_ref:
        return [base_ref]
    return []


def run_git(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip() or "git diff failed"
        raise ChangeContextError(message)
    return completed.stdout


def parse_diff_changed_files(diff_text: str) -> list[str]:
    files: list[str] = []
    for line in diff_text.splitlines():
        if not line.startswith("diff --git "):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        path = strip_diff_prefix(parts[3])
        if path and path not in files:
            files.append(path)
    return files


def strip_diff_prefix(path: str) -> str:
    if path == "/dev/null":
        return ""
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def normalize_changed_files(repo_root: Path, files: list[str]) -> list[str]:
    normalized: list[str] = []
    for file in files:
        clean_file = file.strip()
        if not clean_file:
            continue
        target = (repo_root / clean_file).resolve()
        try:
            relative = target.relative_to(repo_root)
        except ValueError as exc:
            raise ChangeContextError("changed files must be inside repo root") from exc
        value = str(relative)
        if value not in normalized:
            normalized.append(value)
    return normalized


def normalize_changed_symbols(repo_root: Path, symbols: list[ChangedSymbol]) -> list[ChangedSymbol]:
    normalized: list[ChangedSymbol] = []
    for symbol in symbols:
        file = normalize_changed_files(repo_root, [symbol.file])[0]
        normalized.append(symbol.model_copy(update={"file": file}))
    return normalized


def truncate_diff(diff_text: str) -> str:
    if len(diff_text) <= MAX_DIFF_SUMMARY_CHARS:
        return diff_text
    return diff_text[:MAX_DIFF_SUMMARY_CHARS] + "\n... diff summary truncated ..."
