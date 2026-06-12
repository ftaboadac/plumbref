# Plumbref Report

Verdict: Partially supported
Verification mode: scenario
Budget mode: normal
Template: Field migration (`field_migration` v1.0)

Scenario: Rename the public input template_id to verification_template_id while preserving existing behavior.

## Template Checklist
- Source: builtin:field_migration.toml
- Required claim types: `definition`, `behavior`, `impact`, `recommendation`
- Required searches:
  - `{field_name}`
  - `{source_owner}`
  - `{target_owner}`
  - `{field_name} read`
  - `{field_name} write`
- Contradiction searches:
  - `{field_name} migration`
  - `{field_name} backfill`
  - `{field_name} serializer schema payload`
  - `{field_name} external api webhook sync`
  - `{field_name} test fixture`
- Evidence categories:
  - `field definition`
  - `direct reads`
  - `direct writes`
  - `persistence or migration artifacts`
  - `validation or schema boundary`
  - `API or event payload boundary`
  - `background jobs or async workflows`
  - `external integrations`
  - `tests`
  - `docs`
- Report sections:
  - `supported migration impacts`
  - `likely code changes`
  - `data migration or backfill risks`
  - `downstream consumers`
  - `unchecked areas`
  - `safer implementation plan`
- Unchecked-area prompts:
  - Which reads or writes were not traced to a caller?
  - Were persistence and backfill requirements found?
  - Were external payload boundaries checked?
- Evidence categories recorded: `API or event payload boundary`, `direct reads`, `docs`, `field definition`
- Contradiction passes recorded: 4/4 judged claim(s)

## Measurement
- Claims: 4 (supported=3, too_broad=1)
- Searches run: 9
- Search results: 69 match(es) across 11 matched file(s)
- Evidence read: 9 file read(s), 9 snippet(s), 5 unique evidence file(s)
- Contradiction passes: 4/4 judged claim(s)
- Unsupported or qualified claims caught: 1 (too_broad=1)
- Source-token estimate:
  - Bounded evidence: 2491 estimated token(s)
  - Search previews: 857 estimated token(s)
  - Full cited files baseline: 10749 estimated token(s) (77% reduction from bounded evidence)
  - Full matched files baseline: 18503 estimated token(s) (87% reduction from bounded evidence)
  - Method: estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing

## Predicted Outcomes

### supported: template_id is part of the MCP plumbref_start input and is passed into session startup.
- Type: api
- Risk: high
- Budget used: searches=2, files=1, snippets=1, reference_depth=0
- Reasoning: template_id appears in the MCP tool signature and is forwarded into session startup.
- Limits: This checks the Python MCP server contract, not generated MCP client metadata in a specific editor.
- Contradiction pass: yes
- Evidence:
  - `plumbref/mcp_server.py:34-54` [API or event payload boundary]: The MCP start tool accepts template_id and forwards it to HARNESS.start_session.

    ```text
            question: str,
            answer: str,
            mode: str = "explanation",
            scenario: str | None = None,
            budget_mode: str | None = None,
            output_modes: list[str] | None = None,
            template_id: str | None = None,
        ) -> dict[str, Any]:
            """Start a verification session."""
            modes = [OutputMode(output_mode) for output_mode in output_modes] if output_modes else None
            state = HARNESS.start_session(
                repo_root=repo_root,
                question=question,
                answer=answer,
                mode=VerificationMode(mode),
                scenario=scenario,
                config_path=config_path,
                budget_mode=BudgetMode(budget_mode) if budget_mode else None,
                output_modes=modes,
                template_id=template_id,
            )
    ```

