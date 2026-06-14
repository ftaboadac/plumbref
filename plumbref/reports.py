from __future__ import annotations

import re
from collections import Counter
from math import ceil
from pathlib import Path
from typing import Any

from plumbref.cache import read_json, stable_cache_key, write_json
from plumbref.config import PlumbrefConfig
from plumbref.models import (
    ClaimStatus,
    OutputMode,
    RenderedReport,
    ReportPolicy,
    RiskLevel,
    SessionState,
    VerificationMode,
)
from plumbref.privacy import redact_text


def render_report(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    output_modes: list[OutputMode] | None = None,
    write_files: bool | None = None,
    report_write_reason: str | None = None,
) -> RenderedReport:
    modes = output_modes or state.session.output_modes
    resolved_write_files = should_write_report(
        state=state,
        config=config,
        write_files=write_files,
        report_write_reason=report_write_reason,
    )
    resolved_write_reason = report_write_reason or default_report_write_reason(state, config)

    markdown_path: Path | None = None
    json_path: Path | None = None
    if resolved_write_files:
        dated_report_path = config.report_path / state.session.created_at.date().isoformat()
        markdown_path = dated_report_path / f"{state.session.id}.md"
        json_path = dated_report_path / f"{state.session.id}.json"

    payload = build_json_report(state, config)
    markdown = build_markdown_report(state, modes, config, json_report_path=json_path)
    inline_answer = build_inline_answer(state, config, payload)
    verdict = payload["verdict"]
    if resolved_write_files:
        dated_report_path.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        write_json(json_path, payload)
        write_report_index_entry(
            state=state,
            config=config,
            markdown_path=markdown_path,
            json_path=json_path,
            reason=resolved_write_reason,
        )

    return RenderedReport(
        session_id=state.session.id,
        verdict=verdict,
        inline_answer=inline_answer,
        markdown=markdown,
        json_report=payload,
        report_written=resolved_write_files,
        report_write_reason=resolved_write_reason if resolved_write_files else None,
        markdown_path=markdown_path,
        json_path=json_path,
    )


def should_write_report(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    write_files: bool | None,
    report_write_reason: str | None,
) -> bool:
    if write_files is not None:
        return write_files
    if config.report_policy == ReportPolicy.ALWAYS:
        return True
    if config.report_policy == ReportPolicy.MANUAL:
        return False
    return bool(report_write_reason) or should_auto_write_report(state)


def should_auto_write_report(state: SessionState) -> bool:
    if state.session.mode == VerificationMode.CHANGE_IMPACT or state.session.change_context:
        return True
    if state.session.template and state.session.template.id in {
        "field_migration",
        "downstream_consumers",
        "external_integration",
    }:
        return True
    for claim in state.claims.values():
        if claim.status != ClaimStatus.SUPPORTED:
            return True
        if claim.risk == RiskLevel.HIGH:
            return True
        if claim.absolute_language:
            return True
    return False


def default_report_write_reason(state: SessionState, config: PlumbrefConfig) -> str:
    if config.report_policy == ReportPolicy.ALWAYS:
        return "policy_always"
    if state.session.mode == VerificationMode.CHANGE_IMPACT or state.session.change_context:
        return "auto_report_due_to_change_impact"
    if state.session.template and state.session.template.id in {
        "field_migration",
        "downstream_consumers",
        "external_integration",
    }:
        return f"auto_report_due_to_{state.session.template.id}"
    for claim in state.claims.values():
        if claim.status != ClaimStatus.SUPPORTED:
            return f"auto_report_due_to_{claim.status.value}"
        if claim.risk == RiskLevel.HIGH:
            return "auto_report_due_to_high_risk_claim"
        if claim.absolute_language:
            return "auto_report_due_to_absolute_language"
    return "requested"


def write_report_index_entry(
    *,
    state: SessionState,
    config: PlumbrefConfig,
    markdown_path: Path,
    json_path: Path,
    reason: str,
) -> None:
    index_path = config.report_path / "index.json"
    existing = read_json(index_path) or {}
    reports = existing.get("reports", [])
    if not isinstance(reports, list):
        reports = []
    reports = [entry for entry in reports if not is_report_index_entry(entry, state.session.id)]
    reports.append(
        {
            "session_id": state.session.id,
            "created_at": state.session.created_at.isoformat(),
            "question": redact_text(state.session.question, config.privacy_patterns),
            "mode": state.session.mode.value,
            "template_id": state.session.template.id if state.session.template else None,
            "reason": reason,
            "markdown_path": str(markdown_path),
            "json_path": str(json_path),
        }
    )
    write_json(index_path, {"reports": reports})


def is_report_index_entry(entry: object, session_id: str) -> bool:
    return isinstance(entry, dict) and entry.get("session_id") == session_id


