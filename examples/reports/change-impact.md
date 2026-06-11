# Plumbref Report

Verdict: Partially supported
Verification mode: change_impact
Budget mode: normal

## Change Scope
- Source: files
- Changed files:
  - `tests/fixtures/sample_repo/app.py`
- Changed symbols:
  - `tests/fixtures/sample_repo/app.py:19` function `update_report_wording`

## Impact Claims

### supported: The change affects report wording from items to records.
- Type: impact
- Risk: medium
- Budget used: searches=1, files=1, snippets=1, reference_depth=0
- Reasoning: The changed function replaces the word items with records in a report title string.
- Limits: This supports the changed symbol behavior, not every caller or downstream display.
- Contradiction pass: yes
- Evidence:
  - `tests/fixtures/sample_repo/app.py:19-20`: update_report_wording replaces items with records.

    ```text
    def update_report_wording(title: str) -> str:
        return title.replace("items", "records")
    ```

### too_broad: This change only affects report wording.
- Type: impact
- Risk: medium
- Budget used: searches=2, files=1, snippets=1, reference_depth=0
- Reasoning: The snippet supports a narrower wording change but does not prove no other behavior or caller is affected.
- Limits: Say the shown changed symbol affects report wording; verify callers before claiming it is the only effect.
- Contradiction pass: no
- Evidence:
  - `tests/fixtures/sample_repo/app.py:15-20`: The file also contains title rendering that controls report wording.

    ```text
    def render_report_title(total_records: int) -> str:
        return f"Report for {total_records} items"


    def update_report_wording(title: str) -> str:
        return title.replace("items", "records")
    ```

## Search Trace
- `update_report_wording` matched 1 file(s) in 7ms.
  - Files: `tests/fixtures/sample_repo/app.py`
  - Matches:
    - `tests/fixtures/sample_repo/app.py:19`: def update_report_wording(title: str) -> str:
- `items records report wording` matched 2 file(s) in 11ms.
  - Files: `tests/fixtures/sample_repo/app.py`, `tests/fixtures/sample_repo/docs.md`
  - Matches:
    - `tests/fixtures/sample_repo/app.py:16`: return f"Report for {total_records} items"
    - `tests/fixtures/sample_repo/app.py:20`: return title.replace("items", "records")
    - `tests/fixtures/sample_repo/docs.md:5`: Report wording changes replace "items" with "records".

## Missing / Uncertain Areas
- too_broad: This change only affects report wording. Limits: Say the shown changed symbol affects report wording; verify callers before claiming it is the only effect.

## Safer Impact Statement
1 impact claim(s) are directly supported. 1 impact claim(s) need qualification or follow-up.

Supported impact(s):
- The change affects report wording from items to records.

Qualify or avoid:
- too_broad: This change only affects report wording. Safer wording: Say the shown changed symbol affects report wording; verify callers before claiming it is the only effect.
