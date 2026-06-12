# Plumbref Report

Verdict: Partially supported
Verification mode: change_impact
Budget mode: normal
Template: Change impact (`change_impact` v1.0)

## Change Scope
- Source: files
- Changed files:
  - `plumbref/cli.py`
  - `plumbref/reports.py`
  - `README.md`
  - `docs/agent-usage.md`
  - `tests/test_cli_onboarding.py`
  - `tests/test_reports.py`

## Template Checklist
- Source: builtin:change_impact.toml
- Required claim types: `impact`, `behavior`, `api`
- Required searches:
  - `{changed_file}`
  - `{changed_symbol}`
  - `{changed_symbol} caller`
  - `{changed_symbol} import`
- Contradiction searches:
  - `{changed_symbol} test`
  - `{changed_symbol} fixture`
  - `{changed_symbol} docs`
  - `{changed_symbol} downstream`
- Evidence categories:
  - `changed surface area`
  - `direct consumers`
  - `indirect or downstream consumers`
  - `contracts or API boundaries`
  - `tests`
  - `docs`
- Report sections:
  - `changed surface area`
  - `direct consumers`
  - `supported impacts`
  - `speculative impacts`
  - `missing tests`
  - `safer impact statement`
- Unchecked-area prompts:
  - Were callers and imports checked?
  - Were tests for touched behavior found?
  - Does any claim use only, always, or never without broad searches?
- Evidence categories recorded: `changed surface area`, `docs`, `tests`
- Contradiction passes recorded: 4/4 judged claim(s)

## Measurement
- Claims: 4 (supported=3, too_broad=1)
- Searches run: 10
- Search results: 47 match(es) across 10 matched file(s)
- Evidence read: 11 file read(s), 11 snippet(s), 6 unique evidence file(s)
- Contradiction passes: 4/4 judged claim(s)
- Unsupported or qualified claims caught: 1 (too_broad=1)
- Source-token estimate:
  - Bounded evidence: 3146 estimated token(s)
  - Search previews: 537 estimated token(s)
  - Full cited files baseline: 18838 estimated token(s) (83% reduction from bounded evidence)
  - Full matched files baseline: 24551 estimated token(s) (87% reduction from bounded evidence)
  - Method: estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing

## Impact Claims

