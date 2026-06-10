from __future__ import annotations

import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

from groundcheck.models import BudgetMode, OutputMode


class ConfigLoadError(ValueError):
    pass


class GroundcheckConfig(BaseModel):
    ignored_paths: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".venv",
            "node_modules",
            "frontend/.next",
            ".cache",
        ],
    )
    docs_paths: list[str] = Field(default_factory=lambda: ["docs"])
    cache_path: Path = Path(".cache/groundcheck")
    report_path: Path = Path(".cache/groundcheck/reports")
    privacy_patterns: list[str] = Field(
        default_factory=lambda: [
            r"AKIA[0-9A-Z]{16}",
            r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+['\"]",
        ],
    )
    default_budget_mode: BudgetMode = BudgetMode.NORMAL
    default_output_modes: list[OutputMode] = Field(default_factory=lambda: [OutputMode.ENGINEER])

    @field_validator("cache_path", "report_path")
    @classmethod
    def expand_paths(cls, value: Path) -> Path:
        return value.expanduser()

    @field_validator("privacy_patterns")
    @classmethod
    def validate_privacy_patterns(cls, values: list[str]) -> list[str]:
        for pattern in values:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"invalid privacy pattern {pattern!r}: {exc}") from exc
        return values


def load_config(repo_root: Path, config_path: Path | None = None) -> GroundcheckConfig:
    resolved_repo_root = repo_root.expanduser().resolve()
    discovered = discover_config_path(resolved_repo_root, config_path)
    payload = load_config_payload(discovered) if discovered else {}
    config = build_config(payload)
    config.cache_path = resolve_config_path(resolved_repo_root, config.cache_path)
    config.report_path = resolve_config_path(resolved_repo_root, config.report_path)
    return config


def discover_config_path(repo_root: Path, explicit_config: Path | None = None) -> Path | None:
    if explicit_config:
        path = explicit_config.expanduser().resolve()
        if not path.is_file():
            raise ConfigLoadError(f"config file does not exist: {path}")
        return path

    candidates = [
        repo_root / ".groundcheck.local.toml",
        repo_root / ".groundcheck.toml",
        Path.home() / ".config" / "groundcheck" / "config.toml",
    ]
    return next((path for path in candidates if path.is_file()), None)


def load_config_payload(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as file:
            loaded = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigLoadError(f"could not parse config file {path}: {exc}") from exc

    payload = loaded.get("groundcheck", loaded)
    if not isinstance(payload, dict):
        raise ConfigLoadError(f"config file {path} must contain a TOML table")
    return normalize_config_payload(payload)


def normalize_config_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    if "redaction_patterns" in normalized and "privacy_patterns" not in normalized:
        normalized["privacy_patterns"] = normalized.pop("redaction_patterns")
    return normalized


def build_config(payload: dict[str, object]) -> GroundcheckConfig:
    try:
        return GroundcheckConfig.model_validate(payload)
    except ValidationError as exc:
        raise ConfigLoadError(f"invalid Groundcheck config: {exc}") from exc


def resolve_config_path(repo_root: Path, path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded.resolve()
    return (repo_root / expanded).resolve()
