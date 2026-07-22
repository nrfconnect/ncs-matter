"""
Copyright (c) 2026 Nordic Semiconductor ASA

SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

Shared YAML loading for memory visualization Sphinx extensions.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from sphinx.util.docutils import SphinxDirective

__version__ = "0.1.0"


def load_memory_yaml(directive: SphinxDirective, relative_file: str) -> dict[str, Any]:
    """Load a YAML file relative to the current RST document directory."""
    source_dir = Path(directive.env.doc2path(directive.env.docname)).parent
    path = (source_dir / relative_file).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Memory data file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def plain_tab_label(tab_title: str) -> str:
    """Return plain text for Sphinx ``.. tab::`` titles (no RST links)."""
    title = tab_title.strip()
    match = re.search(r":zephyr:board:`([^`]+)`", title)
    if match:
        board_name = match.group(1)
        suffix = title[match.end() :].strip()
        return f"{board_name} {suffix}".strip() if suffix else board_name
    ref_match = re.search(r":ref:`([^<`]+)(?:<[^>]+>)?`(?:\s*\(([^)]+)\))?", title)
    if ref_match:
        name = ref_match.group(1).strip()
        variant = ref_match.group(2)
        return f"{name} ({variant})" if variant else name
    if title.startswith(":ref:`") and title.endswith("`"):
        inner = title[len(":ref:`") : -1]
        return inner.split("<")[0].strip()
    return title


def sample_title(sample: dict[str, Any]) -> str:
    """Return the RST sample label from a YAML sample entry."""
    return str(sample.get("title") or sample.get("plain_title") or "")


INTERNAL_NVM_COLUMNS: tuple[tuple[str, str, bool], ...] = (
    ("boot", "MCUboot (used / free)", True),
    ("slot0", "Application (used / free)", True),
    ("factory_data", "Factory data", False),
    ("storage", "Settings", False),
)

EXTERNAL_NVM_COLUMNS: tuple[tuple[str, str], ...] = (("slot1", "Application DFU (used / free)"),)

RAM_SUBHEAD = "used / free"
EMPTY_CELL = "--"


def _fmt_kb(value: int | float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def _used_free(used_kb: float, total_kb: float | None) -> str:
    if total_kb is None:
        return _fmt_kb(used_kb)
    free = max(float(total_kb) - float(used_kb), 0)
    return f"{_fmt_kb(used_kb)} / {_fmt_kb(free)}"


def board_has_external_nvm(board: dict[str, Any]) -> bool:
    for sample in board.get("samples") or []:
        external_parts = sample.get("external_nvm_partitions") or []
        if any(part.get("id") == "slot1" for part in external_parts):
            return True
    return False


def _partition_maps(sample: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    internal = {part["id"]: part for part in sample.get("nvm_partitions") or []}
    external = {
        part["id"]: part
        for part in sample.get("external_nvm_partitions") or []
        if part.get("id") != "padding"
    }
    return internal, external


def sample_table_cells(
    sample: dict[str, Any],
    *,
    include_external: bool,
    ram_total_kb: float | None,
) -> list[str]:
    internal_parts, external_parts = _partition_maps(sample)
    cells: list[str] = []

    for part_id, _, used_free in INTERNAL_NVM_COLUMNS:
        part = internal_parts.get(part_id)
        if part is None:
            cells.append(EMPTY_CELL)
            continue
        size_kb = float(part.get("size_kb") or 0)
        used_kb = float(part.get("used_kb", size_kb))
        if used_free:
            cells.append(_used_free(used_kb, size_kb))
        else:
            cells.append(_fmt_kb(size_kb))

    if include_external:
        for part_id, _ in EXTERNAL_NVM_COLUMNS:
            part = external_parts.get(part_id)
            if part is None:
                cells.append(EMPTY_CELL)
                continue
            size_kb = float(part.get("size_kb") or 0)
            used_kb = float(part.get("used_kb", 0))
            cells.append(_used_free(used_kb, size_kb))

    ram_used_kb = float(sample.get("ram_used_kb") or 0)
    cells.append(_used_free(ram_used_kb, float(ram_total_kb) if ram_total_kb is not None else None))
    return cells


def _header_label(board: dict[str, Any], kind: str) -> str:
    if kind == "nvm":
        total = board.get("nvm_total_kb")
        return f"Internal NVM ({_fmt_kb(float(total))} kB)" if total is not None else "Internal NVM"
    if kind == "external":
        for sample in board.get("samples") or []:
            total = sample.get("external_nvm_total_kb")
            if total:
                return f"External NVM ({_fmt_kb(float(total))} kB)"
        return "External NVM"
    total = board.get("ram_total_kb")
    return f"RAM ({_fmt_kb(float(total))} kB)" if total is not None else "RAM"


def internal_nvm_bytes(board: dict[str, Any]) -> int:
    """Return on-chip NVM capacity in bytes for a YAML board entry."""
    for region in board.get("regions") or []:
        if region.get("id") == "flash_primary":
            return int(region.get("total_bytes") or 0)

    board_nvm_kb = board.get("nvm_total_kb")
    if board_nvm_kb:
        return int(float(board_nvm_kb) * 1024)

    samples = board.get("samples") or []
    if samples:
        return int(max(float(sample.get("nvm_total_kb") or 0) for sample in samples) * 1024)

    return 0


def sort_boards_by_internal_memory(boards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return boards sorted from smallest to largest internal NVM."""
    return sorted(
        boards,
        key=lambda board: (internal_nvm_bytes(board), str(board.get("board_id") or "")),
    )
