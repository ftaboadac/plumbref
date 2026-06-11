from __future__ import annotations

import tomllib
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path

from pydantic import ValidationError

from plumbref.config import PlumbrefConfig, load_config
from plumbref.models import VerificationTemplate


class TemplateLoadError(ValueError):
    pass


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


def get_template(
    template_id: str,
    *,
    repo_root: Path,
    config: PlumbrefConfig | None = None,
) -> VerificationTemplate:
    templates = load_templates(repo_root, config)
    if template_id not in templates:
        available = ", ".join(sorted(templates)) or "none"
        raise TemplateLoadError(f"unknown template {template_id!r}; available templates: {available}")
    return templates[template_id]


def load_builtin_templates() -> list[VerificationTemplate]:
    template_root = files("plumbref").joinpath("templates")
    return [
        parse_template_text(path.read_text(encoding="utf-8"), source=f"builtin:{path.name}")
        for path in sorted(template_root.iterdir(), key=lambda item: item.name)
        if path.name.endswith(".toml")
    ]


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


def load_template_file(path: Path) -> VerificationTemplate:
    return parse_template_text(path.read_text(encoding="utf-8"), source=str(path))


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


def summarize_templates(templates: Iterable[VerificationTemplate]) -> list[dict[str, str]]:
    return [
        {
            "id": template.id,
            "version": template.version,
            "name": template.name,
            "description": template.description,
            "source": template.source,
        }
        for template in sorted(templates, key=lambda item: item.id)
    ]
