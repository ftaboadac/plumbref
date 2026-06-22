from __future__ import annotations

import json
import shutil
import subprocess
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from plumbref.change_context import ChangeContextError, build_change_context
from plumbref.checked_claims import (
    CheckedClaimError,
    export_checked_claims,
    render_checked_claim_diff,
    render_rerun_packet,
)
from plumbref.claim_checks import ClaimCheckError, render_claim_check
from plumbref.config import ConfigLoadError, load_config
from plumbref.models import (
    BudgetMode,
    ChangeSource,
    ClaimWorkItem,
    OutputMode,
    VerificationMode,
)
from plumbref.report_diff import ReportDiffError, render_report_diff
from plumbref.reports import render_report
from plumbref.sessions import HARNESS
from plumbref.template_registry import TemplateLoadError, load_templates, summarize_templates

app = typer.Typer(help="Plumbref verifies AI codebase claims before you rely on them.")

DEFAULT_CONFIG_TEXT = """ignored_paths = [
  ".git",
  ".venv",
  "node_modules",
  ".cache",
]

default_budget_mode = "normal"
default_output_modes = ["engineer", "json"]
default_template_id = "generic_verification"
report_policy = "on_demand"
"""

AGENT_INSTRUCTIONS = """When a user may rely on an AI answer about repository behavior, migration
risk, downstream consumers, or change impact, use Plumbref through MCP before
giving a confident answer.

Trigger Plumbref explicitly when the user says things like "audit that",
"check that with Plumbref", "can I rely on this", "what can I safely say", or
"run this before I send/merge". Also use it automatically for risky claims that
use wording such as only, safe to, no downstream, always, never, all, every, or
guarantee.

Workflow:
1. Choose the closest Plumbref template. Use generic_verification if no specialized template fits.
2. Start a Plumbref session with the user's question, the draft answer or
   hypothesis, the verification mode, budget mode, selected template_id, and
   concrete template_values for placeholders such as flow_name, field_name,
   changed_file, or changed_symbol.
3. Break the draft answer into atomic claims. Avoid bundling multiple behaviors into one claim.
4. Search narrowly for each claim using the template's required searches.
5. Run contradiction searches before marking a claim supported, especially when
   the wording uses only, safe to, no downstream, always, never, all, none, or
   guarantees. For broad claims, run the first-order checks needed to answer
   the claim as written before returning: changed files, non-doc/code changes,
   direct callers/references, relevant tests, and obvious docs/config references.
6. Read bounded snippets only around relevant source lines. Tag snippets with
   the closest template evidence_category when possible. Cache hits and reused
   evidence may return compact references; ask for include_excerpt=true only
   when source text needs to be inspected again.
7. Record conservative judgments. Use supported only when cited evidence
   supports the claim as written and a contradiction pass was completed. For
   too-broad, contradicted, uncertain, not-found, or not-verifiable claims,
   provide safer_wording when there is wording the user can rely on instead.
8. Render the Plumbref result. Return the `inline_answer` in chat by default.
   Let report_policy decide whether files should be written, unless the user
   explicitly asks for a report.

Answering rules:
- Prefer cited source evidence over confidence.
- Say what was not checked.
- Do not leave the obvious check unchecked when it is required to answer the
  user's actual reliance question.
- Use the report's answer gate: say what is safe to rely on from checked
  evidence, qualify too-broad claims, and do not rely on contradicted or
  unverifiable parts.
- Keep normal answers inline with `inline_answer`. Mention report paths only
  when a report was written because the user asked, the answer is risky, or
  the answer needs qualifications.
- Treat supported as supported by checked evidence, not globally true.
- Do not claim global truth from local snippets.
- Do not use Plumbref to inspect production data or external systems.
"""


