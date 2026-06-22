# MCP Stdio Transcript Fixture

Status: reproducible protocol fixture, not yet a captured Codex/Claude/Cursor
client transcript.

This transcript shows the intended Plumbref MCP tool flow for the first-run SSO
claim. It is useful for validating the product moment, but it does not replace
a named-client transcript from Codex, Claude Code, or Cursor.

## Setup

```shell
plumbref doctor --repo-root . --check-mcp-startup
plumbref mcp --repo-root .
```

## User Prompt

```text
The agent said SSO only depends on Okta. Check that before I tell support.
Use Plumbref and return the inline answer.
```

## Tool Flow

The agent starts a session:

```json
{
  "tool": "plumbref_start",
  "arguments": {
    "question": "The agent said SSO only depends on Okta. Check that before I tell support.",
    "answer": "SSO only depends on Okta.",
    "mode": "explanation",
    "template_id": "explain_flow",
    "template_values": {
      "flow_name": "SSO eligibility",
      "entry_point": "start_sso_login",
      "main_entity": "Company",
      "external_system": "Okta"
    }
  }
}
```

The agent stores the claim:

```json
{
  "tool": "plumbref_extract_claims",
  "arguments": {
    "claims": [
      {
        "id": "claim-sso-only-okta",
        "text": "SSO only depends on Okta.",
        "claim_type": "business_rule",
        "risk": "medium"
      }
    ]
  }
}
```

The agent searches for evidence and contradiction paths:

```json
[
  {
    "tool": "plumbref_search_repo",
    "arguments": {
      "claim_id": "claim-sso-only-okta",
      "query": "is_sso_eligible"
    }
  },
  {
    "tool": "plumbref_search_repo",
    "arguments": {
      "claim_id": "claim-sso-only-okta",
      "query": "rippling_integration_id"
    }
  },
  {
    "tool": "plumbref_search_repo",
    "arguments": {
      "claim_id": "claim-sso-only-okta",
      "query": "okta_enabled"
    }
  }
]
```

The agent reads the relevant source:

```json
{
  "tool": "plumbref_read_evidence",
  "arguments": {
    "claim_id": "claim-sso-only-okta",
    "file": "examples/fixtures/sso-before/app/sso.py",
    "start_line": 15,
    "end_line": 22,
    "summary": "is_sso_eligible returns true for a Rippling integration or Okta.",
    "evidence_category": "main implementation path"
  }
}
```

The agent records a contradicted judgment:

```json
{
  "tool": "plumbref_record_judgment",
  "arguments": {
    "claim_id": "claim-sso-only-okta",
    "status": "contradicted",
    "evidence_ids": ["<evidence id returned by plumbref_read_evidence>"],
    "reasoning_summary": "The checked code allows SSO eligibility through a Rippling integration or Okta.",
    "limits": "Tests and support-facing docs were not checked in this first-run fixture.",
    "safer_wording": "The checked SSO eligibility path can allow SSO through Okta or a Rippling integration.",
    "contradiction_searched": true,
    "contradiction_notes": "Searched for non-Okta SSO eligibility paths and found rippling_integration_id."
  }
}
```

The agent renders the result:

```json
{
  "tool": "plumbref_render_report",
  "arguments": {
    "output_modes": ["engineer", "json"],
    "write_files": true,
    "report_write_reason": "first_run_demo"
  }
}
```

## Expected Inline Answer

See `expected/inline-answer.md`.

## Remaining Proof Gap

The next artifact should be a captured transcript from one named client:

- exact client
- exact MCP config file path
- install/setup commands
- screenshot or copied chat transcript
- tool calls
- final inline answer
- generated report path
