# Plumbref Reliance Check Demo

This demo uses Plumbref's own reliance-check pivot as the subject. The point is
to show the product moment: an agent made a broad claim, and Plumbref turned it
into wording that is safer to rely on.

## User Prompt

```text
The agent said this only changes docs. Check that before I rely on it.
```

## Answer Under Review

```text
This only changes docs and positioning copy.
```

## Inline Answer

```text
Based on checked evidence, rely on this only with the qualifications below.

Safe to rely on:
- The checked README changes reposition Plumbref around verifying AI codebase claims before reliance.
- The checked report renderer changes the agent-facing inline answer sections to Safe to rely on, Say with qualification, Do not rely on, Safer wording, Evidence, and Unchecked.

Do not rely on:
- contradicted: This only changes docs and positioning copy.

Safer wording:
- This changes docs and inline report-rendering behavior.

Evidence:
- `README.md:10-16`
- `README.md:59-77`
- `plumbref/reports.py:1177-1216`
- `plumbref/reports.py:1262-1308`

Verification: 3 claim(s) (supported=2, contradicted=1); 4 evidence snippet(s); 3/3 contradiction pass(es).
```

## Broader Follow-Up

The first-order check is enough to reject "only docs." If the reliance question
changes to "is this safe for every downstream consumer?", then run a deeper
pass for:

- downstream consumers of `inline_answer`
- tests for clients that parse inline answer text
- external docs or examples that assert the old section labels

## Verification Ledger

### supported: README now frames Plumbref as verifying AI codebase claims before reliance.

- Type: definition
- Risk: medium
- Reasoning: The README lead states the new reliance-check positioning and says Plumbref returns what is safe to rely on, what needs qualification, what not to rely on, and source lines.
- Contradiction pass: yes
- Evidence:
  - `README.md:10-16`

```text
Plumbref verifies AI codebase claims before you rely on them.

It gives coding agents an evidence gate: before you repeat or act on an answer,
the agent breaks it into claims, checks local repository evidence, and returns
what is safe to rely on, what needs qualification, what not to rely on, and the
source lines behind that call. When the answer is risky, qualified, or
explicitly requested, Plumbref also writes an inspectable report.
```

### supported: The inline answer renderer now emits reliance-oriented sections.

- Type: behavior
- Risk: high
- Reasoning: `build_inline_answer` renders the sections used in the demo: safe-to-rely-on claims, qualifications, do-not-rely-on claims, safer wording, evidence, unchecked areas, and verification counts.
- Contradiction pass: yes
- Evidence:
  - `plumbref/reports.py:1177-1216`

```text
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
        lines.extend(["", "Safe to rely on:", *supported_lines])

    qualified_lines = inline_qualified_lines(state, safe_answer, config)
    if qualified_lines:
        lines.extend(["", "Say with qualification:", *qualified_lines])

    avoid_lines = inline_avoid_lines(safe_answer, config)
    if avoid_lines:
        lines.extend(["", "Do not rely on:", *avoid_lines])

    safer_lines = inline_safer_wording_lines(safe_answer, config)
    if safer_lines:
        lines.extend(["", "Safer wording:", *safer_lines])

    evidence_lines = inline_evidence_lines(state, config)
    if evidence_lines:
        lines.extend(["", "Evidence:", *evidence_lines])

    unchecked_lines = inline_unchecked_lines(quality, config)
    if unchecked_lines:
        lines.extend(["", "Unchecked:", *unchecked_lines])

    lines.extend(["", f"Verification: {inline_measurement_summary(state, measurement)}"])
```

### contradicted: This only changes docs and positioning copy.

- Type: impact
- Risk: high
- Reasoning: First-order evidence contradicts the claim as written: the checked change includes `plumbref/reports.py`, not only documentation or positioning copy.
- Safer wording: This changes docs and inline report-rendering behavior.
- Contradiction pass: yes
- Evidence:
  - `README.md:59-77`
  - `plumbref/reports.py:1262-1308`

```text
Safe to rely on:
- The checked function rewrites the report label from "items" to "records".

Say with qualification:
- too_broad: The change only affects formatting.

Safer wording:
- The checked function changes report-label wording, but downstream exports were
  not fully traced.

Evidence:
- `src/reports/labels.ts:41-58`

Unchecked:
- Conflicting-code-path search not recorded: generated client exports.
```

```text
def inline_qualified_lines(
    state: SessionState,
    safe_answer: dict[str, Any],
    config: PlumbrefConfig,
) -> list[str]:
    items: list[tuple[int, str]] = []
    for claim in state.claims.values():
        judgment = state.judgments.get(claim.id)
        if not judgment or not judgment.limits.strip():
            continue
        if claim.status != ClaimStatus.SUPPORTED:
            continue
        if not is_material_supported_limit(judgment.limits):
            continue
        items.append((inline_limit_priority(claim, judgment.limits), judgment.limits))

    for item in safe_answer["qualified"]:
        items.append((-100, status_claim_text(item)))

    ordered = [text for _priority, text in sorted(items, key=lambda item: item[0])]
    deduped = dedupe_preserve_order([redact_text(text, config.privacy_patterns) for text in ordered if text.strip()])
    lines = [f"- {ensure_sentence(text)}" for text in deduped[:4]]
    if len(deduped) > 4:
        lines.append(f"- {len(deduped) - 4} more qualification(s) in the report.")
    return lines


def inline_avoid_lines(safe_answer: dict[str, Any], config: PlumbrefConfig) -> list[str]:
    texts = [status_claim_text(item) for item in safe_answer["avoid"]]
    deduped = dedupe_preserve_order([redact_text(text, config.privacy_patterns) for text in texts if text.strip()])
    lines = [f"- {ensure_sentence(text)}" for text in deduped[:4]]
    if len(deduped) > 4:
        lines.append(f"- {len(deduped) - 4} more avoid item(s) in the report.")
    return lines


def inline_safer_wording_lines(safe_answer: dict[str, Any], config: PlumbrefConfig) -> list[str]:
    texts = [
        item["safer_wording"]
        for item in [*safe_answer["qualified"], *safe_answer["avoid"]]
        if item.get("safer_wording")
    ]
```

## Why This Demo Matters

Asking the agent "are you sure?" could produce another paragraph of reassurance.
This output gives the user a reliance decision:

- safe to rely on the README positioning change
- safe to rely on the inline-answer renderer change
- do not rely on "only docs" as written because first-order evidence contradicts it
- use the safer wording instead
- inspect the exact source lines if the decision matters
