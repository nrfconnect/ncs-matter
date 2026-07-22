"""
Copyright (c) 2026 Nordic Semiconductor ASA

SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

Sphinx extension for Matter sample memory requirement tables.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from memory_data import (
    EMPTY_CELL,
    EXTERNAL_NVM_COLUMNS,
    INTERNAL_NVM_COLUMNS,
    RAM_SUBHEAD,
    _header_label,
    board_has_external_nvm,
    load_memory_yaml,
    plain_tab_label,
    sample_table_cells,
    sample_title,
    sort_boards_by_internal_memory,
)
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

__version__ = "0.1.0"

RESOURCES_DIR = Path(__file__).parent / "static"
ENV_BOARD_KEY = "matter_memory_table_boards"


def _append_rst_cell(state, entry: nodes.entry, rst_text: str) -> None:
    paragraph = nodes.paragraph()
    content = StringList([rst_text], "<memory_table>")
    state.nested_parse(content, 0, paragraph)
    if len(paragraph) == 1 and isinstance(paragraph[0], nodes.paragraph):
        inner = paragraph[0]
        paragraph.remove(inner)
        paragraph.extend(inner.children)
    entry += paragraph


def _append_text_cell(row: nodes.row, text: str, *, css_class: str = "memory-req-value") -> None:
    entry = nodes.entry()
    entry["classes"] = [css_class]
    entry += nodes.Text(text)
    row += entry


def build_memory_table_nodes(directive: SphinxDirective, board: dict[str, Any]) -> nodes.table:
    include_external = board_has_external_nvm(board)
    internal_count = len(INTERNAL_NVM_COLUMNS)
    external_count = len(EXTERNAL_NVM_COLUMNS) if include_external else 0
    total_cols = 1 + internal_count + external_count + 1

    table = nodes.table()
    table["classes"] = ["memory-req-table"]

    tgroup = nodes.tgroup(cols=total_cols)
    table += tgroup
    tgroup.extend([nodes.colspec(colwidth=28)] + [nodes.colspec(colwidth=10)] * (total_cols - 1))

    thead = nodes.thead()
    tgroup += thead

    group_row = nodes.row()
    thead += group_row

    sample_group = nodes.entry()
    sample_group["morerows"] = 1
    sample_group += nodes.Text("Sample")
    group_row += sample_group

    nvm_group = nodes.entry()
    nvm_group["morecols"] = internal_count - 1
    nvm_group["classes"] = ["memory-req-group-nvm"]
    nvm_group += nodes.Text(_header_label(board, "nvm"))
    group_row += nvm_group

    if include_external:
        external_group = nodes.entry()
        if external_count > 1:
            external_group["morecols"] = external_count - 1
        else:
            external_group["morerows"] = 1
        external_group["classes"] = ["memory-req-group-external"]
        external_group += nodes.Text(_header_label(board, "external"))
        group_row += external_group

    ram_group = nodes.entry()
    ram_group["classes"] = ["memory-req-group-ram"]
    ram_group += nodes.Text(_header_label(board, "ram"))
    group_row += ram_group

    sub_row = nodes.row()
    thead += sub_row

    for _, label, _ in INTERNAL_NVM_COLUMNS:
        entry = nodes.entry()
        entry["classes"] = ["memory-req-subhead"]
        entry += nodes.Text(label)
        sub_row += entry

    for _, label in EXTERNAL_NVM_COLUMNS:
        entry = nodes.entry()
        entry["classes"] = ["memory-req-subhead"]
        entry += nodes.Text(label)
        sub_row += entry

    ram_sub = nodes.entry()
    ram_sub["classes"] = ["memory-req-subhead"]
    ram_sub += nodes.Text(RAM_SUBHEAD)
    sub_row += ram_sub

    tbody = nodes.tbody()
    tgroup += tbody

    ram_total_kb = board.get("ram_total_kb")
    for sample in board.get("samples") or []:
        row = nodes.row()
        tbody += row

        sample_entry = nodes.entry()
        sample_entry["classes"] = ["memory-req-sample"]
        _append_rst_cell(directive.state, sample_entry, sample_title(sample))
        row += sample_entry

        cells = sample_table_cells(
            sample,
            include_external=include_external,
            ram_total_kb=float(ram_total_kb) if ram_total_kb is not None else None,
        )
        for value in cells:
            css = "memory-req-empty" if value == EMPTY_CELL else "memory-req-value"
            _append_text_cell(row, value, css_class=css)

    return table


class MemoryTableBoard(SphinxDirective):
    """Render one board table (used inside generated board tabs)."""

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False
    option_spec = {
        "board-id": directives.unchanged_required,
    }

    def run(self) -> list[nodes.Node]:
        boards = getattr(self.env, ENV_BOARD_KEY, {})
        board = boards.get(self.options["board-id"])
        if board is None:
            return []
        return [build_memory_table_nodes(self, board)]


def _table_tab_intro(board: dict[str, Any]) -> str:
    return board.get("tab_intro_rst", "")


def _build_table_tabs_rst(
    directive: SphinxDirective,
    boards: list[dict[str, Any]],
) -> list[nodes.Node]:
    if not boards:
        note = nodes.paragraph()
        note += nodes.emphasis(text="No memory usage data found.")
        return [note]

    setattr(
        directive.env,
        ENV_BOARD_KEY,
        {str(board["board_id"]): board for board in boards},
    )

    lines = [".. tabs::", ""]
    for board in boards:
        lines.append(f"   .. group-tab:: {plain_tab_label(board['tab_title'])}")
        lines.append("")
        for intro_line in _table_tab_intro(board).splitlines():
            lines.append(f"      {intro_line}")
        lines.append("")
        lines.append(f"      .. memory-table-board::")
        lines.append(f"         :board-id: {board['board_id']}")
        lines.append("")

    container = nodes.container()
    directive.state.nested_parse(StringList(lines, "<memory_table>"), 0, container)
    return container.children


class MemoryTable(SphinxDirective):
    """Render memory requirements tables from a YAML data file."""

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False
    option_spec = {
        "file": directives.unchanged_required,
    }

    def run(self) -> list[nodes.Node]:
        data = load_memory_yaml(self, self.options["file"])
        return _build_table_tabs_rst(
            self,
            sort_boards_by_internal_memory(data.get("boards", [])),
        )


def add_memory_table_resources(app: Sphinx) -> None:
    static_path = RESOURCES_DIR.as_posix()
    if static_path not in app.config.html_static_path:
        app.config.html_static_path.append(static_path)
    app.add_css_file("memory_table.css")


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("memory-table", MemoryTable)
    app.add_directive("memory-table-board", MemoryTableBoard)
    app.connect("builder-inited", add_memory_table_resources)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
