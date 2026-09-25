"""
Copyright (c) 2026 Nordic Semiconductor ASA

SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

Expose west manifest revisions as Sphinx substitutions for documentation links.

Reads the Matter (sdk-connectedhomeip) revision from west.yml and registers
|sdk-connectedhomeip-revision| for use in links.txt and RST sources.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.1.0"

MATTER_WEST_PROJECT = "matter"
SDK_CONNECTEDHOMEIP_REVISION = "sdk-connectedhomeip-revision"


def _load_west_manifest(west_manifest: Path) -> dict[str, Any]:
    if not west_manifest.is_file():
        raise FileNotFoundError(f"west manifest not found: {west_manifest}")
    data = yaml.safe_load(west_manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid west manifest: {west_manifest}")
    return data


def _matter_project(manifest: dict[str, Any]) -> dict[str, Any]:
    projects = manifest.get("manifest", {}).get("projects", [])
    if not isinstance(projects, list):
        raise ValueError("west manifest has no projects list")

    for project in projects:
        if isinstance(project, dict) and project.get("name") == MATTER_WEST_PROJECT:
            return project

    raise ValueError(f"west manifest has no project named {MATTER_WEST_PROJECT!r}")


def _git_short_revision(matter_module: Path, revision: str) -> str | None:
    if not matter_module.is_dir():
        return None

    for ref in (revision, "HEAD"):
        proc = subprocess.run(
            ["git", "-C", str(matter_module), "rev-parse", "--short", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            short_sha = proc.stdout.strip()
            if short_sha:
                return short_sha
    return None


def connectedhomeip_revision(
    west_manifest: Path,
    *,
    matter_module: Path | None = None,
) -> str:
    """Return the sdk-connectedhomeip revision string for documentation links."""
    project = _matter_project(_load_west_manifest(west_manifest))
    revision = str(project.get("revision", "")).strip()
    if not revision:
        raise ValueError(
            f"Project {MATTER_WEST_PROJECT!r} in {west_manifest} has no revision"
        )

    if matter_module is not None:
        short_sha = _git_short_revision(matter_module, revision)
        if short_sha:
            return short_sha

    return revision


def load_west_substitutions(
    west_manifest: Path,
    *,
    matter_module: Path | None = None,
) -> dict[str, str]:
    """Build substitution mapping from west.yml for conf.py preprocessing."""
    return {
        SDK_CONNECTEDHOMEIP_REVISION: connectedhomeip_revision(
            west_manifest,
            matter_module=matter_module,
        ),
    }


def _config_inited(app, config) -> None:
    west_manifest = Path(config.west_manifest_path)
    matter_module = Path(config.matter_module_path) if config.matter_module_path else None
    substitutions = load_west_substitutions(west_manifest, matter_module=matter_module)

    prolog_lines = [
        f".. |{name}| replace:: {value}" for name, value in substitutions.items()
    ]
    existing_prolog = config.rst_prolog or ""
    if existing_prolog and not existing_prolog.endswith("\n"):
        existing_prolog = f"{existing_prolog}\n"
    config.rst_prolog = "\n".join(prolog_lines) + "\n" + existing_prolog


def setup(app):
    app.add_config_value("west_manifest_path", None, "env", [str])
    app.add_config_value("matter_module_path", None, "env", [str])
    app.connect("config-inited", _config_inited)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