@app.command()
def mcp(
    repo_root: Annotated[Path | None, typer.Option(help="Repository root to verify against.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
) -> None:
    from plumbref.mcp_server import run_mcp_server

    run_mcp_server(repo_root=repo_root or Path.cwd(), config_path=config)


@app.command()
def init(
    repo_root: Annotated[Path | None, typer.Option(help="Repository root to initialize.")] = None,
    config_file: Annotated[str, typer.Option(help="Config filename to create under the repo root.")] = ".plumbref.toml",
    force: Annotated[bool, typer.Option(help="Overwrite an existing config file.")] = False,
    print_agent_instructions: Annotated[
        bool,
        typer.Option(help="Print recommended agent instructions after setup."),
    ] = True,
) -> None:
    resolved_repo_root = (repo_root or Path.cwd()).expanduser().resolve()
    target_config = resolved_repo_root / config_file

    typer.echo(f"Repository: {resolved_repo_root}")
    if target_config.exists() and not force:
        typer.echo(f"Config exists: {target_config}")
    else:
        target_config.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        typer.echo(f"Wrote config: {target_config}")

    typer.echo("")
    typer.echo("MCP config:")
    typer.echo(json.dumps(mcp_config_for_repo(resolved_repo_root), indent=2))

    if print_agent_instructions:
        typer.echo("")
        typer.echo("Recommended agent instructions:")
        typer.echo(AGENT_INSTRUCTIONS.strip())

    typer.echo("")
    typer.echo("Next checks:")
    typer.echo(f"  plumbref doctor --repo-root {resolved_repo_root}")
    typer.echo(f"  plumbref templates --repo-root {resolved_repo_root}")


@app.command()
def doctor(
    repo_root: Annotated[Path | None, typer.Option(help="Repository root to check.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
    check_mcp_startup: Annotated[
        bool,
        typer.Option(help="Start the MCP process briefly and confirm it does not exit immediately."),
    ] = False,
) -> None:
    resolved_repo_root = (repo_root or Path.cwd()).expanduser().resolve()
    results = run_doctor_checks(
        repo_root=resolved_repo_root,
        config_path=config,
        check_mcp_startup=check_mcp_startup,
    )
    for result in results:
        marker = "ok" if result["ok"] else "fail"
        typer.echo(f"[{marker}] {result['name']}: {result['detail']}")

    failures = [result for result in results if not result["ok"]]
    if failures:
        raise typer.Exit(1)


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
    config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
    budget_mode: Annotated[BudgetMode | None, typer.Option(help="Verification budget mode.")] = None,
    output_mode: Annotated[list[OutputMode] | None, typer.Option(help="Output mode.")] = None,
    template_id: Annotated[str | None, typer.Option(help="Verification template ID.")] = None,
    template_value: Annotated[
        list[str] | None,
        typer.Option(
            "--template-value",
            help="Concrete template value as key=value, for example flow_name=checkout.",
        ),
    ] = None,
    write_report: Annotated[
        bool | None,
        typer.Option(
            "--write-report/--inline-only",
            help="Force report file creation or force inline-only output. Omit to use report_policy.",
        ),
    ] = None,
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
            template_id=template_id,
            template_values=parse_template_values(template_value or []),
        )
    except (ConfigLoadError, TemplateLoadError) as exc:
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
            raise typer.BadParameter(f"{claims} does not match the Plumbref claim schema: {exc}") from exc

    config = HARNESS.get_config(state.session.id)
    report = render_report(
        state=state,
        config=config,
        write_files=write_report,
        report_write_reason="cli_write_report" if write_report else None,
    )
    if not state.claims:
        typer.echo(
            "Plumbref session created, but no claims were supplied. "
            "This MVP does not extract claims automatically; use MCP for the full workflow "
            "or pass --claims /path/to/claims.json."
        )
    typer.echo(report.markdown)
    if report.markdown_path:
        typer.echo(f"Markdown report: {report.markdown_path}")
    if report.json_path:
        typer.echo(f"JSON report: {report.json_path}")


@app.command("templates")
def templates_command(
    repo_root: Annotated[Path | None, typer.Option(help="Repository root used for repo-local templates.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
    template_id: Annotated[str | None, typer.Option(help="Show one template in full.")] = None,
) -> None:
    try:
        resolved_repo_root = repo_root or Path.cwd()
        loaded_config = HARNESS.get_config() if HARNESS.active_session_id and config is None else None
        if loaded_config is None:
            loaded_config = load_config(resolved_repo_root, config)
        loaded = load_templates(resolved_repo_root, loaded_config)
    except (ConfigLoadError, TemplateLoadError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    if template_id:
        if template_id not in loaded:
            available = ", ".join(sorted(loaded)) or "none"
            raise typer.BadParameter(f"unknown template {template_id!r}; available templates: {available}")
        typer.echo(loaded[template_id].model_dump_json(indent=2))
        return

    for template in summarize_templates(loaded.values()):
        typer.echo(
            f"{template['id']}@{template['version']} - {template['name']} "
            f"({template['source']})"
        )


@app.command("diff-reports")
def diff_reports(
    old_report: Annotated[Path, typer.Argument(help="Old Plumbref JSON report.")],
    new_report: Annotated[Path, typer.Argument(help="New Plumbref JSON report.")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write Markdown diff to this path.")] = None,
) -> None:
    try:
        markdown = render_report_diff(old_report, new_report)
    except ReportDiffError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Wrote report diff: {output}")
        return
    typer.echo(markdown)


@app.command("export-claims")
def export_claims(
    report: Annotated[Path, typer.Argument(help="Plumbref JSON report to export claims from.")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Directory for checked-claim JSON files.")] = Path(
        ".plumbref/claims"
    ),
) -> None:
    try:
        written = export_checked_claims(report, out)
    except CheckedClaimError as exc:
        raise typer.BadParameter(str(exc)) from exc
    for path in written:
        typer.echo(f"Wrote checked claim: {path}")


@app.command("diff-claims")
def diff_claims(
    old_claim: Annotated[Path, typer.Argument(help="Old checked-claim JSON artifact.")],
    new_claim: Annotated[Path, typer.Argument(help="New checked-claim JSON artifact.")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write Markdown diff to this path.")] = None,
) -> None:
    try:
        markdown = render_checked_claim_diff(old_claim, new_claim)
    except CheckedClaimError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Wrote checked-claim diff: {output}")
        return
    typer.echo(markdown)


@app.command("rerun")
def rerun_claim(
    claim: Annotated[Path, typer.Argument(help="Checked-claim JSON artifact to rerun.")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write rerun packet to this path.")] = None,
) -> None:
    try:
        markdown = render_rerun_packet(claim)
    except CheckedClaimError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Wrote rerun packet: {output}")
        return
    typer.echo(markdown)


@app.command("check-claims")
def check_claims(
    claims: Annotated[Path, typer.Argument(help="Markdown file containing explicit claims to check.")],
    repo_root: Annotated[Path | None, typer.Option(help="Repository root for git diff.")] = None,
    diff_target: Annotated[
        str | None,
        typer.Option("--diff", help="Git diff target, such as main...HEAD. Defaults to HEAD."),
    ] = None,
    diff_file: Annotated[Path | None, typer.Option("--diff-file", help="Read changed files from a diff patch.")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write advisory Markdown to this path.")] = None,
) -> None:
    try:
        markdown = render_claim_check(
            claims_path=claims,
            repo_root=(repo_root or Path.cwd()).expanduser().resolve(),
            diff_target=diff_target,
            diff_path=diff_file,
        )
    except ClaimCheckError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Wrote claim check: {output}")
        return
    typer.echo(markdown)


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


def mcp_config_for_repo(repo_root: Path) -> dict[str, object]:
    return {
        "mcpServers": {
            "plumbref": {
                "command": "plumbref",
                "args": ["mcp", "--repo-root", str(repo_root.expanduser().resolve())],
            }
        }
    }


def parse_template_values(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        key, separator, raw = value.partition("=")
        key = key.strip()
        if not separator or not key or not raw.strip():
            raise typer.BadParameter("--template-value must use key=value with a non-empty key and value")
        parsed[key] = raw.strip()
    return parsed


def run_doctor_checks(
    *,
    repo_root: Path,
    config_path: Path | None = None,
    check_mcp_startup: bool = False,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    resolved_repo_root = repo_root.expanduser().resolve()
    results.append(
        {
            "name": "repo root",
            "ok": resolved_repo_root.is_dir(),
            "detail": str(resolved_repo_root),
        }
    )
    results.append(
        {
            "name": "ripgrep",
            "ok": shutil.which("rg") is not None,
            "detail": shutil.which("rg") or "rg not found on PATH",
        }
    )

    config_ok = False
    try:
        loaded_config = load_config(resolved_repo_root, config_path)
        config_ok = True
        results.append({"name": "config", "ok": True, "detail": "loaded"})
    except ConfigLoadError as exc:
        loaded_config = None
        results.append({"name": "config", "ok": False, "detail": str(exc)})

    if config_ok and loaded_config is not None:
        try:
            templates = load_templates(resolved_repo_root, loaded_config)
            results.append(
                {
                    "name": "templates",
                    "ok": bool(templates),
                    "detail": f"{len(templates)} template(s) loaded",
                }
            )
        except TemplateLoadError as exc:
            results.append({"name": "templates", "ok": False, "detail": str(exc)})

        try:
            loaded_config.report_path.mkdir(parents=True, exist_ok=True)
            results.append(
                {
                    "name": "report path",
                    "ok": loaded_config.report_path.is_dir(),
                    "detail": str(loaded_config.report_path),
                }
            )
        except OSError as exc:
            results.append({"name": "report path", "ok": False, "detail": str(exc)})

    if check_mcp_startup:
        results.append(check_mcp_process(resolved_repo_root, config_path))

    return results


def check_mcp_process(repo_root: Path, config_path: Path | None = None) -> dict[str, object]:
    command = [sys.executable, "-m", "plumbref", "mcp", "--repo-root", str(repo_root)]
    if config_path:
        command.extend(["--config", str(config_path)])
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=5)
        return {"name": "mcp startup", "ok": True, "detail": "process stayed running"}
    stdout, stderr = process.communicate(timeout=5)
    return {
        "name": "mcp startup",
        "ok": False,
        "detail": f"process exited early with code {process.returncode}: {stderr or stdout}",
    }


if __name__ == "__main__":
    app()