def build_json_report(state: SessionState, config: PlumbrefConfig) -> dict[str, Any]:
    status_counts = Counter(claim.status for claim in state.claims.values())
    verdict = overall_verdict(status_counts)
    claim_stable_ids = stable_claim_ids(state)
    payload = {
        "session_id": state.session.id,
        "created_at": state.session.created_at.isoformat(),
        "question": state.session.question,
        "verdict": verdict,
        "report_identity": build_report_identity(state),
        "mode": state.session.mode,
        "scenario": state.session.scenario,
        "template": state.session.template.model_dump(mode="json") if state.session.template else None,
        "template_values": state.session.template_values,
        "change_context": state.session.change_context.model_dump(mode="json")
        if state.session.change_context
        else None,
        "budget_mode": state.session.budget_mode,
        "quality": build_quality_summary(state),
        "measurement": build_measurement_summary(state),
        "claims": [
            {
                **claim.model_dump(mode="json"),
                "stable_id": claim_stable_ids[claim.id],
                "stable_id_scope": build_report_identity(state)["id"],
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


def build_report_identity(state: SessionState) -> dict[str, Any]:
    template_id = state.session.template.id if state.session.template else None
    normalized_question = normalize_identity_text(state.session.question)
    repo_identifier = stable_cache_key({"repo_root": str(state.session.repo_root)})[:16]
    identity = {
        "question": normalized_question,
        "mode": state.session.mode.value,
        "template_id": template_id,
        "repo_identifier": repo_identifier,
    }
    return {
        "id": stable_cache_key(identity)[:16],
        **identity,
        "repo_state": state.repo_state_fingerprint,
    }


def normalize_identity_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def stable_claim_ids(state: SessionState) -> dict[str, str]:
    return {claim.id: f"claim-{index:03d}" for index, claim in enumerate(state.claims.values(), start=1)}


def build_markdown_report(
    state: SessionState,
    modes: list[OutputMode],
    config: PlumbrefConfig,
    json_report_path: Path | None = None,
) -> str:
    payload = build_json_report(state, config)
    answer_gate = payload["quality"]["answer_gate"]
    lines = [
        "# Plumbref Report",
        "",
        f"Verdict: {payload['verdict']} - {answer_gate['label']}",
        f"Verification mode: {state.session.mode.value}",
        f"Budget mode: {state.session.budget_mode.value}",
    ]
    if state.session.template:
        lines.append(
            f"Template: {state.session.template.name} (`{state.session.template.id}` v{state.session.template.version})"
        )
        if state.session.template_values:
            values = ", ".join(
                f"`{key}={redact_text(value, config.privacy_patterns)}`"
                for key, value in sorted(state.session.template_values.items())
            )
            lines.append(f"Template values: {values}")
    if state.session.mode == VerificationMode.SCENARIO and state.session.scenario:
        lines.extend(["", f"Scenario: {redact_text(state.session.scenario, config.privacy_patterns)}"])
    lines.extend(["", "## Verification Outcome", *format_quality_summary(payload["quality"])])
    lines.extend(["", "## Answer Under Review", *answer_under_review(state, config)])
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        lines.extend(["", "## Change Scope", *format_change_scope(state, config)])

    issue_claims = [claim for claim in claims_for_report(state) if claim.status != ClaimStatus.SUPPORTED]
    supported_claims = [claim for claim in claims_for_report(state) if claim.status == ClaimStatus.SUPPORTED]
    rendered_excerpt_ids: set[str] = set()
    lines.extend(["", "## Issues That Need Action"])
    if issue_claims:
        for claim in issue_claims:
            lines.extend(render_claim_detail(state, claim, config, rendered_excerpt_ids))
    else:
        lines.append("None. No unsupported, contradicted, uncertain, or too-broad claims were recorded.")

    lines.extend(["", supported_claims_heading(state)])
    if supported_claims:
        for claim in supported_claims:
            lines.extend(render_claim_detail(state, claim, config, rendered_excerpt_ids))
    else:
        lines.append("None recorded.")

    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        lines.extend(["", "## Missing / Uncertain Areas", *change_impact_uncertain_areas(state, config)])

    if OutputMode.SUPPORT in modes:
        lines.extend(
            [
                "",
                "## Support-Safe Summary",
                support_summary(state),
            ],
        )
    lines.extend(
        [
            "",
            "## What Wasn't Checked And Why It Matters",
            *format_unchecked_scope(payload["quality"]),
        ]
    )
    lines.extend(["", "## Measurement", *format_measurement_summary(payload["measurement"])])
    lines.extend(["", "## JSON / Full Trace", *format_json_trace_note(json_report_path)])
    lines.extend(
        [
            "",
            "## To Make A Broader Claim, Verify",
            *format_next_checks(payload["quality"]),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_measurement_summary(state: SessionState) -> dict[str, Any]:
    status_counts = Counter(claim.status.value for claim in state.claims.values())
    unsupported_statuses = {
        ClaimStatus.CONTRADICTED.value,
        ClaimStatus.TOO_BROAD.value,
        ClaimStatus.UNCERTAIN.value,
        ClaimStatus.NOT_FOUND.value,
        ClaimStatus.NOT_VERIFIABLE.value,
    }
    judged_claims = [claim for claim in state.claims.values() if claim.id in state.judgments]
    contradiction_passes = sum(1 for claim in judged_claims if state.judgments[claim.id].contradiction_searched)
    return {
        "claims_total": len(state.claims),
        "claim_status_counts": dict(sorted(status_counts.items())),
        "search_traces_recorded": len(state.traces),
        "searches_run": sum(claim.usage.searches for claim in state.claims.values()),
        "search_matches_returned": sum(len(trace.matches) for trace in state.traces),
        "matched_files": len({file for trace in state.traces for file in trace.matched_files}),
        "evidence_files_read": sum(claim.usage.files for claim in state.claims.values()),
        "evidence_snippets_read": sum(claim.usage.snippets for claim in state.claims.values()),
        "unique_evidence_files": len({snippet.file for snippet in state.evidence.values()}),
        "source_text_chars_returned": state.cache_stats.source_text_chars_returned,
        "source_text_estimated_tokens_returned": estimate_tokens(state.cache_stats.source_text_chars_returned),
        "token_estimate": build_token_estimate(state),
        "cache": {
            **state.cache_stats.model_dump(mode="json"),
            "search_hit_rate_percent": hit_rate_percent(
                state.cache_stats.search_hits,
                state.cache_stats.search_misses,
            ),
            "evidence_hit_rate_percent": hit_rate_percent(
                state.cache_stats.evidence_hits,
                state.cache_stats.evidence_misses,
            ),
        },
        "contradiction_passes": contradiction_passes,
        "judged_claims": len(judged_claims),
        "too_broad_claims": status_counts[ClaimStatus.TOO_BROAD.value],
        "unsupported_or_qualified_claims": sum(status_counts[status] for status in unsupported_statuses),
    }


def format_measurement_summary(measurement: dict[str, Any]) -> list[str]:
    status_counts = measurement["claim_status_counts"]
    status_text = ", ".join(f"{status}={count}" for status, count in status_counts.items()) or "none"
    token_estimate = measurement.get("token_estimate")
    lines = [
        *format_token_reduction_summary(token_estimate),
        f"- Claims: {measurement['claims_total']} ({status_text})",
        (f"- Searches: {measurement['searches_run']} run, {measurement['search_traces_recorded']} trace(s) recorded"),
        (
            "- Search results: "
            f"{measurement['search_matches_returned']} match(es) across "
            f"{measurement['matched_files']} matched file(s)"
        ),
        (
            "- Evidence read: "
            f"{measurement['evidence_files_read']} file read(s), "
            f"{measurement['evidence_snippets_read']} snippet(s), "
            f"{measurement['unique_evidence_files']} unique evidence file(s)"
        ),
        (
            "- Source text returned: "
            f"{measurement['source_text_estimated_tokens_returned']} estimated token(s) "
            f"from {measurement['source_text_chars_returned']} character(s)"
        ),
        (
            "- Contradiction passes: "
            f"{measurement['contradiction_passes']}/{measurement['judged_claims']} judged claim(s)"
        ),
        (
            "- Unsupported or qualified claims caught: "
            f"{measurement['unsupported_or_qualified_claims']} "
            f"(too_broad={measurement['too_broad_claims']})"
        ),
    ]
    if cache := measurement.get("cache"):
        lines.extend(format_cache_summary(cache))
    if token_estimate:
        lines.extend(format_token_estimate_details(token_estimate))
    return lines


def format_cache_summary(cache: dict[str, Any]) -> list[str]:
    return [
        (
            "- Cache reuse: "
            f"searches {cache['search_hit_rate_percent']}% hit rate; "
            f"evidence {cache['evidence_hit_rate_percent']}% hit rate; "
            f"{cache['evidence_reuses']} in-session evidence reuse(s)"
        ),
    ]


def hit_rate_percent(hits: int, misses: int) -> int:
    total = hits + misses
    if total == 0:
        return 0
    return round((hits / total) * 100)


def build_quality_summary(state: SessionState) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    next_checks: list[str] = []
    checked: list[str] = []
    not_checked: list[str] = []

    claims = list(state.claims.values())
    judgments = state.judgments
    supported_claims = [claim for claim in claims if claim.status == ClaimStatus.SUPPORTED]
    unjudged_claims = [claim for claim in claims if claim.id not in judgments]
    broad_claims = [claim for claim in claims if claim.absolute_language]
    broad_supported_without_notes = [
        claim
        for claim in supported_claims
        if claim.absolute_language
        and not (judgments.get(claim.id).contradiction_notes if claim.id in judgments else "")
    ]

    add_quality_check(
        checks,
        key="claims_recorded",
        label="Claims recorded",
        passed=bool(claims),
        completed=len(claims),
        total=max(1, len(claims)),
        missing=[] if claims else ["Store at least one atomic claim."],
    )
    add_quality_check(
        checks,
        key="claims_judged",
        label="Claims judged",
        passed=bool(claims) and not unjudged_claims,
        completed=len(claims) - len(unjudged_claims),
        total=len(claims),
        missing=[claim.text for claim in unjudged_claims],
    )
    add_quality_check(
        checks,
        key="supported_claims_have_evidence",
        label="Supported claims cite evidence",
        passed=all(claim.id in judgments and judgments[claim.id].evidence_ids for claim in supported_claims),
        completed=sum(1 for claim in supported_claims if claim.id in judgments and judgments[claim.id].evidence_ids),
        total=len(supported_claims),
        missing=[
            claim.text
            for claim in supported_claims
            if claim.id not in judgments or not judgments[claim.id].evidence_ids
        ],
    )
    add_quality_check(
        checks,
        key="supported_claims_have_contradiction_pass",
        label="Supported claims have contradiction passes",
        passed=all(claim.id in judgments and judgments[claim.id].contradiction_searched for claim in supported_claims),
        completed=sum(
            1 for claim in supported_claims if claim.id in judgments and judgments[claim.id].contradiction_searched
        ),
        total=len(supported_claims),
        missing=[
            claim.text
            for claim in supported_claims
            if claim.id not in judgments or not judgments[claim.id].contradiction_searched
        ],
    )
    add_quality_check(
        checks,
        key="broad_supported_claims_have_contradiction_notes",
        label="Supported broad claims explain broad-language coverage",
        passed=not broad_supported_without_notes,
        completed=len(supported_claims) - len(broad_supported_without_notes),
        total=len(supported_claims),
        missing=[claim.text for claim in broad_supported_without_notes],
    )

    template = state.session.template
    search_completion: list[dict[str, Any]] = []
    contradiction_search_completion: list[dict[str, Any]] = []
    evidence_category_completion: list[dict[str, Any]] = []
    claim_type_completion: list[dict[str, Any]] = []
    if template:
        present_claim_types = {claim.claim_type for claim in claims}
        for claim_type in template.required_claim_types:
            passed = claim_type in present_claim_types
            item = {
                "claim_type": claim_type.value,
                "passed": passed,
            }
            claim_type_completion.append(item)
            add_quality_check(
                checks,
                key=f"required_claim_type:{claim_type.value}",
                label=f"Required claim type: {claim_type.value}",
                passed=passed,
                completed=1 if passed else 0,
                total=1,
                missing=[] if passed else [claim_type.value],
            )

        for pattern in template.required_searches:
            item = search_pattern_completion(pattern, state.traces, state.session.template_values)
            search_completion.append(item)
            add_quality_check(
                checks,
                key=f"required_search:{pattern}",
                label=f"Required search: {pattern}",
                passed=item["passed"],
                completed=1 if item["passed"] else 0,
                total=1,
                missing=[] if item["passed"] else [pattern],
            )

        for pattern in template.contradiction_searches:
            item = search_pattern_completion(pattern, state.traces, state.session.template_values)
            contradiction_search_completion.append(item)
            add_quality_check(
                checks,
                key=f"contradiction_search:{pattern}",
                label=f"Contradiction search: {pattern}",
                passed=item["passed"],
                completed=1 if item["passed"] else 0,
                total=1,
                missing=[] if item["passed"] else [pattern],
            )

        recorded_categories = {
            normalize_check_text(snippet.evidence_category)
            for snippet in state.evidence.values()
            if snippet.evidence_category
        }
        for category in template.evidence_categories:
            passed = normalize_check_text(category) in recorded_categories
            item = {
                "category": category,
                "passed": passed,
            }
            evidence_category_completion.append(item)
            add_quality_check(
                checks,
                key=f"evidence_category:{category}",
                label=f"Evidence category: {category}",
                passed=passed,
                completed=1 if passed else 0,
                total=1,
                missing=[] if passed else [category],
            )

    for check in checks:
        if check["passed"]:
            checked.append(check["label"])
        else:
            not_checked.append(check["label"])

    if not claims:
        next_checks.append("Store atomic claims before treating the report as verification.")
    if unjudged_claims:
        next_checks.append(f"Record judgments for {len(unjudged_claims)} claim(s).")
    for item in search_completion:
        if not item["passed"]:
            next_checks.append(search_next_check("required search", item))
    for item in contradiction_search_completion:
        if not item["passed"]:
            next_checks.append(search_next_check("contradiction search", item))
    for item in evidence_category_completion:
        if not item["passed"]:
            next_checks.append(f"Read evidence for required category: {item['category']}.")
    for claim in broad_supported_without_notes:
        terms = ", ".join(claim.absolute_language)
        next_checks.append(f"Add contradiction notes for broad claim using: {terms}.")
    for claim in broad_claims:
        if claim.status != ClaimStatus.SUPPORTED:
            next_checks.append(f"Keep broad claim qualified or narrow it: {claim.text}")

    checks_total = len(checks)
    checks_passed = sum(1 for check in checks if check["passed"])
    score = round((checks_passed / checks_total) * 100) if checks_total else 0
    answer_gate = build_answer_gate(state, unjudged_claims)
    return {
        "answer_gate": answer_gate,
        "score": score,
        "grade": quality_grade(score, checks_total),
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "summary": f"{checks_passed}/{checks_total} observable verification check(s) complete.",
        "checked": checked,
        "not_checked": not_checked,
        "next_checks": dedupe_preserve_order(next_checks)[:12],
        "checklist": {
            "checks": checks,
            "required_claim_types": claim_type_completion,
            "required_searches": search_completion,
            "contradiction_searches": contradiction_search_completion,
            "evidence_categories": evidence_category_completion,
        },
        "broad_claims": [
            {
                "claim_id": claim.id,
                "text": claim.text,
                "terms": claim.absolute_language,
                "status": claim.status.value,
                "requires_strict_support": claim.status == ClaimStatus.SUPPORTED,
                "contradiction_notes": judgments[claim.id].contradiction_notes if claim.id in judgments else "",
            }
            for claim in broad_claims
        ],
        "safe_answer": build_safe_answer_summary(state),
    }


def build_answer_gate(
    state: SessionState,
    unjudged_claims: list[Any],
) -> dict[str, Any]:
    claims = list(state.claims.values())
    status_counts = Counter(claim.status.value for claim in claims)
    if not claims:
        return {
            "status": "not_ready",
            "label": "Not ready to answer",
            "summary": "No claims were recorded yet.",
            "can_answer": False,
        }
    if unjudged_claims:
        return {
            "status": "not_ready",
            "label": "Not ready to answer",
            "summary": f"{len(unjudged_claims)} claim(s) still need judgment.",
            "can_answer": False,
        }
    if status_counts[ClaimStatus.CONTRADICTED.value]:
        return {
            "status": "do_not_claim",
            "label": "Do not claim as written",
            "summary": "At least one claim is contradicted by source evidence.",
            "can_answer": False,
        }
    if status_counts[ClaimStatus.NOT_VERIFIABLE.value]:
        return {
            "status": "answer_with_limits",
            "label": "Answer with limits",
            "summary": "Some parts cannot be verified from local source evidence.",
            "can_answer": True,
        }
    qualified_count = sum(
        status_counts[status.value] for status in (ClaimStatus.TOO_BROAD, ClaimStatus.UNCERTAIN, ClaimStatus.NOT_FOUND)
    )
    if qualified_count:
        return {
            "status": "answer_with_qualifications",
            "label": "Answer with qualifications",
            "summary": f"{qualified_count} claim(s) need narrower wording or qualification.",
            "can_answer": True,
        }
    if status_counts[ClaimStatus.SUPPORTED.value] == len(claims):
        return {
            "status": "safe_to_answer",
            "label": "Safe to answer from checked evidence",
            "summary": "All recorded claims are supported by cited source evidence.",
            "can_answer": True,
        }
    return {
        "status": "answer_with_limits",
        "label": "Answer with limits",
        "summary": "Use only the parts supported by recorded source evidence.",
        "can_answer": True,
    }


def add_quality_check(
    checks: list[dict[str, Any]],
    *,
    key: str,
    label: str,
    passed: bool,
    completed: int,
    total: int,
    missing: list[str],
) -> None:
    checks.append(
        {
            "key": key,
            "label": label,
            "passed": passed,
            "completed": completed,
            "total": total,
            "missing": missing,
        }
    )


def search_pattern_completion(
    pattern: str,
    traces: list[Any],
    template_values: dict[str, str] | None = None,
) -> dict[str, Any]:
    resolved = resolve_pattern(pattern, template_values or {})
    if resolved["not_applicable_placeholders"]:
        return {
            "pattern": pattern,
            "resolved_pattern": resolved["resolved_pattern"],
            "missing_placeholders": [],
            "not_applicable_placeholders": resolved["not_applicable_placeholders"],
            "literal_tokens": [],
            "passed": True,
            "skipped": True,
            "matched_queries": [],
        }
    if resolved["missing_placeholders"]:
        return {
            "pattern": pattern,
            "resolved_pattern": resolved["resolved_pattern"],
            "missing_placeholders": resolved["missing_placeholders"],
            "not_applicable_placeholders": [],
            "literal_tokens": [],
            "passed": False,
            "skipped": False,
            "matched_queries": [],
        }
    literal_tokens = normalize_tokens(resolved["resolved_pattern"])
    matched_queries: list[str] = []
    for trace in traces:
        query_tokens = normalize_tokens(trace.query)
        if literal_tokens and all(token in query_tokens for token in literal_tokens):
            matched_queries.append(trace.query)
    return {
        "pattern": pattern,
        "resolved_pattern": resolved["resolved_pattern"],
        "missing_placeholders": [],
        "not_applicable_placeholders": [],
        "literal_tokens": literal_tokens,
        "passed": bool(matched_queries),
        "skipped": False,
        "matched_queries": dedupe_preserve_order(matched_queries),
    }


def resolve_pattern(pattern: str, template_values: dict[str, str]) -> dict[str, Any]:
    missing: list[str] = []
    not_applicable: list[str] = []

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = template_values.get(key, "").strip()
        if not value:
            missing.append(key)
            return match.group(0)
        if is_not_applicable_template_value(value):
            not_applicable.append(key)
            return value
        return value

    resolved = re.sub(r"\{([^}]+)\}", replace, pattern)
    return {
        "resolved_pattern": resolved,
        "missing_placeholders": dedupe_preserve_order(missing),
        "not_applicable_placeholders": dedupe_preserve_order(not_applicable),
    }


def is_not_applicable_template_value(value: str) -> bool:
    normalized = normalize_check_text(value)
    return normalized in {
        "na",
        "n a",
        "none",
        "not applicable",
        "not_applicable",
        "no external system",
    }


def search_next_check(kind: str, item: dict[str, Any]) -> str:
    missing = item.get("missing_placeholders") or []
    if missing:
        return f"Provide template value(s) for {', '.join(missing)} before checking {kind}: {item['pattern']}."
    return f"Run or record {kind}: {item.get('resolved_pattern') or item['pattern']}."


def normalize_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def normalize_check_text(text: str | None) -> str:
    return " ".join(normalize_tokens(text or ""))


def quality_grade(score: int, checks_total: int) -> str:
    if checks_total == 0:
        return "not_started"
    if score >= 90:
        return "complete"
    if score >= 70:
        return "mostly_complete"
    if score >= 40:
        return "partial"
    return "incomplete"


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped


def build_safe_answer_summary(state: SessionState) -> dict[str, Any]:
    supported = []
    qualified = []
    avoid = []
    for claim in state.claims.values():
        judgment = state.judgments.get(claim.id)
        item = {
            "claim_id": claim.id,
            "text": claim.text,
            "status": claim.status.value,
            "limits": judgment.limits if judgment else "",
        }
        if claim.status == ClaimStatus.SUPPORTED:
            supported.append(item)
        elif claim.status in {ClaimStatus.TOO_BROAD, ClaimStatus.UNCERTAIN, ClaimStatus.NOT_FOUND}:
            qualified.append(item)
        elif claim.status in {ClaimStatus.CONTRADICTED, ClaimStatus.NOT_VERIFIABLE}:
            avoid.append(item)
    return {
        "supported": supported,
        "qualified": qualified,
        "avoid": avoid,
    }


def format_quality_summary(quality: dict[str, Any]) -> list[str]:
    answer_gate = quality["answer_gate"]
    lines = [
        f"- Answer gate: {answer_gate['label']}",
        f"- Why: {answer_gate['summary']}",
    ]
    safe_answer = quality["safe_answer"]
    supported = safe_answer["supported"]
    qualified = safe_answer["qualified"]
    avoid = safe_answer["avoid"]
    lines.append(f"- Claim outcome: {len(supported)} supported, {len(qualified)} qualified, {len(avoid)} avoid")
    if supported:
        lines.append("- Safe to say:")
        for item in supported[:6]:
            lines.append(f"  - {item['text']}")
    if qualified:
        lines.append("- Say with qualification:")
        for item in qualified[:6]:
            suffix = f" Limits: {item['limits']}" if item["limits"] else ""
            lines.append(f"  - {item['status']}: {item['text']}{suffix}")
    if avoid:
        lines.append("- Avoid:")
        for item in avoid[:6]:
            suffix = f" Limits: {item['limits']}" if item["limits"] else ""
            lines.append(f"  - {item['status']}: {item['text']}{suffix}")
    return lines


def format_unchecked_scope(quality: dict[str, Any]) -> list[str]:
    not_checked = quality["not_checked"]
    if not not_checked:
        return ["No remaining checklist gaps were recorded."]

    lines = [
        ("Not checked - may affect confidence: " + ", ".join(not_checked[:8]) + "."),
        (
            "Risk: broader answers may miss required claim types, contradiction paths, "
            "or evidence categories until these checks are completed."
        ),
    ]
    if len(not_checked) > 8:
        lines.append(f"{len(not_checked) - 8} more unchecked item(s) are in the JSON report.")
    return lines


def format_next_checks(quality: dict[str, Any]) -> list[str]:
    next_checks = quality["next_checks"]
    if not next_checks:
        return ["None. The recorded claims do not require broader follow-up checks."]
    return [f"- {item}" for item in next_checks]


def format_json_trace_note(json_report_path: Path | None) -> list[str]:
    if json_report_path:
        return [
            "Full checklist details, per-claim budgets, and search trace: "
            f"[{json_report_path.name}]({json_report_path.name})."
        ]
    return ["Full checklist details, per-claim budgets, and search trace are included in the JSON report output."]


def build_token_estimate(state: SessionState) -> dict[str, Any]:
    evidence_excerpt_chars = sum(
        len(snippet.excerpt) for snippet in state.evidence.values() if snippet.excerpt_returned
    )
    search_preview_chars = sum(len(match.preview) for trace in state.traces for match in trace.matches)
    cited_full_file_chars = sum_repo_file_chars(
        state.session.repo_root,
        {snippet.file for snippet in state.evidence.values()},
    )
    matched_full_file_chars = sum_repo_file_chars(
        state.session.repo_root,
        {file for trace in state.traces for file in trace.matched_files},
    )
    return {
        "method": "estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing",
        "returned_evidence_chars": evidence_excerpt_chars,
        "returned_evidence_estimated_tokens": estimate_tokens(evidence_excerpt_chars),
        "search_preview_chars": search_preview_chars,
        "search_preview_estimated_tokens": estimate_tokens(search_preview_chars),
        "full_cited_files_chars": cited_full_file_chars,
        "full_cited_files_estimated_tokens": estimate_tokens(cited_full_file_chars),
        "full_matched_files_chars": matched_full_file_chars,
        "full_matched_files_estimated_tokens": estimate_tokens(matched_full_file_chars),
        "bounded_vs_full_cited_files_token_reduction_percent": token_reduction_percent(
            evidence_excerpt_chars,
            cited_full_file_chars,
        ),
        "bounded_vs_full_matched_files_token_reduction_percent": token_reduction_percent(
            evidence_excerpt_chars,
            matched_full_file_chars,
        ),
    }


def format_token_reduction_summary(token_estimate: dict[str, Any] | None) -> list[str]:
    if not token_estimate:
        return []
    cited_reduction = token_estimate["bounded_vs_full_cited_files_token_reduction_percent"]
    matched_reduction = token_estimate["bounded_vs_full_matched_files_token_reduction_percent"]
    return [
        (
            "- **Token reduction from bounded evidence: "
            f"{cited_reduction}% vs full cited files; "
            f"{matched_reduction}% vs full matched files.**"
        )
    ]


def format_token_estimate_details(token_estimate: dict[str, Any]) -> list[str]:
    cited_reduction = token_estimate["bounded_vs_full_cited_files_token_reduction_percent"]
    matched_reduction = token_estimate["bounded_vs_full_matched_files_token_reduction_percent"]
    return [
        "- Source-token estimate details:",
        (f"  - Returned evidence excerpts: {token_estimate['returned_evidence_estimated_tokens']} estimated token(s)"),
        (f"  - Search previews: {token_estimate['search_preview_estimated_tokens']} estimated token(s)"),
        (
            "  - Full cited files baseline: "
            f"{token_estimate['full_cited_files_estimated_tokens']} estimated token(s) "
            f"({cited_reduction}% reduction from bounded evidence)"
        ),
        (
            "  - Full matched files baseline: "
            f"{token_estimate['full_matched_files_estimated_tokens']} estimated token(s) "
            f"({matched_reduction}% reduction from bounded evidence)"
        ),
        f"  - Method: {token_estimate['method']}",
    ]


def estimate_tokens(character_count: int) -> int:
    if character_count <= 0:
        return 0
    return ceil(character_count / 4)


def token_reduction_percent(bounded_chars: int, baseline_chars: int) -> int:
    if baseline_chars <= 0:
        return 0
    reduction = 1 - (bounded_chars / baseline_chars)
    return max(0, round(reduction * 100))


def sum_repo_file_chars(repo_root: Path, files: set[str]) -> int:
    total = 0
    for file in files:
        target = (repo_root / file).resolve()
        if repo_root.resolve() not in target.parents and target != repo_root.resolve():
            continue
        try:
            total += len(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return total


def format_template_checklist(state: SessionState, config: PlumbrefConfig) -> list[str]:
    template = state.session.template
    if not template:
        return []

    lines = [
        f"- Source: {redact_text(template.source, config.privacy_patterns)}",
    ]
    if state.session.template_values:
        values = ", ".join(
            f"`{key}={redact_text(value, config.privacy_patterns)}`"
            for key, value in sorted(state.session.template_values.items())
        )
        lines.append(f"- Template values: {values}")
    else:
        lines.append("- Template values: none")
    if template.required_claim_types:
        lines.append(
            "- Required claim types: "
            + ", ".join(f"`{claim_type.value}`" for claim_type in template.required_claim_types)
        )
    lines.extend(format_template_list("Required searches", template.required_searches, config))
    lines.extend(format_template_list("Contradiction searches", template.contradiction_searches, config))
    lines.extend(format_template_list("Evidence categories", template.evidence_categories, config))
    lines.extend(format_template_list("Report sections", template.report_sections, config))
    if template.unchecked_area_prompts:
        lines.append("- Unchecked-area prompts:")
        for prompt in template.unchecked_area_prompts:
            lines.append(f"  - {redact_text(prompt, config.privacy_patterns)}")

    evidence_categories = sorted(
        {snippet.evidence_category for snippet in state.evidence.values() if snippet.evidence_category}
    )
    if evidence_categories:
        recorded_categories = ", ".join(f"`{category}`" for category in evidence_categories)
        lines.append(f"- Evidence categories recorded: {recorded_categories}")
    else:
        lines.append("- Evidence categories recorded: none")

    judged_claims = [claim for claim in state.claims.values() if claim.id in state.judgments]
    contradiction_count = sum(1 for claim in judged_claims if state.judgments[claim.id].contradiction_searched)
    lines.append(f"- Contradiction passes recorded: {contradiction_count}/{len(judged_claims)} judged claim(s)")
    return lines


def format_template_list(label: str, values: list[str], config: PlumbrefConfig) -> list[str]:
    if not values:
        return []
    lines = [f"- {label}:"]
    for value in values:
        lines.append(f"  - `{redact_text(value, config.privacy_patterns)}`")
    return lines


def claim_section_heading(state: SessionState) -> str:
    if state.session.mode == VerificationMode.SCENARIO:
        return "## Predicted Outcomes"
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        return "## Impact Claims"
    return "## Claims"


def supported_claims_heading(state: SessionState) -> str:
    if state.session.mode == VerificationMode.SCENARIO:
        return "## Supported Predicted Outcomes"
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        return "## Supported Impact Claims"
    return "## Supported Claims"


def claims_for_report(state: SessionState) -> list[Any]:
    claims = list(state.claims.values())

    status_order = {
        ClaimStatus.CONTRADICTED: 0,
        ClaimStatus.TOO_BROAD: 1,
        ClaimStatus.UNCERTAIN: 2,
        ClaimStatus.NOT_FOUND: 3,
        ClaimStatus.NOT_VERIFIABLE: 4,
        ClaimStatus.SUPPORTED: 5,
    }
    return sorted(claims, key=lambda claim: status_order[claim.status])


def render_claim_detail(
    state: SessionState,
    claim: Any,
    config: PlumbrefConfig,
    rendered_excerpt_ids: set[str],
) -> list[str]:
    lines = [
        "",
        f"### {claim.status.value}: {redact_text(claim.text, config.privacy_patterns)}",
        f"- Type: {claim.claim_type.value}",
        f"- Risk: {claim.risk.value}",
    ]
    if claim.expected_outcome:
        lines.append(f"- Predicted outcome: {redact_text(claim.expected_outcome, config.privacy_patterns)}")
    if claim.assumptions:
        assumptions = "; ".join(redact_text(assumption, config.privacy_patterns) for assumption in claim.assumptions)
        lines.append(f"- Assumptions: {assumptions}")
    judgment = state.judgments.get(claim.id)
    if judgment:
        lines.append(
            f"- Reasoning: {redact_text(judgment.reasoning_summary, config.privacy_patterns) or 'Not provided.'}"
        )
        lines.append(f"- Limits: {redact_text(judgment.limits, config.privacy_patterns) or 'Not provided.'}")
        lines.append(f"- Contradiction pass: {'yes' if judgment.contradiction_searched else 'no'}")
    evidence_for_claim = [
        snippet for snippet in state.evidence.values() if snippet.claim_id == claim.id or claim.id in snippet.claim_ids
    ]
    if evidence_for_claim:
        lines.append("- Evidence:")
        for snippet in evidence_for_claim:
            location = f"{snippet.file}:{snippet.start_line}-{snippet.end_line}"
            summary = redact_text(snippet.summary, config.privacy_patterns) or "Evidence snippet recorded."
            category = f" [{snippet.evidence_category}]" if snippet.evidence_category else ""
            cache = " cache_hit" if snippet.cache_hit else ""
            reused = " reused" if len(snippet.claim_ids) > 1 else ""
            lines.append(f"  - `{location}`{category}{cache}{reused}: {summary}")
            if snippet.excerpt_returned and snippet.id not in rendered_excerpt_ids:
                lines.extend(format_excerpt(snippet.excerpt))
                rendered_excerpt_ids.add(snippet.id)
            elif snippet.id in rendered_excerpt_ids:
                lines.append("    - Excerpt already shown for this reused evidence reference.")
            else:
                lines.append(
                    "    - Excerpt not shown because this cached evidence reference did not return source text."
                )
    return lines


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


def answer_under_review(state: SessionState, config: PlumbrefConfig) -> list[str]:
    answer = redact_text(state.session.answer, config.privacy_patterns).strip()
    if not answer:
        return ["No answer text was provided for review."]
    return [answer]


def build_inline_answer(
    state: SessionState,
    config: PlumbrefConfig,
    payload: dict[str, Any] | None = None,
) -> str:
    """Build the chat-shaped answer an MCP agent can return directly."""
    report = payload or build_json_report(state, config)
    quality = report["quality"]
    measurement = report["measurement"]
    answer_gate = quality["answer_gate"]
    safe_answer = quality["safe_answer"]

    lines = [inline_answer_opening(answer_gate)]
    supported_lines = inline_supported_lines(safe_answer["supported"], config)
    if supported_lines:
        lines.extend(["", "What Plumbref checked:", *supported_lines])

    limit_lines = inline_limit_lines(state, safe_answer, config)
    if limit_lines:
        lines.extend(["", "Important limits:", *limit_lines])

    evidence_lines = inline_evidence_lines(state, config)
    if evidence_lines:
        lines.extend(["", "Evidence checked:", *evidence_lines])

    lines.extend(["", f"Verification: {inline_measurement_summary(state, measurement)}"])

    return "\n".join(lines).strip() + "\n"


def inline_answer_opening(answer_gate: dict[str, Any]) -> str:
    status = answer_gate["status"]
    if status == "safe_to_answer":
        return "Based on checked evidence, this answer is supported."
    if status == "answer_with_qualifications":
        return "Based on checked evidence, answer with these qualifications."
    if status == "answer_with_limits":
        return "Based on checked evidence, answer with these limits."
    if status == "do_not_claim":
        return "Plumbref found source evidence against the answer as written."
    return "Plumbref does not have enough checked evidence to answer yet."


def inline_supported_lines(items: list[dict[str, Any]], config: PlumbrefConfig) -> list[str]:
    lines = [f"- {inline_supported_text(item, config)}" for item in items[:4]]
    if len(items) > 4:
        lines.append(f"- {len(items) - 4} more supported claim(s) in the report.")
    return lines


def inline_supported_text(item: dict[str, Any], config: PlumbrefConfig) -> str:
    text = redact_text(item["text"], config.privacy_patterns)
    text = shorten_inline_claim(text)
    return ensure_sentence(truncate_words(text, 220))


def shorten_inline_claim(text: str) -> str:
    for separator in (
        ":",
        ";",
        ", and passes",
        " and passes",
        ", and the checked frontend test",
        " and the checked frontend test",
        ", and tests",
        " and tests",
    ):
        prefix, found, _rest = text.partition(separator)
        if found and 30 <= len(prefix) <= 210:
            return prefix
    return text


def inline_limit_lines(
    state: SessionState,
    safe_answer: dict[str, Any],
    config: PlumbrefConfig,
) -> list[str]:
    limits: list[tuple[int, str]] = []
    for item in [*safe_answer["qualified"], *safe_answer["avoid"]]:
        if item["limits"]:
            limits.append((-100, qualified_inline_limit_text(item)))
        else:
            limits.append((-100, f"{item['status']}: {item['text']}"))

    if not limits:
        for claim in state.claims.values():
            judgment = state.judgments.get(claim.id)
            if not judgment or not judgment.limits.strip():
                continue
            if claim.status != ClaimStatus.SUPPORTED:
                continue
            if not is_material_supported_limit(judgment.limits):
                continue
            limits.append((inline_limit_priority(claim, judgment.limits), judgment.limits))

    ordered_limits = [limit for _priority, limit in sorted(limits, key=lambda item: item[0])]
    deduped = dedupe_preserve_order(
        [redact_text(limit, config.privacy_patterns) for limit in ordered_limits if limit.strip()]
    )
    lines = [f"- {ensure_sentence(limit)}" for limit in deduped[:4]]
    if len(deduped) > 4:
        lines.append(f"- {len(deduped) - 4} more limit(s) in the report.")
    return lines


def inline_limit_priority(claim: Any, limit: str) -> int:
    normalized = normalize_check_text(limit)
    priority = 50
    if claim.status != ClaimStatus.SUPPORTED:
        priority -= 100
    if claim.risk == RiskLevel.HIGH:
        priority -= 20
    if "idempotency" in normalized or "server side" in normalized or "server side duplicate" in normalized:
        priority -= 15
    if "not found" in normalized or "did not find" in normalized or "no focused" in normalized:
        priority -= 12
    if "no browser" in normalized or "not execute" in normalized:
        priority -= 5
    return priority


def qualified_inline_limit_text(item: dict[str, Any]) -> str:
    text = item["text"].strip()
    limits = item["limits"].strip()
    if not text:
        return limits
    if not limits:
        return f"{item['status']}: {text}"
    return f"{item['status']}: {text} Limits: {limits}"


def is_material_supported_limit(limit: str) -> bool:
    normalized = normalize_check_text(limit)
    if not normalized:
        return False
    return normalized not in {"not provided", "none", "n a", "not applicable"}


def inline_evidence_lines(state: SessionState, config: PlumbrefConfig) -> list[str]:
    claims = list(state.claims.values())
    priority = [
        ClaimStatus.CONTRADICTED,
        ClaimStatus.TOO_BROAD,
        ClaimStatus.UNCERTAIN,
        ClaimStatus.NOT_FOUND,
        ClaimStatus.NOT_VERIFIABLE,
        ClaimStatus.SUPPORTED,
    ]
    claims.sort(key=lambda claim: priority.index(claim.status))

    evidence_by_id = state.evidence
    locations: list[str] = []
    for claim in claims:
        judgment = state.judgments.get(claim.id)
        if not judgment:
            continue
        for evidence_id in judgment.evidence_ids:
            snippet = evidence_by_id.get(evidence_id)
            if not snippet:
                continue
            location = f"{snippet.file}:{snippet.start_line}-{snippet.end_line}"
            locations.append(redact_text(location, config.privacy_patterns))

    return [f"- `{location}`" for location in dedupe_preserve_order(locations)[:4]]


def inline_measurement_summary(state: SessionState, measurement: dict[str, Any]) -> str:
    status_counts = measurement["claim_status_counts"]
    status_text = ", ".join(f"{status}={count}" for status, count in status_counts.items()) or "no claims"
    evidence_count = len(state.evidence)
    return (
        f"{measurement['claims_total']} claim(s) ({status_text}); "
        f"{evidence_count} evidence snippet(s); "
        f"{measurement['contradiction_passes']}/{measurement['judged_claims']} contradiction pass(es)."
    )


def user_answer(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if state.session.mode == VerificationMode.SCENARIO:
        return scenario_user_answer(state, config)
    if state.session.mode == VerificationMode.CHANGE_IMPACT:
        return change_impact_user_answer(state, config)
    return explanation_user_answer(state, config)


def explanation_user_answer(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if not state.claims:
        return ["No source-backed answer is available yet."]

    return natural_answer_lines(
        state,
        config,
        supported_prefix="Based on the checked evidence:",
        qualified_prefix="Important qualification:",
        avoid_prefix="Do not claim:",
        no_supported="Plumbref did not find a source-backed answer yet.",
    )


def change_impact_user_answer(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if not state.claims:
        return ["No source-backed impact answer is available yet."]

    return natural_answer_lines(
        state,
        config,
        supported_prefix="Based on the checked evidence, the impact is:",
        qualified_prefix="Important qualification:",
        avoid_prefix="Do not describe the impact this way:",
        no_supported="Plumbref did not find enough source-backed evidence to state the impact yet.",
    )


def scenario_user_answer(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if not state.claims:
        return ["No source-backed scenario conclusion is available yet."]

    return natural_answer_lines(
        state,
        config,
        supported_prefix="Based on the checked evidence, the expected outcome is:",
        qualified_prefix="Important qualification:",
        avoid_prefix="Do not rely on this outcome:",
        no_supported="Plumbref did not find enough source-backed evidence to state the scenario outcome yet.",
    )


def natural_answer_lines(
    state: SessionState,
    config: PlumbrefConfig,
    *,
    supported_prefix: str,
    qualified_prefix: str,
    avoid_prefix: str,
    no_supported: str,
) -> list[str]:
    safe_answer = build_safe_answer_summary(state)
    supported = safe_answer["supported"]
    qualified = safe_answer["qualified"]
    avoid = safe_answer["avoid"]
    lines: list[str] = []

    if supported:
        lines.extend(format_answer_group(supported_prefix, supported, config))
    else:
        lines.append(no_supported)

    if qualified:
        lines.extend(format_qualified_answer_group(qualified_prefix, qualified, config))
    if avoid:
        lines.extend(format_qualified_answer_group(avoid_prefix, avoid, config))
    return lines


def format_answer_group(
    prefix: str,
    items: list[dict[str, Any]],
    config: PlumbrefConfig,
) -> list[str]:
    if len(items) == 1:
        text = redact_text(items[0]["text"], config.privacy_patterns)
        return [f"{prefix} {ensure_sentence(text)}"]

    lines = [prefix]
    for item in items[:6]:
        text = redact_text(item["text"], config.privacy_patterns)
        lines.append(f"- {ensure_sentence(text)}")
    if len(items) > 6:
        lines.append(f"- Additional supported claims omitted: {len(items) - 6}")
    return lines


def format_qualified_answer_group(
    prefix: str,
    items: list[dict[str, Any]],
    config: PlumbrefConfig,
) -> list[str]:
    if len(items) == 1:
        return [f"{prefix} {qualified_answer_sentence(items[0], config)}"]

    lines = [prefix]
    for item in items[:4]:
        lines.append(f"- {qualified_answer_sentence(item, config)}")
    if len(items) > 4:
        lines.append(f"- Additional qualified claims omitted: {len(items) - 4}")
    return lines


def qualified_answer_sentence(item: dict[str, Any], config: PlumbrefConfig) -> str:
    limits = redact_text(item["limits"], config.privacy_patterns)
    if limits:
        return ensure_sentence(limits)
    text = redact_text(item["text"], config.privacy_patterns)
    return ensure_sentence(f"{item['status']}: {text}")


def ensure_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped[-1] in ".!?":
        return stripped
    return f"{stripped}."


def truncate_words(text: str, max_chars: int) -> str:
    stripped = text.strip()
    if len(stripped) <= max_chars:
        return stripped
    words = stripped.split()
    shortened: list[str] = []
    for word in words:
        candidate = " ".join([*shortened, word])
        if len(candidate) > max_chars - 1:
            break
        shortened.append(word)
    return (" ".join(shortened) or stripped[: max_chars - 1]).rstrip(" ,;:") + "..."


def explanation_safe_answer(state: SessionState, config: PlumbrefConfig) -> list[str]:
    if not state.claims:
        return ["No verified claims are available yet."]

    safe_answer = build_safe_answer_summary(state)
    lines: list[str] = []
    supported = safe_answer["supported"]
    qualified = safe_answer["qualified"]
    avoid = safe_answer["avoid"]
    if supported:
        lines.append("Source-supported:")
        for item in supported:
            lines.append(f"- {redact_text(item['text'], config.privacy_patterns)}")
    if qualified:
        if lines:
            lines.append("")
        lines.append("Needs qualification:")
        for item in qualified:
            limits = redact_text(item["limits"], config.privacy_patterns)
            suffix = f" Limits: {limits}" if limits else ""
            lines.append(f"- {item['status']}: {redact_text(item['text'], config.privacy_patterns)}{suffix}")
    if avoid:
        if lines:
            lines.append("")
        lines.append("Avoid claiming:")
        for item in avoid:
            limits = redact_text(item["limits"], config.privacy_patterns)
            suffix = f" Limits: {limits}" if limits else ""
            lines.append(f"- {item['status']}: {redact_text(item['text'], config.privacy_patterns)}{suffix}")
    return lines or ["No supported wording is available yet."]


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
            lines.append(f"  - `{redact_text(location, config.privacy_patterns)}` {symbol_kind} `{symbol_name}`")
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
    fence = markdown_code_fence(excerpt)
    return ["", f"    {fence}text", *[f"    {line}" for line in excerpt.splitlines()], f"    {fence}"]


def markdown_code_fence(text: str) -> str:
    longest_run = 0
    current_run = 0
    for character in text:
        if character == "`":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    return "`" * max(3, longest_run + 1)
