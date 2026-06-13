from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from plumbref.cli import app
from plumbref.report_diff import build_report_diff, compare_reports, render_report_diff


def test_report_diff_renders_status_evidence_added_and_removed_changes(tmp_path: Path) -> None:
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    old_path.write_text(json.dumps(old_report()), encoding="utf-8")
    new_path.write_text(json.dumps(new_report()), encoding="utf-8")

    markdown = render_report_diff(old_path, new_path)

    assert "# Plumbref Report Diff" in markdown
    assert "Question: How does SSO eligibility work?" in markdown
    assert "- Claims compared: 4" in markdown
    assert "- Status changes: 1" in markdown
    assert "- Evidence drift: 1" in markdown
    assert "- Location-only drift: 0" in markdown
    assert "- Added claims: 1" in markdown
    assert "- Removed claims: 1" in markdown
    assert "## Status Changes" in markdown
    assert "## New Claims" in markdown
    assert "## Removed Claims" in markdown
    assert "## Evidence Drift" in markdown
    assert "### `claim-001`" in markdown
    assert "- Status: `supported` -> `contradicted`" in markdown
    assert "### `claim-002`" in markdown
    assert "- Status unchanged: `supported`" in markdown
    assert "- Evidence: changed" in markdown
    assert "### `claim-003`" in markdown
    assert "- Status: removed" in markdown
    assert "### `claim-004`" in markdown
    assert "- Status: added" in markdown

    result = build_report_diff(old_path, new_path)
    response = result.to_response()
    assert response["summary"]["status_changes"] == 1
    assert response["summary"]["evidence_drift"] == 1
    assert response["summary"]["evidence_only_changes"] == 1
    assert response["summary"]["location_only_drift"] == 0
    assert response["summary"]["added_claims"] == 1
    assert response["summary"]["removed_claims"] == 1
    assert response["changes"][0]["stable_id"] == "claim-001"
    assert response["changes"][0]["change_type"] == "status_and_evidence_changed"
    assert response["changes"][0]["old"]["status"] == "supported"
    assert response["changes"][0]["new"]["status"] == "contradicted"


def test_report_diff_demotes_line_range_only_drift(tmp_path: Path) -> None:
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    old = old_report()
    new = old_report()
    new["evidence"][0]["start_line"] = 20
    new["evidence"][0]["end_line"] = 30
    old_path.write_text(json.dumps(old), encoding="utf-8")
    new_path.write_text(json.dumps(new), encoding="utf-8")

    response = build_report_diff(old_path, new_path).to_response()

    assert response["summary"]["changed_claims"] == 0
    assert response["summary"]["evidence_drift"] == 0
    assert response["summary"]["location_only_drift"] == 1
    assert response["changes"][0]["change_type"] == "location_only_drift"
    assert "## Location-Only Drift" in response["markdown"]
    assert "- Evidence: location changed only" in response["markdown"]


def test_report_diff_falls_back_to_order_ids_for_older_reports() -> None:
    old = old_report()
    new = new_report()
    for report in (old, new):
        for claim in report["claims"]:
            claim.pop("stable_id", None)

    diffs = compare_reports(old, new)

    assert [diff.stable_id for diff in diffs] == ["claim-001", "claim-002", "claim-003"]


def test_diff_reports_cli_writes_markdown_output(tmp_path: Path) -> None:
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    output_path = tmp_path / "diff.md"
    old_path.write_text(json.dumps(old_report()), encoding="utf-8")
    new_path.write_text(json.dumps(new_report()), encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "diff-reports",
            str(old_path),
            str(new_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Wrote report diff:" in result.output
    assert output_path.is_file()
    assert "supported` -> `contradicted" in output_path.read_text(encoding="utf-8")


def old_report() -> dict[str, object]:
    return {
        "question": "How does SSO eligibility work?",
        "template": {"id": "explain_flow", "name": "Explain Flow"},
        "claims": [
            claim("claim-001", "SSO starts only when a provider is configured.", "supported", ["ev-1"]),
            claim("claim-002", "The callback validates the provider response.", "supported", ["ev-2"]),
            claim("claim-003", "Legacy fallback is still accepted.", "supported", ["ev-3"]),
        ],
        "evidence": [
            evidence("ev-1", "claim-uuid-claim-001", "auth/sso.py", 10, 20, "aaa111"),
            evidence("ev-2", "claim-uuid-claim-002", "auth/callback.py", 30, 44, "bbb222"),
            evidence("ev-3", "claim-uuid-claim-003", "auth/legacy.py", 5, 12, "ccc333"),
        ],
    }


def new_report() -> dict[str, object]:
    return {
        "question": "How does SSO eligibility work?",
        "template": {"id": "explain_flow", "name": "Explain Flow"},
        "claims": [
            claim("claim-001", "SSO starts only when a provider is configured.", "contradicted", ["ev-1-new"]),
            claim("claim-002", "The callback validates the provider response.", "supported", ["ev-2-new"]),
            claim("claim-004", "The login button hides when SSO is unavailable.", "supported", ["ev-4"]),
        ],
        "evidence": [
            evidence("ev-1-new", "claim-uuid-claim-001", "auth/sso.py", 10, 22, "ddd444"),
            evidence("ev-2-new", "claim-uuid-claim-002", "auth/callback.py", 31, 44, "eee555"),
            evidence("ev-4", "claim-uuid-claim-004", "frontend/login.tsx", 50, 58, "fff666"),
        ],
    }


def claim(stable_id: str, text: str, status: str, evidence_ids: list[str]) -> dict[str, object]:
    return {
        "id": f"claim-uuid-{stable_id}",
        "stable_id": stable_id,
        "text": text,
        "status": status,
        "claim_type": "business_rule",
        "judgment": {
            "status": status,
            "evidence_ids": evidence_ids,
            "limits": "",
            "contradiction_searched": status == "supported",
        },
    }


def evidence(
    evidence_id: str,
    claim_id: str,
    file: str,
    start_line: int,
    end_line: int,
    sha256: str,
) -> dict[str, object]:
    return {
        "id": evidence_id,
        "claim_id": claim_id,
        "claim_ids": [claim_id],
        "file": file,
        "start_line": start_line,
        "end_line": end_line,
        "sha256": sha256,
        "excerpt": "",
    }
