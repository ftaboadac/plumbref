from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from plumbref.cli import app, mcp_config_for_repo, run_doctor_checks


def test_mcp_config_for_repo_uses_absolute_repo_root(tmp_path: Path) -> None:
    """Generated MCP config points at the selected repository root."""
    config = mcp_config_for_repo(tmp_path)

    assert config["mcpServers"]["plumbref"]["command"] == "plumbref"
    assert config["mcpServers"]["plumbref"]["args"] == [
        "mcp",
        "--repo-root",
        str(tmp_path.resolve()),
    ]


def test_init_writes_default_config_and_prints_mcp_json(tmp_path: Path) -> None:
    """Init creates a starter config and prints copy-paste MCP setup."""
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "init",
            "--repo-root",
            str(tmp_path),
            "--no-print-agent-instructions",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / ".plumbref.toml").is_file()
    assert "MCP config:" in result.output
    assert '"command": "plumbref"' in result.output
    assert "default_template_id = \"generic_verification\"" in (tmp_path / ".plumbref.toml").read_text(
        encoding="utf-8"
    )


def test_init_does_not_overwrite_existing_config_without_force(tmp_path: Path) -> None:
    """Init is non-destructive by default."""
    config = tmp_path / ".plumbref.toml"
    config.write_text('default_budget_mode = "fast"\n', encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "init",
            "--repo-root",
            str(tmp_path),
            "--no-print-agent-instructions",
        ],
    )

    assert result.exit_code == 0
    assert config.read_text(encoding="utf-8") == 'default_budget_mode = "fast"\n'
    assert "Config exists:" in result.output


def test_doctor_checks_config_templates_and_report_path(tmp_path: Path) -> None:
    """Doctor reports core local readiness checks."""
    results = run_doctor_checks(repo_root=tmp_path)

    names = {str(result["name"]): result for result in results}
    assert names["repo root"]["ok"] is True
    assert names["config"]["ok"] is True
    assert names["templates"]["ok"] is True
    assert names["report path"]["ok"] is True


def test_doctor_command_exits_zero_when_required_checks_pass(tmp_path: Path) -> None:
    """Doctor CLI succeeds for a valid repo root and default config."""
    runner = CliRunner()

    result = runner.invoke(app, ["doctor", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "[ok] templates:" in result.output
