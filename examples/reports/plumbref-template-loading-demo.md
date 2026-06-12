# Dogfood Demo: Template Loading

This is a non-toy Plumbref-style report over Plumbref's own source code. It is
intended as a public demo artifact: the subject is this repository's template
loading workflow, not a private codebase.

Question:

```text
How does Plumbref load verification templates, and can custom templates override built-ins?
```

Initial hypothesis:

```text
Plumbref loads built-in templates, then loads user/repo configured templates.
Custom templates with the same ID can override built-ins. Template checklists
also guarantee that every required evidence category was completed.
```

# Plumbref Report

Verdict: Partially supported
Verification mode: explanation
Budget mode: normal
Template: Generic verification (`generic_verification` v1.0)

## Measurement

- Claims: 3 (supported=2, too_broad=1)
- Searches run: 5
- Search results: 14 match(es) across 4 matched file(s)
- Evidence read: 4 file read(s), 4 snippet(s), 4 unique evidence file(s)
- Contradiction passes: 2/3 judged claim(s)
- Unsupported or qualified claims caught: 1 (too_broad=1)

## Claims

### supported: Plumbref loads built-in templates before loading templates from configured directories.

- Type: behavior
- Risk: medium
- Budget used: searches=2, files=1, snippets=1, reference_depth=0
- Reasoning: `load_templates` initializes an empty registry, stores every built-in template by ID, then iterates through discovered template directories and stores those templates by ID.
- Limits: This supports the registry order in the current implementation, not any external package manager behavior.
- Contradiction pass: yes
- Evidence:
  - `plumbref/template_registry.py:18-30` [direct implementation]: `load_templates` writes built-ins first and then writes templates loaded from discovered directories.

    ```text
    def load_templates(repo_root: Path, config: PlumbrefConfig | None = None) -> dict[str, VerificationTemplate]:
        resolved_repo_root = repo_root.expanduser().resolve()
        resolved_config = config or load_config(resolved_repo_root)
        templates: dict[str, VerificationTemplate] = {}

        for template in load_builtin_templates():
            templates[template.id] = template

        for directory in template_directories(resolved_repo_root, resolved_config):
            for template in load_templates_from_directory(directory):
                templates[template.id] = template

        return templates
    ```

### supported: A custom template with the same ID can override a built-in template.

- Type: behavior
- Risk: medium
- Budget used: searches=2, files=2, snippets=2, reference_depth=0
- Reasoning: Templates are stored in a dictionary by `template.id`, so a later source replaces an earlier value with the same ID. The test suite verifies this behavior with a repo-local `change_impact` override.
- Limits: This verifies repo-local override behavior. Shared template-pack precedence depends on the configured loading order.
- Contradiction pass: yes
- Evidence:
  - `plumbref/template_registry.py:23-28` [direct implementation]: Later loaded templates are assigned into the same dictionary key.

    ```text
    for template in load_builtin_templates():
        templates[template.id] = template

    for directory in template_directories(resolved_repo_root, resolved_config):
        for template in load_templates_from_directory(directory):
            templates[template.id] = template
    ```

  - `tests/test_templates.py:31-49` [tests]: A repo-local `change_impact.toml` with version `2.0` overrides the built-in template.

    ```text
    def test_repo_local_template_overrides_builtin(tmp_path: Path) -> None:
        """Repo-local templates can override built-ins without changing package code."""
        template_dir = tmp_path / ".plumbref" / "templates"
        template_dir.mkdir(parents=True)
        (template_dir / "change_impact.toml").write_text(
            """
    id = "change_impact"
    version = "2.0"
    name = "Repo change impact"
    description = "Repo-specific override."
    required_searches = ["{changed_symbol} owner"]
    """.strip(),
            encoding="utf-8",
        )

        template = get_template("change_impact", repo_root=tmp_path)

        assert template.version == "2.0"
        assert template.source.endswith(".plumbref/templates/change_impact.toml")
    ```

### too_broad: Template checklists guarantee that every required evidence category was completed.

- Type: behavior
- Risk: high
- Budget used: searches=1, files=2, snippets=1, reference_depth=0
- Reasoning: Reports display template checklist metadata and the evidence categories that were recorded, but supported judgments are currently enforced only for cited evidence and contradiction pass. The source does not enforce every template evidence category before support.
- Limits: Safer wording: template checklists make skipped categories visible; they do not yet guarantee full checklist completion.
- Contradiction pass: no
- Evidence:
  - `plumbref/models.py:210-216` [direct implementation]: Supported judgments require evidence IDs and a contradiction pass.

    ```text
    @model_validator(mode="after")
    def validate_supported_judgment(self) -> Judgment:
        if self.status == ClaimStatus.SUPPORTED and not self.evidence_ids:
            raise ValueError("supported judgments require at least one evidence id")
        if self.status == ClaimStatus.SUPPORTED and not self.contradiction_searched:
            raise ValueError("supported judgments require a contradiction pass")
        return self
    ```

  - `plumbref/reports.py:179-207` [reporting]: Measurement and checklist data are reported, including unsupported or qualified claims caught.

    ```text
    return {
        "claims_total": len(state.claims),
        "claim_status_counts": dict(sorted(status_counts.items())),
        "searches_run": len(state.traces),
        "search_matches_returned": sum(len(trace.matches) for trace in state.traces),
        "matched_files": len({file for trace in state.traces for file in trace.matched_files}),
        "evidence_files_read": sum(claim.usage.files for claim in state.claims.values()),
        "evidence_snippets_read": sum(claim.usage.snippets for claim in state.claims.values()),
        "unique_evidence_files": len({snippet.file for snippet in state.evidence.values()}),
        "contradiction_passes": contradiction_passes,
        "judged_claims": len(judged_claims),
        "too_broad_claims": status_counts[ClaimStatus.TOO_BROAD.value],
        "unsupported_or_qualified_claims": sum(status_counts[status] for status in unsupported_statuses),
    }
    ```

## Search Trace

- `load_templates template_directories` matched source and tests covering registry order.
- `repo local template overrides builtin` matched the custom override test.
- `supported judgments require template categories` did not find enforcement for required template evidence categories.
- `contradiction_searched supported judgment` matched judgment validation.
- `measurement unsupported too_broad` matched report measurement output.

## Safe Public Summary

Plumbref's template system is source-backed as an extensible registry: built-ins
load first, and user/repo/configured templates can override them by ID. The demo
also caught an over-broad claim: templates currently make coverage visible, but
they do not yet enforce completion of every evidence category before support.
