from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from plumbref.cache import write_json
from plumbref.config import PlumbrefConfig
from plumbref.models import (
    ClaimStatus,
    OutputMode,
    RenderedReport,
    SessionState,
    VerificationMode,
)
from plumbref.privacy import redact_text


def render_report(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    output_modes: list[OutputMode] | None = None,
    write_files: bool = True,
) -> RenderedReport:
    modes = output_modes or state.session.output_modes
    payload = build_json_report(state, config)
    markdown = build_markdown_report(state, modes, config)
    verdict = payload["verdict"]

    markdown_path: Path | None = None
    json_path: Path | None = None
    if write_files:
        config.report_path.mkdir(parents=True, exist_ok=True)
        markdown_path = config.report_path / f"{state.session.id}.md"
        json_path = config.report_path / f"{state.session.id}.json"
        markdown_path.write_text(markdown, encoding="utf-8")
        write_json(json_path, payload)

    return RenderedReport(
        session_id=state.session.id,
        verdict=verdict,
        markdown=markdown,
        json_report=payload,
        markdown_path=markdown_path,
        json_path=json_path,
    )


def build_json_report(state: SessionState, config: PlumbrefConfig) -> dict[str, Any]:
    status_counts = Counter(claim.status for claim in state.claims.values())
    verdict = overall_verdict(status_counts)
    payload = {
        "session_id": state.session.id,
        "verdict": verdict,
        "mode": state.session.mode,
        "scenario": state.session.scenario,
        "change_context": state.session.change_context.model_dump(mode="json")
        if state.session.change_context
        else None,
        "budget_mode": state.session.budget_mode,
        "claims": [
            {
                **claim.model_dump(mode="json"),
                "judgment": state.judgments.get(claim.id).model_dump(mode="json")
                if claim.id in state.judgments
                else None,
            }
            for claim in state.claims.values()
        ],
        "evidence": [snippet.model_dump(mode="json") for snippet in state.evidence.values()],
        "trace": [trace.model_dump(mode="json") for trace in state.traces],
    }
    return redact_payload(payload, config.privacy_patterns)


def build_markdown_report(
    state: SessionState,
    modes: list[OutputMode],
    config: PlumbrefConfig,
) -> str:
    payload = build_json_report(state, config)
    lines = [
        "# Plumbref Report",
        "",
        f"Verdict: {payload['verdict']}",
        f"Verification mode: {state.session.mode.value}",
        f"Budget mode: {state.session.budget_mode.value}",
    ]
    if state.session.mode == VerificationMode.SCENARIO and state.session.scenario:
        lines.extend(["", f"Scenario: {redact_text(state.session.scenario, config.privacy_patterns)}"])
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        lines.extend(["", "## Change Scope", *format_change_scope(state, config)])
    lines.extend(["", claim_section_heading(state)])
    for claim in claims_for_report(state):
        lines.extend(
            [
                "",
                f"### {claim.status.value}: {redact_text(claim.text, config.privacy_patterns)}",
                f"- Type: {claim.claim_type.value}",
                f"- Risk: {claim.risk.value}",
                "- Budget used: "
                f"searches={claim.usage.searches}, "
                f"files={claim.usage.files}, "
                f"snippets={claim.usage.snippets}, "
                f"reference_depth={claim.usage.reference_depth}",
            ],
        )
        if claim.expected_outcome:
            lines.append(f"- Predicted outcome: {redact_text(claim.expected_outcome, config.privacy_patterns)}")
        if claim.assumptions:
            assumptions = "; ".join(
                redact_text(assumption, config.privacy_patterns) for assumption in claim.assumptions
            )
            lines.append(f"- Assumptions: {assumptions}")
        judgment = state.judgments.get(claim.id)
        if judgment:
            lines.append(
                f"- Reasoning: {redact_text(judgment.reasoning_summary, config.privacy_patterns) or 'Not provided.'}"
            )
            lines.append(f"- Limits: {redact_text(judgment.limits, config.privacy_patterns) or 'Not provided.'}")
            lines.append(f"- Contradiction pass: {'yes' if judgment.contradiction_searched else 'no'}")
        evidence_for_claim = [snippet for snippet in state.evidence.values() if snippet.claim_id == claim.id]
        if evidence_for_claim:
            lines.append("- Evidence:")
            for snippet in evidence_for_claim:
                location = f"{snippet.file}:{snippet.start_line}-{snippet.end_line}"
                summary = redact_text(snippet.summary, config.privacy_patterns) or "Evidence snippet recorded."
                lines.append(f"  - `{location}`: {summary}")
                lines.extend(format_excerpt(snippet.excerpt))

    lines.extend(["", "## Search Trace"])
    if not state.traces:
        lines.append("No searches recorded.")
    for trace in state.traces:
        exhausted = " budget exhausted" if trace.budget_exhausted else ""
        lines.append(
            f"- `{trace.query}` matched {len(trace.matched_files)} file(s) in {trace.elapsed_ms}ms.{exhausted}"
        )
        if trace.matched_files:
            lines.append(f"  - Files: {', '.join(f'`{file}`' for file in trace.matched_files[:5])}")
            if len(trace.matched_files) > 5:
                lines.append(f"  - Additional files omitted: {len(trace.matched_files) - 5}")
        if trace.matches:
            lines.append("  - Matches:")
            for match in trace.matches[:5]:
                lines.append(f"    - `{match.file}:{match.line}`: {match.preview}")
            if len(trace.matches) > 5:
                lines.append(f"    - Additional matches omitted: {len(trace.matches) - 5}")

    if state.session.mode == VerificationMode.SCENARIO:
        lines.extend(["", "## Safe Conclusion", *scenario_safe_conclusion(state, config)])
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        lines.extend(["", "## Missing / Uncertain Areas", *change_impact_uncertain_areas(state, config)])
        lines.extend(["", "## Safer Impact Statement", *change_impact_safe_statement(state, config)])

    if OutputMode.SUPPORT in modes:
        lines.extend(
            [
                "",
                "## Support-Safe Summary",
                support_summary(state),
            ],
        )
    return "\n".join(lines).strip() + "\n"