### supported: The change adds init and doctor CLI commands for onboarding and readiness checks.
- Type: impact
- Risk: medium
- Budget used: searches=3, files=3, snippets=3, reference_depth=0
- Reasoning: The changed CLI defines init and doctor plus tests for the expected onboarding behavior.
- Limits: This does not prove every MCP client can consume the printed JSON without manual placement.
- Contradiction pass: yes
- Evidence:
  - `plumbref/cli.py:78-110` [changed surface area]: init writes or reuses a config, prints MCP config, prints agent instructions, and suggests next checks.

    ```text
    @app.command()
    def init(
        repo_root: Annotated[Path | None, typer.Option(help="Repository root to initialize.")] = None,
        config_file: Annotated[str, typer.Option(help="Config filename to create under the repo root.")] = ".plumbref.toml",
        force: Annotated[bool, typer.Option(help="Overwrite an existing config file.")] = False,
        print_agent_instructions: Annotated[
            bool,
            typer.Option(help="Print recommended agent instructions after setup."),
        ] = True,
    ) -> None:
        resolved_repo_root = (repo_root or Path.cwd()).expanduser().resolve()
        target_config = resolved_repo_root / config_file
    
        typer.echo(f"Repository: {resolved_repo_root}")
        if target_config.exists() and not force:
            typer.echo(f"Config exists: {target_config}")
        else:
            target_config.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
            typer.echo(f"Wrote config: {target_config}")
    
        typer.echo("")
        typer.echo("MCP config:")
        typer.echo(json.dumps(mcp_config_for_repo(resolved_repo_root), indent=2))
    
        if print_agent_instructions:
            typer.echo("")
            typer.echo("Recommended agent instructions:")
            typer.echo(AGENT_INSTRUCTIONS.strip())
    
        typer.echo("")
        typer.echo("Next checks:")
        typer.echo(f"  plumbref doctor --repo-root {resolved_repo_root}")
        typer.echo(f"  plumbref templates --repo-root {resolved_repo_root}")
    ```
  - `plumbref/cli.py:113-134` [changed surface area]: doctor runs readiness checks and exits non-zero if any check fails.

    ```text
    @app.command()
    def doctor(
        repo_root: Annotated[Path | None, typer.Option(help="Repository root to check.")] = None,
        config: Annotated[Path | None, typer.Option(help="Path to a Plumbref TOML config file.")] = None,
        check_mcp_startup: Annotated[
            bool,
            typer.Option(help="Start the MCP process briefly and confirm it does not exit immediately."),
        ] = False,
    ) -> None:
        resolved_repo_root = (repo_root or Path.cwd()).expanduser().resolve()
        results = run_doctor_checks(
            repo_root=resolved_repo_root,
            config_path=config,
            check_mcp_startup=check_mcp_startup,
        )
        for result in results:
            marker = "ok" if result["ok"] else "fail"
            typer.echo(f"[{marker}] {result['name']}: {result['detail']}")
    
        failures = [result for result in results if not result["ok"]]
        if failures:
            raise typer.Exit(1)
    ```
  - `tests/test_cli_onboarding.py:22-84` [tests]: Tests cover init config output, non-destructive init behavior, and doctor success checks.

    ```text
    def test_init_writes_default_config_and_prints_mcp_json(tmp_path: Path) -> None:
        """Init creates a starter config and prints copy-paste MCP setup."""
        runner = CliRunner()
    
        result = runner.invoke(
            app,
            [
                "init",
                "--repo-root",
                str(tmp_path),
                "--no-print-agent-instructions",
            ],
        )
    
        assert result.exit_code == 0
        assert (tmp_path / ".plumbref.toml").is_file()
        assert "MCP config:" in result.output
        assert '"command": "plumbref"' in result.output
        assert "default_template_id = \"generic_verification\"" in (tmp_path / ".plumbref.toml").read_text(
            encoding="utf-8"
        )
    
    
    def test_init_does_not_overwrite_existing_config_without_force(tmp_path: Path) -> None:
        """Init is non-destructive by default."""
        config = tmp_path / ".plumbref.toml"
        config.write_text('default_budget_mode = "fast"\n', encoding="utf-8")
        runner = CliRunner()
    
        result = runner.invoke(
            app,
            [
                "init",
                "--repo-root",
                str(tmp_path),
                "--no-print-agent-instructions",
            ],
        )
    
        assert result.exit_code == 0
        assert config.read_text(encoding="utf-8") == 'default_budget_mode = "fast"\n'
        assert "Config exists:" in result.output
    
    
    def test_doctor_checks_config_templates_and_report_path(tmp_path: Path) -> None:
        """Doctor reports core local readiness checks."""
        results = run_doctor_checks(repo_root=tmp_path)
    
        names = {str(result["name"]): result for result in results}
        assert names["repo root"]["ok"] is True
        assert names["config"]["ok"] is True
        assert names["templates"]["ok"] is True
        assert names["report path"]["ok"] is True
    
    
    def test_doctor_command_exits_zero_when_required_checks_pass(tmp_path: Path) -> None:
        """Doctor CLI succeeds for a valid repo root and default config."""
        runner = CliRunner()
    
        result = runner.invoke(app, ["doctor", "--repo-root", str(tmp_path)])
    
        assert result.exit_code == 0
        assert "[ok] templates:" in result.output
    ```

