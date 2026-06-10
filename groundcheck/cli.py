from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from groundcheck.change_context import ChangeContextError, build_change_context
from groundcheck.config import ConfigLoadError
from groundcheck.models import (
    BudgetMode,
    ChangeSource,
    ClaimWorkItem,
    OutputMode,
    VerificationMode,
)
from groundcheck.reports import render_report
from groundcheck.sessions import HARNESS

app = typer.Typer(help="Groundcheck repo-local verification tools.")


@app.command()
def mcp(
    repo_root: Annotated[Path | None, typer.Option(help="Repository root to verify against.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to a Groundcheck TOML config file.")] = None,
) -> None:
    from groundcheck.mcp_server import run_mcp_server

    run_mcp_server(repo_root=repo_root or Path.cwd(), config_path=config)


@app.command()
def verify(
    question: Annotated[str, typer.Option(help="Original user question.")],
    answer: Annotated[Path, typer.Option(help="Path to the answer Markdown/text file.")],
    repo_root: Annotated[Path | None, typer.Option(help="Repository root to verify against.")] = None,
    claims: Annotated[Path | None, typer.Option(help="Optional JSON file of agent-extracted claims.")] = None,
    mode: Annotated[VerificationMode, typer.Option(help="Verification mode.")] = VerificationMode.EXPLANATION,
    scenario: Annotated[str | None, typer.Option(help="Scenario being verified for scenario mode.")] = None,
    changed_file: Annotated[
        list[str] | None, typer.Option("--changed-file", help="Changed file for change_impact mode.")
    ] = None,
    diff: Annotated[Path | None, typer.Option(help="Path to a git diff patch for change_impact mode.")] = None,
    diff_target: Annotated[
        str | None, typer.Option(help="Git diff target, such as main...HEAD, for change_impact mode.")
    ] = None,
    base_ref: Annotated[str | None, typer.Option(help="Base ref for change_impact mode.")] = None,
    compare_ref: Annotated[str | None, typer.Option(help="Compare ref for change_impact mode.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to a Groundcheck TOML config file.")] = None,
    budget_mode: Annotated[BudgetMode | None, typer.Option(help="Verification budget mode.")] = None,
    output_mode: Annotated[list[OutputMode] | None, typer.Option(help="Output mode.")] = None,
) -> None:
    try:
        state = HARNESS.start_session(
            repo_root=repo_root or Path.cwd(),
            question=question,
            answer=answer.read_text(encoding="utf-8"),
            mode=mode,
            scenario=scenario,
            config_path=config,
            budget_mode=budget_mode,
            output_modes=output_mode,
        )
    except ConfigLoadError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if mode == VerificationMode.CHANGE_IMPACT or changed_file or diff or diff_target or base_ref or compare_ref:
        try:
            source = change_source_for_inputs(changed_file, diff, diff_target, base_ref, compare_ref)
            context = build_change_context(
                repo_root=state.session.repo_root,
                source=source,
                changed_files=changed_file,
                diff_text=diff.read_text(encoding="utf-8") if diff else None,
                base_ref=base_ref,
                compare_ref=compare_ref,
                diff_target=diff_target,
            )
            HARNESS.record_change_context(context, session_id=state.session.id)
        except ChangeContextError as exc:
            raise typer.BadParameter(f"could not record change context: {exc}") from exc
    if claims:
        try:
            payload = json.loads(claims.read_text(encoding="utf-8"))
            HARNESS.store_claims([ClaimWorkItem.model_validate(item) for item in payload], session_id=state.session.id)
        except JSONDecodeError as exc:
            raise typer.BadParameter(f"{claims} is not valid JSON: {exc.msg}") from exc
        except ValidationError as exc:
            raise typer.BadParameter(f"{claims} does not match the Groundcheck claim schema: {exc}") from exc

    config = HARNESS.get_config(state.session.id)
    report = render_report(state=state, config=config)
    if not state.claims:
        typer.echo(
            "Groundcheck session created, but no claims were supplied. "
            "This MVP does not extract claims automatically; use MCP for the full workflow "
            "or pass --claims /path/to/claims.json."
        )
    typer.echo(report.markdown)
    if report.markdown_path:
        typer.echo(f"Markdown report: {report.markdown_path}")
    if report.json_path:
        typer.echo(f"JSON report: {report.json_path}")


def change_source_for_inputs(
    changed_file: list[str] | None,
    diff: Path | None,
    diff_target: str | None,
    base_ref: str | None,
    compare_ref: str | None,
) -> ChangeSource:
    if diff:
        return ChangeSource.DIFF
    if diff_target or base_ref or compare_ref:
        return ChangeSource.BRANCH
    if changed_file:
        return ChangeSource.FILES
    return ChangeSource.WORKTREE


if __name__ == "__main__":
    app()