### supported: template_id is exposed through CLI options for verify and templates commands.
- Type: api
- Risk: high
- Budget used: searches=2, files=3, snippets=3, reference_depth=0
- Reasoning: The CLI and docs expose template_id as public syntax in multiple places.
- Limits: This does not enumerate every downstream blog post or third-party client config.
- Contradiction pass: yes
- Evidence:
  - `plumbref/cli.py:137-170` [API or event payload boundary]: The verify command exposes template_id and passes it to start_session.

    ```text
    @app.command()
    def verify(
        question: Annotated[str, typer.Option(help="Original user question.")],
        answer: Annotated[Path, typer.Option(help="Path to the answer Markdown/text file.")],
        repo_root: Annotated[Path | None, typer.Option(help="Repository root to verify against.")] = None,
        claims: Annotated[Path | None, typer.Option(help="Optional JSON file of agent-extracted claims.")] = None,
        mode: Annotated[VerificationMode, typer.Option(help="Verification mode.")] = VerificationMode.EXPLANATION,
        scenario: Annotated[str | None, typer.Option(help="Scenario being verified for scenario mode.")] = None,
        changed_file: Annotated[
            list[str] | None, typer.Option("--changed-file", help="Changed file for change_impact mode.")
        ] = None,
        diff: Annotated[Path | None, typer.Option(help="Path to a git diff patch for change_impact mode.")] = None,
        diff_target: Annotated[
            str | None, typer.Option(help="Git diff target, such as main...HEAD, for change_impact mode.")
        ] = None,
        base_ref: Annotated[str | None, typer.Option(help="Base ref for change_impact mode.")] = None,
        compare_ref: Annotated[str | None, typer.Option(help="Compare ref for change_impact mode.")] = None,
        config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
        budget_mode: Annotated[BudgetMode | None, typer.Option(help="Verification budget mode.")] = None,
        output_mode: Annotated[list[OutputMode] | None, typer.Option(help="Output mode.")] = None,
        template_id: Annotated[str | None, typer.Option(help="Verification template ID.")] = None,
    ) -> None:
        try:
            state = HARNESS.start_session(
                repo_root=repo_root or Path.cwd(),
                question=question,
                answer=answer.read_text(encoding="utf-8"),
                mode=mode,
                scenario=scenario,
                config_path=config,
                budget_mode=budget_mode,
                output_modes=output_mode,
                template_id=template_id,
            )
    ```
  - `plumbref/cli.py:212-231` [API or event payload boundary]: The templates command exposes template_id to inspect one template.

    ```text
    @app.command("templates")
    def templates_command(
        repo_root: Annotated[Path | None, typer.Option(help="Repository root used for repo-local templates.")] = None,
        config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
        template_id: Annotated[str | None, typer.Option(help="Show one template in full.")] = None,
    ) -> None:
        try:
            resolved_repo_root = repo_root or Path.cwd()
            loaded_config = HARNESS.get_config() if HARNESS.active_session_id and config is None else None
            if loaded_config is None:
                loaded_config = load_config(resolved_repo_root, config)
            loaded = load_templates(resolved_repo_root, loaded_config)
        except (ConfigLoadError, TemplateLoadError) as exc:
            raise typer.BadParameter(str(exc)) from exc
    
        if template_id:
            if template_id not in loaded:
                available = ", ".join(sorted(loaded)) or "none"
                raise typer.BadParameter(f"unknown template {template_id!r}; available templates: {available}")
            typer.echo(loaded[template_id].model_dump_json(indent=2))
    ```
  - `README.md:277-299` [docs]: Public docs show --template-id and template_id in agent payloads.

    ````text
    List available templates:
    
    ```shell
    plumbref templates --repo-root /path/to/repo
    ```
    
    Inspect one template:
    
    ```shell
    plumbref templates --repo-root /path/to/repo --template-id field_migration
    ```
    
    Agents can start a session with a template:
    
    ```json
    {
      "question": "What should we consider before moving provider_id?",
      "answer": "The field move may affect job enqueueing and payload builders.",
      "mode": "scenario",
      "template_id": "field_migration",
      "budget_mode": "normal",
      "output_modes": ["engineer", "json"]
    }
    ````

### supported: Session startup falls back from explicit template_id to config.default_template_id and uses the selected template for mode validation and budget selection.
- Type: behavior
- Risk: medium
- Budget used: searches=2, files=2, snippets=2, reference_depth=0
- Reasoning: The selected template id participates in config fallback, template lookup, mode validation, and budget selection.
- Limits: This checks session startup, not all docs examples.
- Contradiction pass: yes
- Evidence:
  - `plumbref/sessions.py:25-65` [direct reads]: start_session chooses explicit template_id or config.default_template_id, validates mode, and applies template budgets.

    ```text
        def start_session(
            self,
            *,
            repo_root: Path,
            question: str,
            answer: str,
            mode: VerificationMode = VerificationMode.EXPLANATION,
            scenario: str | None = None,
            config_path: Path | None = None,
            budget_mode: BudgetMode | None = None,
            output_modes: list[OutputMode] | None = None,
            template_id: str | None = None,
        ) -> SessionState:
            resolved_repo_root = repo_root.expanduser().resolve()
            config = load_config(resolved_repo_root, config_path)
            resolved_template_id = template_id or config.default_template_id
            template = (
                get_template(resolved_template_id, repo_root=resolved_repo_root, config=config)
                if resolved_template_id
                else None
            )
            if template and template.modes and mode not in template.modes:
                supported_modes = ", ".join(template_mode.value for template_mode in template.modes)
                raise TemplateLoadError(
                    f"template {template.id!r} does not support mode {mode.value!r}; "
                    f"supported modes: {supported_modes}"
                )
            resolved_budget_mode = budget_mode or config.default_budget_mode
            resolved_output_modes = output_modes or config.default_output_modes
            budget = template.budgets.get(resolved_budget_mode) if template else None
            session = VerificationSession(
                repo_root=resolved_repo_root,
                question=question,
                answer=answer,
                mode=mode,
                scenario=scenario,
                template=template,
                budget_mode=resolved_budget_mode,
                output_modes=resolved_output_modes,
            )
            state = SessionState(session=session, budget=budget or budget_for_mode(resolved_budget_mode))
    ```
  - `plumbref/config.py:24-31` [field definition]: The config model includes default_template_id.

    ```text
            ],
        )
        docs_paths: list[str] = Field(default_factory=lambda: ["docs"])
        cache_path: Path = Path(".cache/plumbref")
        report_path: Path = Path(".cache/plumbref/reports")
        template_paths: list[Path] = Field(default_factory=list)
        default_template_id: str | None = None
        privacy_patterns: list[str] = Field(
    ```

### too_broad: Only the Pydantic model field would need to change for this rename.
- Type: recommendation
- Risk: high
- Budget used: searches=3, files=3, snippets=3, reference_depth=0
- Reasoning: The evidence shows public MCP, CLI, config, docs, and tests use the name. A model-only rename would miss public interfaces.
- Limits: Safer plan: add a backwards-compatible alias/deprecation path, then update CLI, MCP docs, tests, and examples.
- Contradiction pass: yes
- Evidence:
  - `plumbref/mcp_server.py:34-54` [API or event payload boundary]: template_id is a public MCP tool argument, not only an internal model field.

    ```text
            question: str,
            answer: str,
            mode: str = "explanation",
            scenario: str | None = None,
            budget_mode: str | None = None,
            output_modes: list[str] | None = None,
            template_id: str | None = None,
        ) -> dict[str, Any]:
            """Start a verification session."""
            modes = [OutputMode(output_mode) for output_mode in output_modes] if output_modes else None
            state = HARNESS.start_session(
                repo_root=repo_root,
                question=question,
                answer=answer,
                mode=VerificationMode(mode),
                scenario=scenario,
                config_path=config_path,
                budget_mode=BudgetMode(budget_mode) if budget_mode else None,
                output_modes=modes,
                template_id=template_id,
            )
    ```
  - `plumbref/cli.py:137-170` [API or event payload boundary]: template_id is part of CLI verify behavior.

    ```text
    @app.command()
    def verify(
        question: Annotated[str, typer.Option(help="Original user question.")],
        answer: Annotated[Path, typer.Option(help="Path to the answer Markdown/text file.")],
        repo_root: Annotated[Path | None, typer.Option(help="Repository root to verify against.")] = None,
        claims: Annotated[Path | None, typer.Option(help="Optional JSON file of agent-extracted claims.")] = None,
        mode: Annotated[VerificationMode, typer.Option(help="Verification mode.")] = VerificationMode.EXPLANATION,
        scenario: Annotated[str | None, typer.Option(help="Scenario being verified for scenario mode.")] = None,
        changed_file: Annotated[
            list[str] | None, typer.Option("--changed-file", help="Changed file for change_impact mode.")
        ] = None,
        diff: Annotated[Path | None, typer.Option(help="Path to a git diff patch for change_impact mode.")] = None,
        diff_target: Annotated[
            str | None, typer.Option(help="Git diff target, such as main...HEAD, for change_impact mode.")
        ] = None,
        base_ref: Annotated[str | None, typer.Option(help="Base ref for change_impact mode.")] = None,
        compare_ref: Annotated[str | None, typer.Option(help="Compare ref for change_impact mode.")] = None,
        config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
        budget_mode: Annotated[BudgetMode | None, typer.Option(help="Verification budget mode.")] = None,
        output_mode: Annotated[list[OutputMode] | None, typer.Option(help="Output mode.")] = None,
        template_id: Annotated[str | None, typer.Option(help="Verification template ID.")] = None,
    ) -> None:
        try:
            state = HARNESS.start_session(
                repo_root=repo_root or Path.cwd(),
                question=question,
                answer=answer.read_text(encoding="utf-8"),
                mode=mode,
                scenario=scenario,
                config_path=config,
                budget_mode=budget_mode,
                output_modes=output_mode,
                template_id=template_id,
            )
    ```
  - `README.md:277-299` [docs]: Docs expose the current template_id spelling.

    ````text
    List available templates:
    
    ```shell
    plumbref templates --repo-root /path/to/repo
    ```
    
    Inspect one template:
    
    ```shell
    plumbref templates --repo-root /path/to/repo --template-id field_migration
    ```
    
    Agents can start a session with a template:
    
    ```json
    {
      "question": "What should we consider before moving provider_id?",
      "answer": "The field move may affect job enqueueing and payload builders.",
      "mode": "scenario",
      "template_id": "field_migration",
      "budget_mode": "normal",
      "output_modes": ["engineer", "json"]
    }
    ````

