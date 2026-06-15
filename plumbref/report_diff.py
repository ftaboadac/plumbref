from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ReportDiffError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceRef:
    file: str
    start_line: int | None
    end_line: int | None
    sha256: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> EvidenceRef:
        return cls(
            file=str(payload.get("file") or "unknown"),
            start_line=payload.get("start_line") if isinstance(payload.get("start_line"), int) else None,
            end_line=payload.get("end_line") if isinstance(payload.get("end_line"), int) else None,
            sha256=str(payload.get("sha256") or ""),
        )

    def label(self) -> str:
        location = self.file
        if self.start_line is not None and self.end_line is not None:
            location = f"{location}:{self.start_line}-{self.end_line}"
        suffix = f" `{self.sha256[:8]}`" if self.sha256 else ""
        return f"`{location}`{suffix}"

    def content_key(self) -> tuple[str, str]:
        return (self.file, self.sha256)


@dataclass(frozen=True)
class ClaimSnapshot:
    stable_id: str
    claim_id: str
    text: str
    status: str
    claim_type: str
    evidence: tuple[EvidenceRef, ...]
    limits: str
    safer_wording: str
    contradiction_searched: bool


@dataclass(frozen=True)
class ClaimDiff:
    stable_id: str
    old: ClaimSnapshot | None
    new: ClaimSnapshot | None

    @property
    def status_changed(self) -> bool:
        return self.old is not None and self.new is not None and self.old.status != self.new.status

    @property
    def evidence_changed(self) -> bool:
        return self.old is not None and self.new is not None and set(self.old.evidence) != set(self.new.evidence)

    @property
    def location_only_drift(self) -> bool:
        if self.old is None or self.new is None or not self.evidence_changed:
            return False
        return evidence_content_keys(self.old.evidence) == evidence_content_keys(self.new.evidence)

    @property
    def material_evidence_changed(self) -> bool:
        return self.evidence_changed and not self.location_only_drift

    @property
    def added(self) -> bool:
        return self.old is None and self.new is not None

    @property
    def removed(self) -> bool:
        return self.old is not None and self.new is None

    @property
    def changed(self) -> bool:
        return self.status_changed or self.evidence_changed or self.added or self.removed


@dataclass(frozen=True)
class ReportDiffResult:
    old_report: dict[str, Any]
    new_report: dict[str, Any]
    old_path: Path
    new_path: Path
    diffs: list[ClaimDiff]
    markdown: str

    def summary(self) -> dict[str, Any]:
        return diff_summary(self.diffs)

    def changes(self) -> list[dict[str, Any]]:
        return [serialize_claim_diff(diff) for diff in self.diffs if diff.changed]

    def to_response(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "changes": self.changes(),
            "markdown": self.markdown,
            "old_report_path": str(self.old_path),
            "new_report_path": str(self.new_path),
        }