### supported: The public setup path now tells users to run plumbref init and plumbref doctor.
- Type: impact
- Risk: medium
- Budget used: searches=2, files=2, snippets=2, reference_depth=0
- Reasoning: README and agent usage docs now present init/doctor as the easiest setup path.
- Limits: The docs still require users to place MCP JSON in their client-specific config.
- Contradiction pass: yes
- Evidence:
  - `README.md:112-183` [docs]: README adds the fast setup path and MCP startup check commands.

    ````text
    Fast setup from a repository checkout:
    
    ```shell
    cd /path/to/repo
    plumbref init
    plumbref doctor
    ```
    
    For agent-specific usage guidance, recommended instructions, and conversational
    examples, see [Agent Usage Guide](docs/agent-usage.md).
    
    For public-demo readiness, honest positioning, and the dogfood demo, see
    [Launch Checklist](docs/launch-checklist.md).
    
    ## Config
    
    Config discovery order:
    
    1. explicit `--config`
    2. `<repo-root>/.plumbref.local.toml`
    3. `<repo-root>/.plumbref.toml`
    4. `~/.config/plumbref/config.toml`
    
    Example:
    
    ```toml
    ignored_paths = [
      ".git",
      ".venv",
      "node_modules",
      ".cache",
    ]
    
    privacy_patterns = [
      "AKIA[0-9A-Z]{16}",
      "(?i)(api[_-]?key|secret|token|password)\\s*[:=]\\s*['\\\"][^'\\\"]+['\\\"]",
    ]
    
    default_budget_mode = "normal"
    default_output_modes = ["engineer", "json"]
    default_template_id = "generic_verification"
    
    template_paths = [
      "plumbref-template-pack",
    ]
    ```
    
    `redaction_patterns` is accepted as an alias for `privacy_patterns`.
    `template_paths` entries are resolved relative to the repository root unless
    they are absolute paths.
    
    ## MCP Setup
    
    The quickest path is to let Plumbref print the repo-specific MCP config and
    agent instructions:
    
    ```shell
    cd /path/to/repo
    plumbref init
    ```
    
    Then verify local readiness:
    
    ```shell
    plumbref doctor
    ```
    
    For an MCP startup check:
    
    ```shell
    plumbref doctor --check-mcp-startup
    ```
    ````
  - `docs/agent-usage.md:36-50` [docs]: Agent usage docs add the init/doctor setup path and explain what each command checks.

    ````text
    plumbref mcp --repo-root /path/to/repo
    ```
    
    The easiest setup path is:
    
    ```shell
    cd /path/to/repo
    plumbref init
    plumbref doctor
    ```
    
    `plumbref init` creates a starter `.plumbref.toml` if one does not already
    exist, prints copy-paste MCP JSON, and prints the recommended agent
    instructions. `plumbref doctor` checks local readiness: repo root, ripgrep,
    config loading, template loading, and report-path writability.
    ````

### supported: Generated reports now include a measurement summary in Markdown and JSON.
- Type: impact
- Risk: medium
- Budget used: searches=2, files=4, snippets=4, reference_depth=0
- Reasoning: Report rendering now adds measurement to both JSON and Markdown, with tests for the section and counts.
- Limits: The measurement is process telemetry, not a quality score.
- Contradiction pass: yes
- Evidence:
  - `plumbref/reports.py:50-76` [changed surface area]: JSON reports include a measurement payload.

    ```text
    def build_json_report(state: SessionState, config: PlumbrefConfig) -> dict[str, Any]:
        status_counts = Counter(claim.status for claim in state.claims.values())
        verdict = overall_verdict(status_counts)
        payload = {
            "session_id": state.session.id,
            "verdict": verdict,
            "mode": state.session.mode,
            "scenario": state.session.scenario,
            "template": state.session.template.model_dump(mode="json") if state.session.template else None,
            "change_context": state.session.change_context.model_dump(mode="json")
            if state.session.change_context
            else None,
            "budget_mode": state.session.budget_mode,
            "measurement": build_measurement_summary(state),
            "claims": [
                {
                    **claim.model_dump(mode="json"),
                    "judgment": state.judgments.get(claim.id).model_dump(mode="json")
                    if claim.id in state.judgments
                    else None,
                }
                for claim in state.claims.values()
            ],
            "evidence": [snippet.model_dump(mode="json") for snippet in state.evidence.values()],
            "trace": [trace.model_dump(mode="json") for trace in state.traces],
        }
        return redact_payload(payload, config.privacy_patterns)
    ```
  - `plumbref/reports.py:99-116` [changed surface area]: Markdown reports include a Measurement section before claim sections.

    ```text
        if state.session.mode == VerificationMode.CHANGE_IMPACT:
            lines.extend(["", "## Change Scope", *format_change_scope(state, config)])
        if state.session.template:
            lines.extend(["", "## Template Checklist", *format_template_checklist(state, config)])
        lines.extend(["", "## Measurement", *format_measurement_summary(payload["measurement"])])
        lines.extend(["", claim_section_heading(state)])
        for claim in claims_for_report(state):
            lines.extend(
                [
                    "",
                    f"### {claim.status.value}: {redact_text(claim.text, config.privacy_patterns)}",
                    f"- Type: {claim.claim_type.value}",
                    f"- Risk: {claim.risk.value}",
                    "- Budget used: "
                    f"searches={claim.usage.searches}, "
                    f"files={claim.usage.files}, "
                    f"snippets={claim.usage.snippets}, "
                    f"reference_depth={claim.usage.reference_depth}",
    ```
  - `plumbref/reports.py:179-230` [changed surface area]: Measurement counts claims, searches, evidence reads, contradiction passes, and unsupported or qualified claims.

    ```text
    def build_measurement_summary(state: SessionState) -> dict[str, Any]:
        status_counts = Counter(claim.status.value for claim in state.claims.values())
        unsupported_statuses = {
            ClaimStatus.CONTRADICTED.value,
            ClaimStatus.TOO_BROAD.value,
            ClaimStatus.UNCERTAIN.value,
            ClaimStatus.NOT_FOUND.value,
            ClaimStatus.NOT_VERIFIABLE.value,
        }
        judged_claims = [claim for claim in state.claims.values() if claim.id in state.judgments]
        contradiction_passes = sum(
            1
            for claim in judged_claims
            if state.judgments[claim.id].contradiction_searched
        )
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
    
    
    def format_measurement_summary(measurement: dict[str, Any]) -> list[str]:
        status_counts = measurement["claim_status_counts"]
        status_text = ", ".join(f"{status}={count}" for status, count in status_counts.items()) or "none"
        return [
            f"- Claims: {measurement['claims_total']} ({status_text})",
            f"- Searches run: {measurement['searches_run']}",
            (
                "- Search results: "
                f"{measurement['search_matches_returned']} match(es) across "
                f"{measurement['matched_files']} matched file(s)"
            ),
            (
                "- Evidence read: "
                f"{measurement['evidence_files_read']} file read(s), "
                f"{measurement['evidence_snippets_read']} snippet(s), "
                f"{measurement['unique_evidence_files']} unique evidence file(s)"
            ),
            (
                "- Contradiction passes: "
                f"{measurement['contradiction_passes']}/{measurement['judged_claims']} judged claim(s)"
            ),
    ```
  - `tests/test_reports.py:61-77` [tests]: Report tests assert the Measurement heading, JSON measurement counts, and safe fenced snippets.

    `````text
        report = render_report(state=state, config=config)
    
        assert report.json_report["verdict"] == "Supported"
        assert "Support-Safe Summary" in report.markdown
        assert "## Measurement" in report.markdown
        assert "```text" in report.markdown
        assert '"reason": "missing provider_id"' in report.markdown
        assert report.json_report["measurement"]["claims_total"] == 1
        assert report.json_report["measurement"]["evidence_snippets_read"] == 1
    
    
    def test_format_excerpt_uses_longer_fence_when_excerpt_contains_backticks() -> None:
        """Markdown evidence snippets remain readable when source contains code fences."""
        lines = format_excerpt("```shell\nplumbref init\n```")
    
        assert lines[1] == "    ````text"
        assert lines[-1] == "    ````"
    `````

### too_broad: Setup is now as simple as it can possibly be for every MCP client.
- Type: impact
- Risk: high
- Budget used: searches=3, files=2, snippets=2, reference_depth=0
- Reasoning: The setup is simpler, but the docs still require manual client-specific config placement. The universal "as simple as possible for every MCP client" claim is not source-verifiable.
- Limits: Safer wording: setup is reduced to init/doctor plus copying the printed MCP config into the user's MCP client.
- Contradiction pass: yes
- Evidence:
  - `docs/agent-usage.md:63-84` [docs]: Docs still say users must put the JSON in the client-specific MCP configuration location and reload the client.

    ````text
    ```
    
    With an explicit config file:
    
    ```json
    {
      "mcpServers": {
        "plumbref": {
          "command": "plumbref",
          "args": [
            "mcp",
            "--repo-root",
            "/path/to/repo",
            "--config",
            "/path/to/repo/.plumbref.toml"
          ]
        }
      }
    }
    ```
    
    The config shape is the same for most MCP clients. Put the JSON in the
    ````
  - `README.md:163-201` [docs]: README provides the fastest path but still shows generic MCP config rather than automatic editor setup.

    ````text
    ## MCP Setup
    
    The quickest path is to let Plumbref print the repo-specific MCP config and
    agent instructions:
    
    ```shell
    cd /path/to/repo
    plumbref init
    ```
    
    Then verify local readiness:
    
    ```shell
    plumbref doctor
    ```
    
    For an MCP startup check:
    
    ```shell
    plumbref doctor --check-mcp-startup
    ```
    
    Plumbref is a stdio MCP server. Any MCP-capable client can launch it with:
    
    ```shell
    plumbref mcp --repo-root /path/to/repo
    ```
    
    Cursor-style MCP config:
    
    ```json
    {
      "mcpServers": {
        "plumbref": {
          "command": "plumbref",
          "args": ["mcp", "--repo-root", "/path/to/repo"]
        }
      }
    }
    ````

## Search Trace
- `def init` matched 1 file(s) in 12ms.
  - Files: `plumbref/cli.py`
  - Matches:
    - `plumbref/cli.py:79`: def init(
- `def doctor` matched 1 file(s) in 14ms.
  - Files: `plumbref/cli.py`
  - Matches:
    - `plumbref/cli.py:114`: def doctor(
- `mcp_config_for_repo` matched 2 file(s) in 14ms.
  - Files: `tests/test_cli_onboarding.py`, `plumbref/cli.py`
  - Matches:
    - `tests/test_cli_onboarding.py:7`: from plumbref.cli import app, mcp_config_for_repo, run_doctor_checks
    - `tests/test_cli_onboarding.py:10`: def test_mcp_config_for_repo_uses_absolute_repo_root(tmp_path: Path) -> None:
    - `tests/test_cli_onboarding.py:12`: config = mcp_config_for_repo(tmp_path)
    - `plumbref/cli.py:100`: typer.echo(json.dumps(mcp_config_for_repo(resolved_repo_root), indent=2))
    - `plumbref/cli.py:257`: def mcp_config_for_repo(repo_root: Path) -> dict[str, object]:
- `plumbref init` matched 6 file(s) in 12ms.
  - Files: `ROADMAP.md`, `README.md`, `docs/agent-usage.md`, `docs/launch-checklist.md`, `tests/test_reports.py`
  - Additional files omitted: 1
  - Matches:
    - `ROADMAP.md:308`: - [x] `plumbref init` to create config and examples.
    - `README.md:116`: plumbref init
    - `README.md:170`: plumbref init
    - `README.md:489`: plumbref init --repo-root /path/to/repo
    - `docs/agent-usage.md:43`: plumbref init
    - Additional matches omitted: 5
- `plumbref doctor` matched 5 file(s) in 13ms.
  - Files: `README.md`, `docs/agent-usage.md`, `docs/launch-checklist.md`, `plumbref/cli.py`, `CHANGELOG.md`
  - Matches:
    - `README.md:117`: plumbref doctor
    - `README.md:176`: plumbref doctor
    - `README.md:182`: plumbref doctor --check-mcp-startup
    - `README.md:495`: plumbref doctor --repo-root /path/to/repo
    - `docs/agent-usage.md:44`: plumbref doctor
    - Additional matches omitted: 5
- `build_measurement_summary` matched 1 file(s) in 17ms.
  - Files: `plumbref/reports.py`
  - Matches:
    - `plumbref/reports.py:63`: "measurement": build_measurement_summary(state),
    - `plumbref/reports.py:179`: def build_measurement_summary(state: SessionState) -> dict[str, Any]:
- `## Measurement` matched 3 file(s) in 13ms.
  - Files: `examples/reports/plumbref-template-loading-demo.md`, `tests/test_reports.py`, `plumbref/reports.py`
  - Matches:
    - `examples/reports/plumbref-template-loading-demo.md:28`: ## Measurement
    - `tests/test_reports.py:65`: assert "## Measurement" in report.markdown
    - `plumbref/reports.py:103`: lines.extend(["", "## Measurement", *format_measurement_summary(payload["measurement"])])
- `MCP client` matched 2 file(s) in 13ms.
  - Files: `README.md`, `docs/agent-usage.md`
  - Matches:
    - `README.md:109`: Then add Plumbref to your MCP client configuration. See [MCP Setup](#mcp-setup)
    - `README.md:223`: Claude Code, Codex, and other MCP clients generally use the same command/args
    - `docs/agent-usage.md:84`: The config shape is the same for most MCP clients. Put the JSON in the
- `client-specific` matched 2 file(s) in 12ms.
  - Files: `README.md`, `docs/agent-usage.md`
  - Matches:
    - `README.md:224`: shape for stdio servers. Use the client-specific location for MCP server
    - `docs/agent-usage.md:85`: client-specific MCP configuration location and restart or reload the client.
- `plumbref init` matched 6 file(s) in 15ms.
  - Files: `ROADMAP.md`, `README.md`, `docs/agent-usage.md`, `docs/launch-checklist.md`, `tests/test_reports.py`
  - Additional files omitted: 1
  - Matches:
    - `ROADMAP.md:308`: - [x] `plumbref init` to create config and examples.
    - `README.md:116`: plumbref init
    - `README.md:170`: plumbref init
    - `README.md:489`: plumbref init --repo-root /path/to/repo
    - `docs/agent-usage.md:43`: plumbref init
    - Additional matches omitted: 5

## Missing / Uncertain Areas
- too_broad: Setup is now as simple as it can possibly be for every MCP client. Limits: Safer wording: setup is reduced to init/doctor plus copying the printed MCP config into the user's MCP client.

## Safer Impact Statement
3 impact claim(s) are directly supported. 1 impact claim(s) need qualification or follow-up.

Supported impact(s):
- The change adds init and doctor CLI commands for onboarding and readiness checks.
- The public setup path now tells users to run plumbref init and plumbref doctor.
- Generated reports now include a measurement summary in Markdown and JSON.

Qualify or avoid:
- too_broad: Setup is now as simple as it can possibly be for every MCP client. Safer wording: Safer wording: setup is reduced to init/doctor plus copying the printed MCP config into the user's MCP client.
