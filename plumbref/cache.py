from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def stable_cache_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_state_fingerprint(repo_root: Path, ignored_paths: list[str]) -> str:
    payload: list[dict[str, Any]] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or should_ignore_path(repo_root, path, ignored_paths):
            continue
        try:
            stat = path.stat()
            relative_path = path.relative_to(repo_root).as_posix()
        except OSError:
            continue
        payload.append(
            {
                "path": relative_path,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    return stable_cache_key({"files": payload})


def should_ignore_path(repo_root: Path, path: Path, ignored_paths: list[str]) -> bool:
    try:
        relative_parts = path.relative_to(repo_root).parts
    except ValueError:
        return True
    for ignored_path in ignored_paths:
        ignored_parts = Path(ignored_path).parts
        if relative_parts[: len(ignored_parts)] == ignored_parts:
            return True
    return False