def claim_section_heading(state: SessionState) -> str:
    if state.session.mode == VerificationMode.SCENARIO:
        return "## Predicted Outcomes"
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        return "## Impact Claims"
    return "## Claims"


def claims_for_report(state: SessionState) -> list[Any]:
    claims = list(state.claims.values())
    if state.session.mode != VerificationMode.CHANGE_IMPACT:
        return claims

    status_order = {
        ClaimStatus.SUPPORTED: 0,
        ClaimStatus.TOO_BROAD: 1,
        ClaimStatus.UNCERTAIN: 2,
        ClaimStatus.NOT_FOUND: 3,
        ClaimStatus.CONTRADICTED: 4,
        ClaimStatus.NOT_VERIFIABLE: 5,
    }
    return sorted(claims, key=lambda claim: status_order[claim.status])


def overall_verdict(status_counts: Counter[ClaimStatus]) -> str:
    if not status_counts:
        return "No claims recorded"
    if status_counts[ClaimStatus.CONTRADICTED]:
        return "Contradicted claims found"
    if (
        status_counts[ClaimStatus.TOO_BROAD]
        or status_counts[ClaimStatus.UNCERTAIN]
        or status_counts[ClaimStatus.NOT_FOUND]
    ):
        return "Partially supported"
    if status_counts[ClaimStatus.SUPPORTED] and len(status_counts) == 1:
        return "Supported"
    return "Partially supported"


def support_summary(state: SessionState) -> str:
    supported = [claim for claim in state.claims.values() if claim.status == ClaimStatus.SUPPORTED]
    risky = [
        claim
        for claim in state.claims.values()
        if claim.status
        in {ClaimStatus.CONTRADICTED, ClaimStatus.TOO_BROAD, ClaimStatus.UNCERTAIN, ClaimStatus.NOT_FOUND}
    ]
    if not state.claims:
        return "No verified claims are available yet."
    return (
        f"{len(supported)} claim(s) have direct source support. "
        f"{len(risky)} claim(s) need qualification or engineering confirmation before external use."
    )


def format_change_scope(state: SessionState, config: PlumbrefConfig) -> list[str]:
    context = state.session.change_context
    if not context:
        return ["No change context recorded."]

    lines = [
        f"- Source: {context.source.value}",
    ]
    if context.base_ref:
        lines.append(f"- Base ref: {redact_text(context.base_ref, config.privacy_patterns)}")
    if context.compare_ref:
        lines.append(f"- Compare ref: {redact_text(context.compare_ref, config.privacy_patterns)}")
    if context.diff_target:
        lines.append(f"- Diff target: {redact_text(context.diff_target, config.privacy_patterns)}")
    if context.changed_files:
        lines.append("- Changed files:")
        for file in context.changed_files:
            lines.append(f"  - `{redact_text(file, config.privacy_patterns)}`")
    else:
        lines.append("- Changed files: none recorded")
    if context.changed_symbols:
        lines.append("- Changed symbols:")
        for symbol in context.changed_symbols:
            location = symbol.file
            if symbol.start_line:
                location = f"{location}:{symbol.start_line}"
            symbol_kind = redact_text(symbol.kind, config.privacy_patterns)
            symbol_name = redact_text(symbol.name, config.privacy_patterns)
            lines.append(
                f"  - `{redact_text(location, config.privacy_patterns)}` "
                f"{symbol_kind} `{symbol_name}`"
            )
    if context.diff_summary:
        lines.extend(
            [
                "- Diff summary:",
                "",
                "  ```diff",
                *[f"  {line}" for line in redact_text(context.diff_summary, config.privacy_patterns).splitlines()],
                "  ```",
            ]
        )
    return lines


