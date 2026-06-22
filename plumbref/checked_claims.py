from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class CheckedClaimError(ValueError):
    pass


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CheckedClaimError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CheckedClaimError(f"{path} is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise CheckedClaimError(f"{path} must contain a JSON object")
    return payload


def export_checked_claims(report_path: Path, out_dir: Path) -> list[Path]:
    report = load_json_object(report_path)
    if not isinstance(report.get("claims"), list):
        raise CheckedClaimError(f"{report_path} does not look like a Plumbref JSON report")
    claims = checked_claims_from_report(report, source_report_path=report_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for claim in claims:
        path = out_dir / f"{safe_claim_filename(claim['claim_id'], claim['claim_text'])}.json"
        path.write_text(json.dumps(claim, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def checked_claims_from_report(
    report: dict[str, Any],
    *,
    source_report_path: Path | None = None,
) -> list[dict[str, Any]]:
    evidence_by_id = {
        str(item.get("id")): item for item in report.get("evidence", []) if isinstance(item, dict) and item.get("id")
    }
    quality = report.get("quality") if isinstance(report.get("quality"), dict) else {}
    gate = quality.get("answer_gate") if isinstance(quality.get("answer_gate"), dict) else {}
    gate_coverage = quality.get("gate_coverage") if isinstance(quality.get("gate_coverage"), dict) else {}
    missing_by_claim = (
        gate_coverage.get("missing_by_claim")
        if isinstance(gate_coverage.get("missing_by_claim"), dict)
        else {}
    )
    report_identity = report.get("report_identity") if isinstance(report.get("report_identity"), dict) else {}
    template = report.get("template") if isinstance(report.get("template"), dict) else {}
    exported: list[dict[str, Any]] = []
    for index, claim in enumerate(report.get("claims", []), start=1):
        if not isinstance(claim, dict):
            continue
        source_claim_id = str(claim.get("id") or "")
        stable_id = str(claim.get("stable_id") or f"claim-{index:03d}")
        judgment = claim.get("judgment") if isinstance(claim.get("judgment"), dict) else {}
        evidence_ids = [str(value) for value in judgment.get("evidence_ids", []) if value]
        traces = [
            trace
            for trace in report.get("trace", [])
            if isinstance(trace, dict) and str(trace.get("claim_id") or "") == source_claim_id
        ]
        template_values = report.get("template_values") if isinstance(report.get("template_values"), dict) else {}
        absolute_language = claim.get("absolute_language") if isinstance(claim.get("absolute_language"), list) else []
        evidence = [
            evidence_ref(evidence_by_id[evidence_id])
            for evidence_id in evidence_ids
            if evidence_id in evidence_by_id
        ]
        exported.append(
            {
                "schema_version": "1",
                "claim_id": stable_id,
                "source_claim_id": source_claim_id,
                "claim_text": str(claim.get("text") or ""),
                "question": str(report.get("question") or ""),
                "source_report_path": str(source_report_path) if source_report_path else "",
                "repo_identity": report_identity.get("repo_identifier"),
                "repo_state": report_identity.get("repo_state"),
                "report_identity": report_identity.get("id"),
                "mode": str(report.get("mode") or ""),
                "template_id": template.get("id"),
                "template_values": template_values,
                "status": str(claim.get("status") or judgment.get("status") or "unknown"),
                "gate_status": str(gate.get("status") or "unknown"),
                "gate_summary": str(gate.get("summary") or ""),
                "claim_type": str(claim.get("claim_type") or "unknown"),
                "risk": str(claim.get("risk") or "unknown"),
                "absolute_language": absolute_language,
                "evidence": evidence,
                "searches": [search_ref(trace) for trace in traces],
                "missing_checks": [str(item) for item in missing_by_claim.get(source_claim_id, [])],
                "limits": str(judgment.get("limits") or ""),
                "safer_wording": str(judgment.get("safer_wording") or ""),
                "contradiction_searched": bool(judgment.get("contradiction_searched")),
                "created_at": str(report.get("created_at") or ""),
            }
        )
    return exported


def evidence_ref(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "file": payload.get("file"),
        "start_line": payload.get("start_line"),
        "end_line": payload.get("end_line"),
        "sha256": payload.get("sha256"),
        "summary": payload.get("summary") or "",
        "evidence_category": payload.get("evidence_category"),
    }


def search_ref(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": payload.get("query"),
        "matched_files": payload.get("matched_files") if isinstance(payload.get("matched_files"), list) else [],
        "budget_exhausted": bool(payload.get("budget_exhausted")),
        "truncated": bool(payload.get("truncated")),
    }


def safe_claim_filename(claim_id: str, claim_text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", claim_text.lower()).strip("-")[:48]
    return f"{claim_id}-{slug or 'claim'}"


def render_checked_claim_diff(old_path: Path, new_path: Path) -> str:
    old = load_json_object(old_path)
    new = load_json_object(new_path)
    return render_claim_diff_markdown(old, new, old_path=old_path, new_path=new_path)


def render_claim_diff_markdown(
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    old_path: Path,
    new_path: Path,
) -> str:
    changes: list[str] = []
    for label, key in (
        ("Status", "status"),
        ("Gate", "gate_status"),
        ("Limits", "limits"),
        ("Safer wording", "safer_wording"),
    ):
        if old.get(key) != new.get(key):
            changes.append(f"- {label}: `{old.get(key) or ''}` -> `{new.get(key) or ''}`")
    old_evidence = evidence_labels(old.get("evidence"))
    new_evidence = evidence_labels(new.get("evidence"))
    if old_evidence != new_evidence:
        changes.append(
            f"- Evidence changed: {len(old_evidence)} old reference(s), "
            f"{len(new_evidence)} new reference(s)"
        )
    old_missing = [str(item) for item in old.get("missing_checks", []) if item]
    new_missing = [str(item) for item in new.get("missing_checks", []) if item]
    if old_missing != new_missing:
        changes.append(f"- Missing checks changed: {len(old_missing)} old, {len(new_missing)} new")
    if not changes:
        changes.append("- No status, evidence, limit, or missing-check changes detected.")
    lines = [
        "# Plumbref Checked Claim Diff",
        "",
        f"Claim: {new.get('claim_text') or old.get('claim_text') or 'unknown'}",
        f"Old claim: `{old_path}`",
        f"New claim: `{new_path}`",
        "",
        "## What Changed",
        *changes,
    ]
    return "\n".join(lines).strip() + "\n"


def evidence_labels(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    labels: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        labels.add(f"{item.get('file')}:{item.get('start_line')}-{item.get('end_line')}:{item.get('sha256')}")
    return labels


def render_rerun_packet(claim_path: Path) -> str:
    claim = load_json_object(claim_path)
    lines = [
        "# Plumbref Claim Rerun Packet",
        "",
        "Use this packet to rerun the checked claim against the current repo state.",
        "",
        f"Claim ID: `{claim.get('claim_id')}`",
        f"Claim: {claim.get('claim_text')}",
        f"Original status: `{claim.get('status')}`",
        f"Original gate: `{claim.get('gate_status')}`",
        f"Template: `{claim.get('template_id') or 'none'}`",
        "",
        "## Rerun Instructions",
        "",
        "1. Start a new Plumbref session with the claim text as the answer under review.",
        "2. Use the same template and template values when applicable.",
        "3. Search the current repo for the claim, contradiction paths, and required evidence categories.",
        "4. Record a new judgment and render a new report.",
        "5. Export the new report with `plumbref export-claims`.",
        "6. Compare old and new artifacts with `plumbref diff-claims`.",
    ]
    missing_checks = [str(item) for item in claim.get("missing_checks", []) if item]
    if missing_checks:
        lines.extend(["", "## Original Missing Checks", *[f"- {item}" for item in missing_checks]])
    return "\n".join(lines).strip() + "\n"
