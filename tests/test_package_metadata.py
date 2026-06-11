from __future__ import annotations

import tomllib
from pathlib import Path

from plumbref import __version__


def test_package_version_matches_project_metadata() -> None:
    """Runtime package version stays aligned with build metadata."""
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ == project["project"]["version"]