def load_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReportDiffError(f"could not read report {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ReportDiffError(f"{path} is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ReportDiffError(f"{path} does not contain a JSON object")
    if not isinstance(payload.get("claims"), list):
        raise ReportDiffError(f"{path} does not look like a Plumbref JSON report: missing claims list")
    return payload


def render_report_diff(old_path: Path, new_path: Path) -> str:
    return build_report_diff(old_path, new_path).markdown


def build_report_diff(old_path: Path, new_path: Path) -> ReportDiffResult:
    old_report = load_report(old_path)
    new_report = load_report(new_path)
    diffs = compare_reports(old_report, new_report)
    markdown = render_diff_markdown(
        old_report=old_report,
        new_report=new_report,
        old_path=old_path,
        new_path=new_path,
        diffs=diffs,
    )
    return ReportDiffResult(
        old_report=old_report,
        new_report=new_report,
        old_path=old_path,
        new_path=new_path,
        diffs=diffs,
        markdown=markdown,
    )


def compare_reports(old_report: dict[str, Any], new_report: dict[str, Any]) -> list[ClaimDiff]:
    old_claims = claim_snapshots(old_report)
    new_claims = claim_snapshots(new_report)
    stable_ids = sorted({*old_claims, *new_claims}, key=claim_sort_key)
    return [
        ClaimDiff(
            stable_id=stable_id,
            old=old_claims.get(stable_id),
            new=new_claims.get(stable_id),
        )
        for stable_id in stable_ids
    ]


def claim_snapshots(report: dict[str, Any]) -> dict[str, ClaimSnapshot]:
    evidence_by_id = {
        str(item.get("id")): item for item in report.get("evidence", []) if isinstance(item, dict) and item.get("id")
    }
    snapshots: dict[str, ClaimSnapshot] = {}
    for index, claim in enumerate(report.get("claims", []), start=1):
        if not isinstance(claim, dict):
            continue
        stable_id = str(claim.get("stable_id") or f"claim-{index:03d}")
        claim_id = str(claim.get("id") or "")
        judgment = claim.get("judgment") if isinstance(claim.get("judgment"), dict) else {}
        evidence_ids = [str(value) for value in judgment.get("evidence_ids", []) if value]
        evidence = evidence_for_claim(
            claim_id=claim_id,
            evidence_ids=evidence_ids,
            evidence_by_id=evidence_by_id,
            report_evidence=report.get("evidence", []),
        )
        snapshots[stable_id] = ClaimSnapshot(
            stable_id=stable_id,
            claim_id=claim_id,
            text=str(claim.get("text") or ""),
            status=str(claim.get("status") or judgment.get("status") or "unknown"),
            claim_type=str(claim.get("claim_type") or "unknown"),
            evidence=tuple(sorted(evidence, key=lambda item: item.label())),
            limits=str(judgment.get("limits") or ""),
            safer_wording=str(judgment.get("safer_wording") or ""),
            contradiction_searched=bool(judgment.get("contradiction_searched")),
        )
    return snapshots


def evidence_for_claim(
    *,
    claim_id: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
    report_evidence: Any,
) -> list[EvidenceRef]:
    refs = [
        EvidenceRef.from_payload(evidence_by_id[evidence_id])
        for evidence_id in evidence_ids
        if evidence_id in evidence_by_id
    ]
    if refs:
        return refs
    if not isinstance(report_evidence, list):
        return []
    matched: list[EvidenceRef] = []
    for item in report_evidence:
        if not isinstance(item, dict):
            continue
        claim_ids = [str(value) for value in item.get("claim_ids", [])]
        if item.get("claim_id") == claim_id or claim_id in claim_ids:
            matched.append(EvidenceRef.from_payload(item))
    return matched


def render_diff_markdown(
    *,
    old_report: dict[str, Any],
    new_report: dict[str, Any],
    old_path: Path,
    new_path: Path,
    diffs: list[ClaimDiff],
) -> str:
    summary = diff_summary(diffs)
    status_changes = [diff for diff in diffs if diff.status_changed]
    added = [diff for diff in diffs if diff.added]
    removed = [diff for diff in diffs if diff.removed]
    material_evidence_drift = [
        diff
        for diff in diffs
        if diff.material_evidence_changed and not diff.status_changed and not diff.added and not diff.removed
    ]
    location_drift = [
        diff
        for diff in diffs
        if diff.location_only_drift and not diff.status_changed and not diff.added and not diff.removed
    ]
    unchanged = [diff for diff in diffs if not diff.changed]
    lines = [
        "# Plumbref Report Diff",
        "",
        f"Question: {display_question(old_report, new_report)}",
        f"Summary: {headline_summary(diffs)}",
        f"Template: {display_template(old_report, new_report)}",
        f"Old report: `{old_path}`",
        f"New report: `{new_path}`",
        "",
        "## What Changed",
        summarize_changes_sentence(summary),
        "",
        f"- Claims compared: {summary['claims_compared']}",
        f"- Status changes: {summary['status_changes']}",
        f"- Evidence drift: {summary['evidence_drift']}",
        f"- Location-only drift: {summary['location_only_drift']}",
        f"- Added claims: {summary['added_claims']}",
        f"- Removed claims: {summary['removed_claims']}",
    ]
    if not any((status_changes, added, removed, material_evidence_drift, location_drift)):
        lines.append("- No claim status or evidence changes detected.")
    lines.extend(render_diff_section("Status Changes", status_changes))
    lines.extend(render_diff_section("New Claims", added))
    lines.extend(render_diff_section("Removed Claims", removed))
    lines.extend(render_diff_section("Evidence Drift", material_evidence_drift))
    lines.extend(render_diff_section("Location-Only Drift", location_drift))
    lines.extend(render_unchanged_claims(unchanged))
    return "\n".join(lines).strip() + "\n"


def diff_summary(diffs: list[ClaimDiff]) -> dict[str, Any]:
    status_changed = [diff for diff in diffs if diff.status_changed]
    material_evidence_changed = [diff for diff in diffs if diff.material_evidence_changed]
    evidence_drift = [diff for diff in material_evidence_changed if not diff.status_changed]
    location_only_drift = [diff for diff in diffs if diff.location_only_drift and not diff.status_changed]
    added = [diff for diff in diffs if diff.added]
    removed = [diff for diff in diffs if diff.removed]
    return {
        "claims_compared": len(diffs),
        "status_changes": len(status_changed),
        "evidence_drift": len(evidence_drift),
        "evidence_only_changes": len(evidence_drift),
        "location_only_drift": len(location_only_drift),
        "added_claims": len(added),
        "removed_claims": len(removed),
        "changed_claims": sum(
            1
            for diff in diffs
            if diff.status_changed or diff.material_evidence_changed or diff.added or diff.removed
        ),
    }


def serialize_claim_diff(diff: ClaimDiff) -> dict[str, Any]:
    before = serialize_claim_snapshot(diff.old)
    after = serialize_claim_snapshot(diff.new)
    return {
        "stable_id": diff.stable_id,
        "change_type": claim_diff_change_type(diff),
        "status_changed": diff.status_changed,
        "evidence_changed": diff.evidence_changed,
        "material_evidence_changed": diff.material_evidence_changed,
        "location_only_drift": diff.location_only_drift,
        "old": before,
        "new": after,
    }


def serialize_claim_snapshot(snapshot: ClaimSnapshot | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return {
        "stable_id": snapshot.stable_id,
        "claim_id": snapshot.claim_id,
        "text": snapshot.text,
        "status": snapshot.status,
        "claim_type": snapshot.claim_type,
        "limits": snapshot.limits,
        "safer_wording": snapshot.safer_wording,
        "contradiction_searched": snapshot.contradiction_searched,
        "evidence": [
            {
                "file": item.file,
                "start_line": item.start_line,
                "end_line": item.end_line,
                "sha256": item.sha256,
            }
            for item in snapshot.evidence
        ],
    }


def claim_diff_change_type(diff: ClaimDiff) -> str:
    if diff.added:
        return "added"
    if diff.removed:
        return "removed"
    if diff.status_changed and diff.material_evidence_changed:
        return "status_and_evidence_changed"
    if diff.status_changed:
        return "status_changed"
    if diff.material_evidence_changed:
        return "evidence_changed"
    if diff.location_only_drift:
        return "location_only_drift"
    return "unchanged"


def evidence_content_keys(evidence: tuple[EvidenceRef, ...]) -> set[tuple[str, str]]:
    return {item.content_key() for item in evidence}


def render_claim_diff(diff: ClaimDiff) -> list[str]:
    before = diff.old
    after = diff.new
    snapshot = after or before
    if snapshot is None:
        return []
    lines = ["", f"### `{diff.stable_id}`"]
    lines.append(f"- Claim: {snapshot.text}")
    if before and after:
        if diff.status_changed:
            lines.append(f"- Status: `{before.status}` -> `{after.status}`")
        else:
            lines.append(f"- Status unchanged: `{after.status}`")
        if diff.location_only_drift:
            lines.append("- Evidence: location changed only")
        else:
            lines.append(f"- Evidence: {'changed' if diff.evidence_changed else 'unchanged'}")
        if before.contradiction_searched != after.contradiction_searched:
            lines.append(
                "- Contradiction check: "
                f"`{format_bool(before.contradiction_searched)}` -> `{format_bool(after.contradiction_searched)}`"
            )
        if before.limits != after.limits:
            lines.append(f"- Limits changed: `{before.limits or 'none'}` -> `{after.limits or 'none'}`")
        if before.safer_wording != after.safer_wording:
            lines.append(
                "- Safer wording changed: "
                f"`{before.safer_wording or 'none'}` -> `{after.safer_wording or 'none'}`"
            )
        lines.extend(format_evidence_delta("Old evidence", before.evidence))
        lines.extend(format_evidence_delta("New evidence", after.evidence))
    elif after:
        lines.append("- Status: added")
        lines.append(f"- New status: `{after.status}`")
        lines.extend(format_evidence_delta("New evidence", after.evidence))
    elif before:
        lines.append("- Status: removed")
        lines.append(f"- Old status: `{before.status}`")
        lines.extend(format_evidence_delta("Old evidence", before.evidence))
    return lines


def render_diff_section(title: str, diffs: list[ClaimDiff]) -> list[str]:
    lines = ["", f"## {title}"]
    if not diffs:
        lines.append("None.")
        return lines
    for diff in diffs:
        lines.extend(render_claim_diff(diff))
    return lines


def render_unchanged_claims(diffs: list[ClaimDiff]) -> list[str]:
    lines = ["", "## Unchanged Claims"]
    if not diffs:
        lines.append("None.")
        return lines
    for diff in diffs:
        snapshot = diff.new or diff.old
        if snapshot:
            lines.append(f"- `{diff.stable_id}` {snapshot.status}: {snapshot.text}")
    return lines


def summarize_changes_sentence(summary: dict[str, Any]) -> str:
    parts: list[str] = []
    if summary["status_changes"]:
        parts.append(pluralize(summary["status_changes"], "claim changed status", "claims changed status"))
    if summary["added_claims"]:
        parts.append(pluralize(summary["added_claims"], "new claim appeared", "new claims appeared"))
    if summary["removed_claims"]:
        parts.append(pluralize(summary["removed_claims"], "claim was removed", "claims were removed"))
    if summary["evidence_drift"]:
        parts.append(pluralize(summary["evidence_drift"], "claim changed evidence", "claims changed evidence"))
    if not parts:
        return "No material claim changes were detected."
    sentence = ", ".join(parts)
    return sentence[0].upper() + sentence[1:] + "."


def headline_summary(diffs: list[ClaimDiff]) -> str:
    summary = diff_summary(diffs)
    status_changes = [diff for diff in diffs if diff.status_changed]
    if status_changes:
        primary = status_changes[0]
        if primary.old and primary.new:
            details = (
                f"`{primary.old.text}` changed from `{primary.old.status}` "
                f"to `{primary.new.status}`"
            )
            updated_wording = primary.new.safer_wording or primary.new.limits
            if updated_wording:
                details += f"; updated wording: {updated_wording.rstrip('.')}"
            if len(status_changes) > 1:
                details += f" ({len(status_changes) - 1} more status change(s))."
            else:
                details += "."
            return details
    return summarize_changes_sentence(summary)


def pluralize(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def format_evidence_delta(label: str, evidence: tuple[EvidenceRef, ...]) -> list[str]:
    if not evidence:
        return [f"- {label}: none"]
    joined = ", ".join(item.label() for item in evidence[:6])
    suffix = f" and {len(evidence) - 6} more" if len(evidence) > 6 else ""
    return [f"- {label}: {joined}{suffix}"]


def display_question(old_report: dict[str, Any], new_report: dict[str, Any]) -> str:
    return str(new_report.get("question") or old_report.get("question") or "(question unavailable)")


def display_template(old_report: dict[str, Any], new_report: dict[str, Any]) -> str:
    template = new_report.get("template") or old_report.get("template")
    if isinstance(template, dict):
        template_id = template.get("id")
        template_name = template.get("name")
        if template_id and template_name:
            return f"{template_name} (`{template_id}`)"
        if template_id:
            return str(template_id)
    return "(template unavailable)"


def claim_sort_key(stable_id: str) -> tuple[str, int | str]:
    prefix, separator, suffix = stable_id.rpartition("-")
    if separator and suffix.isdigit():
        return (prefix, int(suffix))
    return (stable_id, stable_id)


def format_bool(value: bool) -> str:
    return "yes" if value else "no"
