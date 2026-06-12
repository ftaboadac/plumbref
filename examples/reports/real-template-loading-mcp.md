# Plumbref Report

Verdict: Contradicted claims found
Verification mode: explanation
Budget mode: normal
Template: Explain flow (`explain_flow` v1.0)

## Template Checklist
- Source: builtin:explain_flow.toml
- Required claim types: `definition`, `behavior`, `api`, `business_rule`
- Required searches:
  - `{flow_name}`
  - `{entry_point}`
  - `{main_entity}`
  - `{external_system}`
- Contradiction searches:
  - `{flow_name} test`
  - `{flow_name} error`
  - `{entry_point} disabled`
  - `{external_system} mock`
- Evidence categories:
  - `entry point`
  - `main implementation path`
  - `data inputs`
  - `data outputs`
  - `external calls`
  - `failure handling`
  - `tests`
  - `docs`
- Report sections:
  - `short flow summary`
  - `source-backed path`
  - `inputs and outputs`
  - `failure modes`
  - `open uncertainties`
  - `files worth reading next`
- Unchecked-area prompts:
  - Did the search find the entry point?
  - Were failure and retry paths checked?
  - Were tests or docs found for this flow?
- Evidence categories recorded: `data inputs`, `docs`, `failure handling`, `main implementation path`, `tests`
- Contradiction passes recorded: 4/4 judged claim(s)

## Measurement
- Claims: 4 (contradicted=1, supported=3)
- Searches run: 10
- Search results: 70 match(es) across 10 matched file(s)
- Evidence read: 8 file read(s), 8 snippet(s), 3 unique evidence file(s)
- Contradiction passes: 4/4 judged claim(s)
- Unsupported or qualified claims caught: 1 (too_broad=0)
- Source-token estimate:
  - Bounded evidence: 1029 estimated token(s)
  - Search previews: 1562 estimated token(s)
  - Full cited files baseline: 5653 estimated token(s) (82% reduction from bounded evidence)
  - Full matched files baseline: 52640 estimated token(s) (98% reduction from bounded evidence)
  - Method: estimated_tokens = ceil(characters / 4); source-text comparison only, not provider billing

## Claims

### supported: Plumbref loads built-in template TOML files from the packaged plumbref/templates directory.
- Type: definition
- Risk: medium
- Budget used: searches=2, files=1, snippets=1, reference_depth=0
- Reasoning: The implementation uses importlib.resources.files("plumbref").joinpath("templates") and parses sorted .toml files.
- Limits: This verifies local package loading, not packaging metadata in built wheels.
- Contradiction pass: yes
- Evidence:
  - `plumbref/template_registry.py:46-52` [main implementation path]: Built-ins are read from the packaged plumbref/templates resource and only .toml files are parsed.

    ```text
    def load_builtin_templates() -> list[VerificationTemplate]:
        template_root = files("plumbref").joinpath("templates")
        return [
            parse_template_text(path.read_text(encoding="utf-8"), source=f"builtin:{path.name}")
            for path in sorted(template_root.iterdir(), key=lambda item: item.name)
            if path.name.endswith(".toml")
        ]
    ```

### supported: After built-ins, Plumbref loads user templates, repo-local templates, and configured template_paths; later templates with the same id override earlier templates.
- Type: behavior
- Risk: medium
- Budget used: searches=3, files=3, snippets=3, reference_depth=0
- Reasoning: Code and docs agree: built-ins are loaded first, then user/repo/configured directories overwrite by template id.
- Limits: The report did not create a custom template on disk; existing tests cover that behavior separately.
- Contradiction pass: yes
- Evidence:
  - `plumbref/template_registry.py:18-30` [main implementation path]: The templates dict is first populated with built-ins, then overwritten by templates from configured directories.

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
  - `plumbref/template_registry.py:55-61` [data inputs]: Template directories are user config, repo-local .plumbref/templates, and config.template_paths.

    ```text
    def template_directories(repo_root: Path, config: PlumbrefConfig) -> list[Path]:
        directories = [
            Path.home() / ".config" / "plumbref" / "templates",
            repo_root / ".plumbref" / "templates",
            *config.template_paths,
        ]
        return [directory.expanduser().resolve() for directory in directories if directory.expanduser().is_dir()]
    ```
  - `README.md:313-322` [docs]: Public docs describe the same order and say later sources can override earlier templates.

    ```text
    Shared template packs can live anywhere and be referenced with `template_paths`
    in `.plumbref.toml`. Plumbref loads templates in this order:
    
    1. built-in templates
    2. user templates from `~/.config/plumbref/templates`
    3. repo-local templates from `.plumbref/templates`
    4. configured `template_paths`
    
    Later sources can override earlier templates with the same ID. This lets a team
    adapt a built-in playbook without forking Plumbref.
    ```

