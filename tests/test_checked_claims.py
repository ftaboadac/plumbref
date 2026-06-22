from __future__ import annotations

import json
from pathlib import Path

from plumbref.checked_claims import export_checked_claims, render_checked_claim_diff, render_rerun_packet
from plumbref.claim_checks import render_claim_check


def test_export_checked_claims_writes_claim_artifacts(tmp_path: Path) -> None:
    """Checked claims can be exported from a Plumbref JSON report."""
    report = tmp_path / "report.json"
    report.write_text(json.dumps(sample_report()), encoding="utf-8")

    written = export_checked_claims(report, tmp_path / "claims")

    assert len(written) == 1
    payload = json.loads(written[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1"
    assert payload["claim_id"] == "claim-001"
    assert payload["claim_text"] == "This PR only changes docs."
    assert payload["gate_status"] == "answer_with_qualifications"
    assert payload["missing_checks"] == ["Run or record required search: docs."]
    assert payload["evidence"][0]["file"] == "README.md"
    assert payload["searches"][0]["query"] == "docs"


def test_render_checked_claim_diff_shows_status_changes(tmp_path: Path) -> None:
    """Checked-claim diffs compare status, gate, evidence, and limits."""
    old_claim = sample_checked_claim(status="too_broad", gate_status="answer_with_qualifications")
    new_claim = sample_checked_claim(status="contradicted", gate_status="do_not_claim")
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    old_path.write_text(json.dumps(old_claim), encoding="utf-8")
    new_path.write_text(json.dumps(new_claim), encoding="utf-8")

    markdown = render_checked_claim_diff(old_path, new_path)

    assert "# Plumbref Checked Claim Diff" in markdown
    assert "Status: `too_broad` -> `contradicted`" in markdown
    assert "Gate: `answer_with_qualifications` -> `do_not_claim`" in markdown


def test_render_rerun_packet_is_honest_about_agent_work(tmp_path: Path) -> None:
    """Rerun packets instruct an MCP/agent workflow without pretending to reason automatically."""
    claim_path = tmp_path / "claim.json"
    claim_path.write_text(json.dumps(sample_checked_claim()), encoding="utf-8")

    markdown = render_rerun_packet(claim_path)

    assert "# Plumbref Claim Rerun Packet" in markdown
    assert "Start a new Plumbref session" in markdown
    assert "Record a new judgment" in markdown
    assert "Original Missing Checks" in markdown


def test_render_claim_check_flags_only_docs_claim_against_code_diff(tmp_path: Path) -> None:
    """Advisory checks flag obvious contradictions in explicit PR claims."""
    claims = tmp_path / "claims.md"
    claims.write_text("- This PR only changes docs.\n", encoding="utf-8")
    diff = tmp_path / "change.diff"
    diff.write_text(
        "\n".join(
            [
                "diff --git a/plumbref/reports.py b/plumbref/reports.py",
                "--- a/plumbref/reports.py",
                "+++ b/plumbref/reports.py",
            ]
        ),
        encoding="utf-8",
    )

    markdown = render_claim_check(claims_path=claims, repo_root=tmp_path, diff_path=diff)

    assert "# Plumbref Advisory Claim Check" in markdown
    assert "## Do Not Rely On" in markdown
    assert "Changed non-doc/copy file: plumbref/reports.py" in markdown


def sample_report() -> dict[str, object]:
    return {
        "created_at": "2026-06-22T00:00:00Z",
        "question": "Check PR claim.",
        "mode": "change_impact",
        "template_values": {"claim_keyword": "docs"},
        "report_identity": {
            "id": "report-1",
            "repo_identifier": "repo-1",
            "repo_state": "state-1",
        },
        "template": {"id": "change_impact"},
        "quality": {
            "answer_gate": {
                "status": "answer_with_qualifications",
                "summary": "Missing required search.",
            },
            "gate_coverage": {
                "missing_by_claim": {
                    "source-claim-1": ["Run or record required search: docs."],
                }
            },
        },
        "claims": [
            {
                "id": "source-claim-1",
                "stable_id": "claim-001",
                "text": "This PR only changes docs.",
                "status": "too_broad",
                "claim_type": "impact",
                "risk": "medium",
                "absolute_language": ["only"],
                "judgment": {
                    "evidence_ids": ["ev-1"],
                    "limits": "Code paths were not checked.",
                    "safer_wording": "Docs changed; code impact not verified.",
                    "contradiction_searched": True,
                },
            }
        ],
        "evidence": [
            {
                "id": "ev-1",
                "file": "README.md",
                "start_line": 1,
                "end_line": 3,
                "sha256": "abc123",
                "summary": "README changed.",
                "evidence_category": "docs",
            }
        ],
        "trace": [
            {
                "claim_id": "source-claim-1",
                "query": "docs",
                "matched_files": ["README.md"],
            }
        ],
    }


def sample_checked_claim(
    *,
    status: str = "too_broad",
    gate_status: str = "answer_with_qualifications",
) -> dict[str, object]:
    return {
        "schema_version": "1",
        "claim_id": "claim-001",
        "claim_text": "This PR only changes docs.",
        "status": status,
        "gate_status": gate_status,
        "template_id": "change_impact",
        "missing_checks": ["Run or record required search: docs."],
        "evidence": [
            {
                "file": "README.md",
                "start_line": 1,
                "end_line": 3,
                "sha256": "abc123",
            }
        ],
    }