def change_impact_uncertain_areas(state: SessionState, config: PlumbrefConfig) -> list[str]:
    risky_statuses = {
        ClaimStatus.UNCERTAIN,
        ClaimStatus.NOT_FOUND,
        ClaimStatus.TOO_BROAD,
        ClaimStatus.CONTRADICTED,
    }
    risky = [claim for claim in state.claims.values() if claim.status in risky_statuses]
    if not risky:
        return ["No missing or uncertain impact areas were recorded."]

    lines: list[str] = []
    for claim in risky:
        judgment = state.judgments.get(claim.id)
        limits = redact_text(judgment.limits, config.privacy_patterns) if judgment else ""
        suffix = f" Limits: {limits}" if limits else ""
        lines.append(f"- {claim.status.value}: {redact_text(claim.text, config.privacy_patterns)}{suffix}")
    return lines


def change_impact_safe_statement(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if not state.claims:
        return ["No impact claims were verified."]

    supported = [claim for claim in state.claims.values() if claim.status == ClaimStatus.SUPPORTED]
    risky = [
        claim
        for claim in state.claims.values()
        if claim.status
        in {
            ClaimStatus.CONTRADICTED,
            ClaimStatus.TOO_BROAD,
            ClaimStatus.UNCERTAIN,
            ClaimStatus.NOT_FOUND,
        }
    ]
    lines = [
        f"{len(supported)} impact claim(s) are directly supported. "
        f"{len(risky)} impact claim(s) need qualification or follow-up."
    ]
    if supported:
        lines.append("")
        lines.append("Supported impact(s):")
        for claim in supported:
            lines.append(f"- {redact_text(claim.text, config.privacy_patterns)}")
    if risky:
        lines.append("")
        lines.append("Qualify or avoid:")
        for claim in risky:
            judgment = state.judgments.get(claim.id)
            limits = redact_text(judgment.limits, config.privacy_patterns) if judgment else ""
            suffix = f" Safer wording: {limits}" if limits else ""
            lines.append(f"- {claim.status.value}: {redact_text(claim.text, config.privacy_patterns)}{suffix}")
    return lines


def scenario_safe_conclusion(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if not state.claims:
        return ["No predicted outcomes were verified."]

    risky_statuses = {
        ClaimStatus.CONTRADICTED,
        ClaimStatus.TOO_BROAD,
        ClaimStatus.UNCERTAIN,
        ClaimStatus.NOT_FOUND,
    }
    supported = [claim for claim in state.claims.values() if claim.status == ClaimStatus.SUPPORTED]
    risky = [claim for claim in state.claims.values() if claim.status in risky_statuses]
    lines: list[str] = []
    if risky:
        lines.append(
            f"{len(supported)} predicted outcome(s) are directly supported. "
            f"{len(risky)} predicted outcome(s) need qualification before relying on this scenario."
        )
    else:
        lines.append("All recorded predicted outcomes are directly supported by the cited evidence.")

    if supported:
        lines.append("")
        lines.append("Supported outcome(s):")
        for claim in supported:
            lines.append(f"- {safe_outcome_text(claim, config)}")
    if risky:
        lines.append("")
        lines.append("Needs qualification:")
        for claim in risky:
            judgment = state.judgments.get(claim.id)
            limits = redact_text(judgment.limits, config.privacy_patterns) if judgment else ""
            suffix = f" Limits: {limits}" if limits else ""
            lines.append(f"- {claim.status.value}: {safe_outcome_text(claim, config)}{suffix}")
    return lines


def safe_outcome_text(claim: Any, config: PlumbrefConfig) -> str:
    text = claim.expected_outcome or claim.text
    return redact_text(text, config.privacy_patterns)


def redact_payload(value: Any, patterns: list[str]) -> Any:
    if isinstance(value, str):
        return redact_text(value, patterns)
    if isinstance(value, list):
        return [redact_payload(item, patterns) for item in value]
    if isinstance(value, dict):
        return {key: redact_payload(item, patterns) for key, item in value.items()}
    return value


def format_excerpt(excerpt: str) -> list[str]:
    if not excerpt:
        return []
    return ["", "    ```text", *[f"    {line}" for line in excerpt.splitlines()], "    ```"]