### supported: Invalid custom template TOML fails with TemplateLoadError instead of being silently accepted.
- Type: behavior
- Risk: medium
- Budget used: searches=2, files=2, snippets=2, reference_depth=0
- Reasoning: The parser raises TemplateLoadError for TOML parse, non-table payload, and validation failures; tests exercise invalid custom templates.
- Limits: This verifies validation failures in template loading, not every possible semantic mistake a template author could make.
- Contradiction pass: yes
- Evidence:
  - `plumbref/template_registry.py:76-91` [failure handling]: Template TOML parse failures and Pydantic validation failures are converted to TemplateLoadError.

    ```text
    def parse_template_text(text: str, *, source: str) -> VerificationTemplate:
        try:
            payload = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise TemplateLoadError(f"could not parse template {source}: {exc}") from exc
    
        template_payload = payload.get("template", payload)
        if not isinstance(template_payload, dict):
            raise TemplateLoadError(f"template {source} must contain a TOML table")
        template_payload = dict(template_payload)
        template_payload["source"] = source
    
        try:
            return VerificationTemplate.model_validate(template_payload)
        except ValidationError as exc:
            raise TemplateLoadError(f"invalid template {source}: {exc}") from exc
    ```
  - `tests/test_templates.py:80-95` [tests]: A test asserts invalid custom templates raise TemplateLoadError.

    ```text
    def test_invalid_custom_template_fails_validation(tmp_path: Path) -> None:
        """Invalid template files fail fast instead of becoming ambiguous prompts."""
        template_dir = tmp_path / ".plumbref" / "templates"
        template_dir.mkdir(parents=True)
        (template_dir / "bad.toml").write_text(
            """
    id = "Bad Template"
    version = "1.0"
    name = "Bad"
    description = "Invalid ID."
    """.strip(),
            encoding="utf-8",
        )
    
        with pytest.raises(TemplateLoadError):
            load_templates(tmp_path)
    ```

### contradicted: Plumbref automatically downloads templates from a remote marketplace.
- Type: behavior
- Risk: high
- Budget used: searches=3, files=2, snippets=2, reference_depth=0
- Reasoning: The implementation and docs describe local filesystem template loading only; searches did not find marketplace or download behavior.
- Limits: A separate future project could add a marketplace, but this code does not currently do that.
- Contradiction pass: yes
- Evidence:
  - `plumbref/template_registry.py:55-69` [main implementation path]: The loader only checks local user, repo-local, and configured directories for .toml files.

    ```text
    def template_directories(repo_root: Path, config: PlumbrefConfig) -> list[Path]:
        directories = [
            Path.home() / ".config" / "plumbref" / "templates",
            repo_root / ".plumbref" / "templates",
            *config.template_paths,
        ]
        return [directory.expanduser().resolve() for directory in directories if directory.expanduser().is_dir()]
    
    
    def load_templates_from_directory(directory: Path) -> list[VerificationTemplate]:
        return [
            load_template_file(path)
            for path in sorted(directory.glob("*.toml"))
            if path.is_file()
        ]
    ```
  - `README.md:302-322` [docs]: Docs describe custom templates as local repo or shared template-pack directories, not a remote marketplace.

    ````text
    If no built-in template fits, use `generic_verification` or add a custom
    template.
    
    ### Custom Templates
    
    Repo-local templates live in:
    
    ```text
    .plumbref/templates/
    ```
    
    Shared template packs can live anywhere and be referenced with `template_paths`
    in `.plumbref.toml`. Plumbref loads templates in this order:
    
    1. built-in templates
    2. user templates from `~/.config/plumbref/templates`
    3. repo-local templates from `.plumbref/templates`
    4. configured `template_paths`
    
    Later sources can override earlier templates with the same ID. This lets a team
    adapt a built-in playbook without forking Plumbref.
    ````

## Search Trace
- `load_builtin_templates` matched 2 file(s) in 20ms.
  - Files: `examples/reports/plumbref-template-loading-demo.md`, `plumbref/template_registry.py`
  - Matches:
    - `examples/reports/plumbref-template-loading-demo.md:56`: for template in load_builtin_templates():
    - `examples/reports/plumbref-template-loading-demo.md:78`: for template in load_builtin_templates():
    - `plumbref/template_registry.py:23`: for template in load_builtin_templates():
    - `plumbref/template_registry.py:46`: def load_builtin_templates() -> list[VerificationTemplate]:
