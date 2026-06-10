from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from plumbref.change_context import (
    ChangeContextError,
    build_change_context,
    parse_diff_changed_files,
)
from plumbref.models import ChangedSymbol, ChangeSource


def test_change_context_accepts_explicit_changed_files(tmp_path: Path) -> None:
    """Explicit changed files become repo-relative change context."""
    context = build_change_context(
        repo_root=tmp_path,
        source=ChangeSource.FILES,
        changed_files=["app.py"],
        changed_symbols=[ChangedSymbol(name="update_report_wording", kind="function", file="app.py")],
    )

    assert context.source == ChangeSource.FILES
    assert context.changed_files == ["app.py"]


def test_diff_text_extracts_changed_files(tmp_path: Path) -> None:
    """Diff text provides changed files without running git."""
    diff_text = "diff --git a/app.py b/app.py\n@@ -1 +1 @@\n-old\n+new\n"

    context = build_change_context(repo_root=tmp_path, source=ChangeSource.DIFF, diff_text=diff_text)

    assert parse_diff_changed_files(diff_text) == ["app.py"]
    assert context.changed_files == ["app.py"]


def test_changed_files_must_stay_inside_repo(tmp_path: Path) -> None:
    """Change context rejects paths outside the repo root."""
    with pytest.raises(ChangeContextError):
        build_change_context(
            repo_root=tmp_path,
            source=ChangeSource.FILES,
            changed_files=["../outside.py"],
        )


def test_git_diff_target_captures_changed_files(tmp_path: Path) -> None:
    """Git diff target captures changed files from local refs."""
    run_git(tmp_path, ["init", "-b", "main"])
    run_git(tmp_path, ["config", "user.email", "plumbref@example.test"])
    run_git(tmp_path, ["config", "user.name", "Plumbref Test"])
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    run_git(tmp_path, ["add", "app.py"])
    run_git(tmp_path, ["commit", "-m", "initial"])
    run_git(tmp_path, ["checkout", "-b", "change"])
    (tmp_path / "app.py").write_text("value = 2\n", encoding="utf-8")
    run_git(tmp_path, ["commit", "-am", "change"])

    context = build_change_context(repo_root=tmp_path, source=ChangeSource.BRANCH, diff_target="main...change")

    assert context.changed_files == ["app.py"]
    assert "value = 2" in context.diff_summary


def run_git(cwd: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=15)
