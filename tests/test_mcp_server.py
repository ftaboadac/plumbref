from __future__ import annotations

import json
from pathlib import Path


def test_mcp_server_import_does_not_require_runtime_import() -> None:
    """MCP server module imports without starting the stdio server."""
    import plumbref.mcp_server

    assert plumbref.mcp_server.run_mcp_server


def test_mcp_start_normalizes_common_agent_aliases() -> None:
    """Common first-run agent guesses map to valid internal enums."""
    from plumbref.mcp_server import normalize_output_modes, normalize_verification_mode
    from plumbref.models import OutputMode, VerificationMode

    assert normalize_verification_mode("verify") == VerificationMode.EXPLANATION
    assert normalize_verification_mode("explain-flow") == VerificationMode.EXPLANATION
    assert normalize_output_modes(["inline_answer", "report"]) == [OutputMode.ENGINEER]
    assert normalize_output_modes(["json_report", "support_answer"]) == [OutputMode.JSON, OutputMode.SUPPORT]


def test_mcp_record_judgment_normalizes_common_status_aliases() -> None:
    """Common first-run judgment guesses map to conservative claim statuses."""
    from plumbref.mcp_server import normalize_claim_status
    from plumbref.models import ClaimStatus

    assert normalize_claim_status("refuted") == ClaimStatus.CONTRADICTED
    assert normalize_claim_status("partially_supported") == ClaimStatus.UNCERTAIN
    assert normalize_claim_status("partially-supported") == ClaimStatus.UNCERTAIN
    assert normalize_claim_status("overbroad") == ClaimStatus.TOO_BROAD
    assert normalize_claim_status("unverifiable") == ClaimStatus.NOT_VERIFIABLE


def test_mcp_diff_reports_tool_returns_structured_diff(tmp_path: Path) -> None:
    """MCP diff helper returns summary, changes, and Markdown for agents."""
    from plumbref.mcp_server import diff_reports_tool

    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    old_path.write_text(
        json.dumps(
            report_payload(
                status="supported",
                evidence_id="old-evidence",
                evidence_sha="abc123",
            )
        ),
        encoding="utf-8",
    )
    new_path.write_text(
        json.dumps(
            report_payload(
                status="contradicted",
                evidence_id="new-evidence",
                evidence_sha="def456",
            )
        ),
        encoding="utf-8",
    )

    response = diff_reports_tool(old_report_path=str(old_path), new_report_path=str(new_path))

    assert response["summary"]["claims_compared"] == 1
    assert response["summary"]["status_changes"] == 1
    assert response["changes"][0]["stable_id"] == "claim-001"
    assert response["changes"][0]["old"]["status"] == "supported"
    assert response["changes"][0]["new"]["status"] == "contradicted"
    assert "# Plumbref Report Diff" in response["markdown"]


def report_payload(*, status: str, evidence_id: str, evidence_sha: str) -> dict[str, object]:
    return {
        "question": "How does SSO eligibility work?",
        "template": {"id": "explain_flow", "name": "Explain Flow"},
        "claims": [
            {
                "id": "claim-uuid",
                "stable_id": "claim-001",
                "text": "SSO requires a configured provider.",
                "status": status,
                "claim_type": "business_rule",
                "judgment": {
                    "status": status,
                    "evidence_ids": [evidence_id],
                    "limits": "",
                    "contradiction_searched": status == "supported",
                },
            }
        ],
        "evidence": [
            {
                "id": evidence_id,
                "claim_id": "claim-uuid",
                "claim_ids": ["claim-uuid"],
                "file": "auth/sso.py",
                "start_line": 10,
                "end_line": 20,
                "sha256": evidence_sha,
                "excerpt": "",
            }
        ],
    }