- `plumbref/templates` matched 4 file(s) in 15ms.
  - Files: `examples/reports/plumbref-template-loading-demo.md`, `README.md`, `docs/agent-usage.md`, `tests/test_templates.py`
  - Matches:
    - `examples/reports/plumbref-template-loading-demo.md:107`: assert template.source.endswith(".plumbref/templates/change_impact.toml")
    - `README.md:310`: .plumbref/templates/
    - `README.md:317`: 2. user templates from `~/.config/plumbref/templates`
    - `README.md:318`: 3. repo-local templates from `.plumbref/templates`
    - `docs/agent-usage.md:141`: Custom templates can live in `.plumbref/templates/`, in
    - Additional matches omitted: 2
- `template_directories` matched 2 file(s) in 14ms.
  - Files: `examples/reports/plumbref-template-loading-demo.md`, `plumbref/template_registry.py`
  - Matches:
    - `examples/reports/plumbref-template-loading-demo.md:59`: for directory in template_directories(resolved_repo_root, resolved_config):
    - `examples/reports/plumbref-template-loading-demo.md:81`: for directory in template_directories(resolved_repo_root, resolved_config):
    - `examples/reports/plumbref-template-loading-demo.md:152`: - `load_templates template_directories` matched source and tests covering registry order.
    - `plumbref/template_registry.py:26`: for directory in template_directories(resolved_repo_root, resolved_config):
    - `plumbref/template_registry.py:55`: def template_directories(repo_root: Path, config: PlumbrefConfig) -> list[Path]:
- `template_paths` matched 5 file(s) in 13ms.
  - Files: `README.md`, `docs/agent-usage.md`, `tests/test_templates.py`, `plumbref/template_registry.py`, `plumbref/config.py`
  - Matches:
    - `README.md:154`: template_paths = [
    - `README.md:160`: `template_paths` entries are resolved relative to the repository root unless
    - `README.md:313`: Shared template packs can live anywhere and be referenced with `template_paths`
    - `README.md:319`: 4. configured `template_paths`
    - `docs/agent-usage.md:143`: in `template_paths`.
    - Additional matches omitted: 4
- `Later sources can override` matched 1 file(s) in 11ms.
  - Files: `README.md`
  - Matches:
    - `README.md:321`: Later sources can override earlier templates with the same ID. This lets a team
- `TemplateLoadError` matched 4 file(s) in 12ms.
  - Files: `tests/test_templates.py`, `plumbref/template_registry.py`, `plumbref/cli.py`, `plumbref/sessions.py`
  - Matches:
    - `tests/test_templates.py:11`: from plumbref.template_registry import TemplateLoadError, get_template, load_templates
    - `tests/test_templates.py:94`: with pytest.raises(TemplateLoadError):
    - `tests/test_templates.py:122`: with pytest.raises(TemplateLoadError):
    - `plumbref/template_registry.py:14`: class TemplateLoadError(ValueError):
    - `plumbref/template_registry.py:42`: raise TemplateLoadError(f"unknown template {template_id!r}; available templates: {available}")
    - Additional matches omitted: 9
- `invalid template` matched 1 file(s) in 14ms.
  - Files: `plumbref/template_registry.py`
  - Matches:
    - `plumbref/template_registry.py:91`: raise TemplateLoadError(f"invalid template {source}: {exc}") from exc
- `marketplace` matched 0 file(s) in 17ms.
- `http` matched 3 file(s) in 11ms.
  - Files: `README.md`, `pyproject.toml`, `uv.lock`
  - Matches:
    - `README.md:1`: # [Plumbref](https://plumbref.vercel.app)
    - `README.md:92`: pipx install git+https://github.com/ftaboadac/plumbref.git
    - `pyproject.toml:45`: Homepage = "https://github.com/ftaboadac/plumbref"
    - `pyproject.toml:46`: Repository = "https://github.com/ftaboadac/plumbref"
    - `pyproject.toml:47`: Issues = "https://github.com/ftaboadac/plumbref/issues"
    - Additional matches omitted: 15
- `template_paths` matched 5 file(s) in 10ms.
  - Files: `README.md`, `docs/agent-usage.md`, `tests/test_templates.py`, `plumbref/template_registry.py`, `plumbref/config.py`
  - Matches:
    - `README.md:154`: template_paths = [
    - `README.md:160`: `template_paths` entries are resolved relative to the repository root unless
    - `README.md:313`: Shared template packs can live anywhere and be referenced with `template_paths`
    - `README.md:319`: 4. configured `template_paths`
    - `docs/agent-usage.md:143`: in `template_paths`.
    - Additional matches omitted: 4