## Search Trace
- `template_id: str | None` matched 3 file(s) in 11ms.
  - Files: `plumbref/mcp_server.py`, `plumbref/config.py`, `plumbref/sessions.py`
  - Matches:
    - `plumbref/mcp_server.py:40`: template_id: str | None = None,
    - `plumbref/config.py:30`: default_template_id: str | None = None
    - `plumbref/sessions.py:36`: template_id: str | None = None,
- `plumbref_start` matched 1 file(s) in 12ms.
  - Files: `plumbref/mcp_server.py`
  - Matches:
    - `plumbref/mcp_server.py:33`: def plumbref_start(
- `template_id` matched 8 file(s) in 13ms.
  - Files: `README.md`, `docs/agent-usage.md`, `tests/test_cli_onboarding.py`, `tests/test_search_and_evidence.py`, `tests/test_templates.py`
  - Additional files omitted: 3
  - Matches:
    - `README.md:152`: default_template_id = "generic_verification"
    - `README.md:296`: "template_id": "field_migration",
    - `docs/agent-usage.md:100`: hypothesis, the verification mode, budget mode, and selected template_id.
    - `docs/agent-usage.md:165`: "template_id": "explain_flow",
    - `docs/agent-usage.md:206`: "template_id": "field_migration",
    - Additional matches omitted: 15
- `--template-id` matched 3 file(s) in 15ms.
  - Files: `README.md`, `docs/launch-checklist.md`, `tests/test_search_and_evidence.py`
  - Matches:
    - `README.md:286`: plumbref templates --repo-root /path/to/repo --template-id field_migration
    - `docs/launch-checklist.md:17`: plumbref templates --repo-root . --template-id change_impact
    - `tests/test_search_and_evidence.py:42`: "Use plumbref templates --template-id field_migration.\n",
    - `tests/test_search_and_evidence.py:52`: claim = ClaimWorkItem(text="The README documents --template-id.")
    - `tests/test_search_and_evidence.py:56`: trace = search_repo(state=state, config=config, claim_id=claim.id, query="--template-id")
    - Additional matches omitted: 1
- `default_template_id` matched 5 file(s) in 13ms.
  - Files: `README.md`, `tests/test_cli_onboarding.py`, `plumbref/cli.py`, `plumbref/config.py`, `plumbref/sessions.py`
  - Matches:
    - `README.md:152`: default_template_id = "generic_verification"
    - `tests/test_cli_onboarding.py:40`: assert "default_template_id = \"generic_verification\"" in (tmp_path / ".plumbref.toml").read_text(
    - `plumbref/cli.py:38`: default_template_id = "generic_verification"
    - `plumbref/config.py:30`: default_template_id: str | None = None
    - `plumbref/sessions.py:40`: resolved_template_id = template_id or config.default_template_id
- `resolved_template_id` matched 1 file(s) in 12ms.
  - Files: `plumbref/sessions.py`
  - Matches:
    - `plumbref/sessions.py:40`: resolved_template_id = template_id or config.default_template_id
    - `plumbref/sessions.py:42`: get_template(resolved_template_id, repo_root=resolved_repo_root, config=config)
    - `plumbref/sessions.py:43`: if resolved_template_id
- `template_id` matched 8 file(s) in 14ms.
  - Files: `README.md`, `docs/agent-usage.md`, `tests/test_cli_onboarding.py`, `tests/test_search_and_evidence.py`, `tests/test_templates.py`
  - Additional files omitted: 3
  - Matches:
    - `README.md:152`: default_template_id = "generic_verification"
    - `README.md:296`: "template_id": "field_migration",
    - `docs/agent-usage.md:100`: hypothesis, the verification mode, budget mode, and selected template_id.
    - `docs/agent-usage.md:165`: "template_id": "explain_flow",
    - `docs/agent-usage.md:206`: "template_id": "field_migration",
    - Additional matches omitted: 15
- `default_template_id` matched 5 file(s) in 13ms.
  - Files: `README.md`, `tests/test_cli_onboarding.py`, `plumbref/config.py`, `plumbref/sessions.py`, `plumbref/cli.py`
  - Matches:
    - `README.md:152`: default_template_id = "generic_verification"
    - `tests/test_cli_onboarding.py:40`: assert "default_template_id = \"generic_verification\"" in (tmp_path / ".plumbref.toml").read_text(
    - `plumbref/config.py:30`: default_template_id: str | None = None
    - `plumbref/sessions.py:40`: resolved_template_id = template_id or config.default_template_id
    - `plumbref/cli.py:38`: default_template_id = "generic_verification"
- `--template-id` matched 3 file(s) in 17ms.
  - Files: `README.md`, `docs/launch-checklist.md`, `tests/test_search_and_evidence.py`
  - Matches:
    - `README.md:286`: plumbref templates --repo-root /path/to/repo --template-id field_migration
    - `docs/launch-checklist.md:17`: plumbref templates --repo-root . --template-id change_impact
    - `tests/test_search_and_evidence.py:42`: "Use plumbref templates --template-id field_migration.\n",
    - `tests/test_search_and_evidence.py:52`: claim = ClaimWorkItem(text="The README documents --template-id.")
    - `tests/test_search_and_evidence.py:56`: trace = search_repo(state=state, config=config, claim_id=claim.id, query="--template-id")
    - Additional matches omitted: 1

## Safe Conclusion
3 predicted outcome(s) are directly supported. 1 predicted outcome(s) need qualification before relying on this scenario.

Supported outcome(s):
- template_id is part of the MCP plumbref_start input and is passed into session startup.
- template_id is exposed through CLI options for verify and templates commands.
- Session startup falls back from explicit template_id to config.default_template_id and uses the selected template for mode validation and budget selection.

Needs qualification:
- too_broad: Only the Pydantic model field would need to change for this rename. Limits: Safer plan: add a backwards-compatible alias/deprecation path, then update CLI, MCP docs, tests, and examples.
