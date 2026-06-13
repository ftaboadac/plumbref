from __future__ import annotations

from pathlib import Path
from typing import Any

from plumbref.change_context import build_change_context
from plumbref.evidence import read_evidence
from plumbref.judgments import record_judgment
from plumbref.models import (
    BudgetMode,
    ChangedSymbol,
    ChangeSource,
    ClaimStatus,
    ClaimWorkItem,
    OutputMode,
    VerificationMode,
)
from plumbref.reports import render_report
from plumbref.search import search_repo
from plumbref.sessions import HARNESS
from plumbref.template_registry import get_template, load_templates, summarize_templates


def run_mcp_server(*, repo_root: Path, config_path: Path | None = None) -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("The MCP Python package is required. Install plumbref with the mcp dependency.") from exc

    server = FastMCP("plumbref")

    @server.tool()
    def plumbref_start(
        question: str,
        answer: str,
        mode: str = "explanation",
        scenario: str | None = None,
        budget_mode: str | None = None,
        output_modes: list[str] | None = None,
        template_id: str | None = None,
        template_values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Start a verification session."""
        modes = [OutputMode(output_mode) for output_mode in output_modes] if output_modes else None
        state = HARNESS.start_session(
            repo_root=repo_root,
            question=question,
            answer=answer,
            mode=VerificationMode(mode),
            scenario=scenario,
            config_path=config_path,
            budget_mode=BudgetMode(budget_mode) if budget_mode else None,
            output_modes=modes,
            template_id=template_id,
            template_values=template_values,
        )
        return state.model_dump(mode="json")

    @server.tool()
    def plumbref_list_templates() -> dict[str, Any]:
        """List built-in, user, and repo-local verification templates."""
        config = HARNESS.get_config() if HARNESS.active_session_id else None
        templates = load_templates(repo_root, config)
        return {"templates": summarize_templates(templates.values())}

    @server.tool()
    def plumbref_get_template(template_id: str) -> dict[str, Any]:
        """Return one verification template playbook by ID."""
        config = HARNESS.get_config() if HARNESS.active_session_id else None
        template = get_template(template_id, repo_root=repo_root, config=config)
        return template.model_dump(mode="json")

    @server.tool()
    def plumbref_record_change_context(
        session_id: str | None = None,
        source: str = "worktree",
        changed_files: list[str] | None = None,
        changed_symbols: list[dict[str, Any]] | None = None,
        diff_text: str | None = None,
        base_ref: str | None = None,
        compare_ref: str | None = None,
        diff_target: str | None = None,
    ) -> dict[str, Any]:
        """Store the change scope for change_impact mode."""
        state = HARNESS.get_state(session_id)
        context = build_change_context(
            repo_root=state.session.repo_root,
            source=ChangeSource(source),
            changed_files=changed_files,
            changed_symbols=[ChangedSymbol.model_validate(symbol) for symbol in (changed_symbols or [])],
            diff_text=diff_text,
            base_ref=base_ref,
            compare_ref=compare_ref,
            diff_target=diff_target,
        )
        HARNESS.record_change_context(context, session_id=state.session.id)
        return context.model_dump(mode="json")

    @server.tool()
    def plumbref_extract_claims(
        claims: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Store atomic claims extracted by the agent. Plumbref does not use an LLM to extract claims."""
        stored = HARNESS.store_claims(
            [ClaimWorkItem.model_validate(claim) for claim in claims],
            session_id=session_id,
        )
        return {"claims": [claim.model_dump(mode="json") for claim in stored]}

    @server.tool()
    def plumbref_search_repo(
        claim_id: str,
        query: str,
        session_id: str | None = None,
        max_results: int = 20,
        reference_depth: int = 0,
    ) -> dict[str, Any]:
        """Search the local repo with rg for one claim. Returns matched files plus line-numbered previews."""
        state = HARNESS.get_state(session_id)
        config = HARNESS.get_config(state.session.id)
        trace = search_repo(
            state=state,
            config=config,
            claim_id=claim_id,
            query=query,
            max_results=max_results,
            reference_depth=reference_depth,
        )
        return trace.model_dump(mode="json")

    @server.tool()
    def plumbref_read_evidence(
        claim_id: str,
        file: str,
        start_line: int,
        end_line: int,
        session_id: str | None = None,
        summary: str = "",
        evidence_category: str | None = None,
        include_excerpt: bool | None = None,
    ) -> dict[str, Any]:
        """Read a bounded source snippet for one claim. Use search results to choose file and line ranges."""
        state = HARNESS.get_state(session_id)
        config = HARNESS.get_config(state.session.id)
        snippet = read_evidence(
            state=state,
            config=config,
            claim_id=claim_id,
            file=file,
            start_line=start_line,
            end_line=end_line,
            summary=summary,
            evidence_category=evidence_category,
            include_excerpt=include_excerpt,
        )
        return snippet.model_dump(mode="json")

    @server.tool()
    def plumbref_record_judgment(
        claim_id: str,
        status: str,
        session_id: str | None = None,
        evidence_ids: list[str] | None = None,
        reasoning_summary: str = "",
        limits: str = "",
        contradiction_searched: bool = False,
        contradiction_notes: str = "",
    ) -> dict[str, Any]:
        """Record the agent's conservative judgment for one claim."""
        state = HARNESS.get_state(session_id)
        judgment = record_judgment(
            state=state,
            claim_id=claim_id,
            status=ClaimStatus(status),
            evidence_ids=evidence_ids,
            reasoning_summary=reasoning_summary,
            limits=limits,
            contradiction_searched=contradiction_searched,
            contradiction_notes=contradiction_notes,
        )
        return judgment.model_dump(mode="json")

    @server.tool()
    def plumbref_render_report(
        session_id: str | None = None,
        output_modes: list[str] | None = None,
        write_files: bool | None = None,
        report_write_reason: str | None = None,
    ) -> dict[str, Any]:
        """Render a verification result, writing report files only when policy or explicit request requires it."""
        state = HARNESS.get_state(session_id)
        config = HARNESS.get_config(state.session.id)
        modes = [OutputMode(mode) for mode in output_modes] if output_modes else None
        report = render_report(
            state=state,
            config=config,
            output_modes=modes,
            write_files=write_files,
            report_write_reason=report_write_reason,
        )
        return report.model_dump(mode="json")

    server.run(transport="stdio")
