from __future__ import annotations

from pathlib import Path

from plumbref.config import load_config
from plumbref.models import BudgetMode, OutputMode, ReportPolicy
from plumbref.sessions import PlumbrefHarness


def test_config_discovery_prefers_explicit_file(tmp_path: Path) -> None:
    """Explicit config paths override repo-local config files."""
    repo_config = tmp_path / ".plumbref.toml"
    repo_config.write_text('default_budget_mode = "deep"\n', encoding="utf-8")
    explicit_config = tmp_path / "custom.toml"
    explicit_config.write_text(
        'default_budget_mode = "fast"\ndefault_output_modes = ["json"]\n',
        encoding="utf-8",
    )

    config = load_config(tmp_path, explicit_config)

    assert config.default_budget_mode == BudgetMode.FAST
    assert config.default_output_modes == [OutputMode.JSON]


def test_config_discovery_prefers_local_over_repo_config(tmp_path: Path) -> None:
    """Repo-local private config overrides checked-in repo config."""
    (tmp_path / ".plumbref.toml").write_text('default_budget_mode = "normal"\n', encoding="utf-8")
    (tmp_path / ".plumbref.local.toml").write_text('default_budget_mode = "deep"\n', encoding="utf-8")

    config = load_config(tmp_path)

    assert config.default_budget_mode == BudgetMode.DEEP


def test_config_accepts_redaction_patterns_alias(tmp_path: Path) -> None:
    """Config supports redaction_patterns as an alias for privacy_patterns."""
    config_path = tmp_path / ".plumbref.toml"
    config_path.write_text('redaction_patterns = ["sample-secret"]\n', encoding="utf-8")

    config = load_config(tmp_path)

    assert config.privacy_patterns == ["sample-secret"]


def test_config_loads_report_policy(tmp_path: Path) -> None:
    """Report file creation policy is configurable."""
    config_path = tmp_path / ".plumbref.toml"
    config_path.write_text('report_policy = "manual"\n', encoding="utf-8")

    config = load_config(tmp_path)

    assert config.report_policy == ReportPolicy.MANUAL


def test_session_uses_config_defaults(tmp_path: Path) -> None:
    """Session startup uses config budget and output defaults when omitted."""
    config_path = tmp_path / ".plumbref.toml"
    config_path.write_text(
        'default_budget_mode = "fast"\ndefault_output_modes = ["engineer", "json"]\n',
        encoding="utf-8",
    )
    harness = PlumbrefHarness()

    state = harness.start_session(repo_root=tmp_path, question="What does this do?", answer="It verifies claims.")

    assert state.session.budget_mode == BudgetMode.FAST
    assert state.session.output_modes == [OutputMode.ENGINEER, OutputMode.JSON]
