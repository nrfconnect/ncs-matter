"""
Copyright (c) 2026 Nordic Semiconductor ASA

SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

Sphinx extension for sample memory bar charts.

"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from memory_data import load_memory_yaml, plain_tab_label, sample_title, sort_boards_by_internal_memory
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

__version__ = "0.1.0"

RESOURCES_DIR = Path(__file__).parent / "static"
ENV_BOARD_KEY = "matter_memory_usage_boards"

PARTITION_COLORS = {
    "boot": ("#2563eb", "#93c5fd"),
    "slot0": ("#16a34a", "#bbf7d0"),
    "slot1": ("#0369a1", "#7dd3fc"),
    "tfm": ("#7c3aed", "#ddd6fe"),
    "factory_data": ("#ea580c", "#fed7aa"),
    "storage": ("#ca8a04", "#fde68a"),
    "tfm_storage": ("#0d9488", "#99f6e4"),
    "padding": ("#94a3b8", "#e2e8f0"),
    "ram": ("#0891b2", "#a5f3fc"),
    "unused": ("#e2e8f0", "#f8fafc"),
}

SPLIT_USAGE_IDS = frozenset({"boot", "slot0", "slot1", "ram"})
ALWAYS_VISIBLE_BAR_IDS = frozenset(
    {"boot", "tfm", "slot0", "slot1", "factory_data", "storage", "tfm_storage", "padding"}
)
NVM_LEGEND_ORDER = (
    "boot",
    "tfm",
    "slot0",
    "factory_data",
    "storage",
    "tfm_storage",
)
EXTERNAL_NVM_LEGEND_ORDER = (
    "slot1",
    "padding",
)
TOOLTIP_ALIGN_START_THRESHOLD_PCT = 20.0


def _kb_label(kb: float) -> str:
    if kb == int(kb):
        return f"{int(kb)} kB"
    return f"{kb:.1f} kB"


def _legend_threshold(data: dict[str, Any]) -> float:
    return float(data.get("legend_threshold_kb", 8))


def _partition_colors(part_id: str) -> tuple[str, str]:
    return PARTITION_COLORS.get(part_id, PARTITION_COLORS["unused"])


def _usage_title(part: dict[str, Any], used_kb: float) -> str:
    size_kb = float(part["size_kb"])
    free_kb = max(size_kb - used_kb, 0)
    label = part["label"]
    if free_kb <= 0:
        return f"{label}: {_kb_label(size_kb)} ({_kb_label(used_kb)} used)"
    return f"{label}: {_kb_label(size_kb)} ({_kb_label(used_kb)} used, {_kb_label(free_kb)} free)"


def _tooltip_align_class(segment_start_pct: float, width_pct: float) -> str:
    center_pct = segment_start_pct + width_pct / 2.0
    if center_pct < TOOLTIP_ALIGN_START_THRESHOLD_PCT:
        return " memory-viz-segment-tooltip-start"
    return ""


def _render_segment(
    part: dict[str, Any],
    total_kb: float,
    threshold_kb: float,
    segment_start_pct: float,
) -> tuple[str, float]:
    if part.get("legend_only"):
        return "", 0.0

    used_color, free_color = _partition_colors(part["id"])
    size_kb = float(part["size_kb"])
    width_pct = 100.0 * size_kb / total_kb if total_kb else 0.0
    min_width_pct = 100.0 * threshold_kb / total_kb if total_kb else 0.0
    if part["id"] not in ALWAYS_VISIBLE_BAR_IDS and width_pct < min_width_pct:
        return "", 0.0

    used_kb = part.get("used_kb")
    title = f'{part["label"]}: {_kb_label(size_kb)}'
    inner = (
        f'<span class="memory-viz-fill memory-viz-fill-used" '
        f'style="width:100%;background:{used_color}"></span>'
    )

    if used_kb is not None and part["id"] in SPLIT_USAGE_IDS:
        used_kb = float(used_kb)
        title = _usage_title(part, used_kb)
        used_pct = min(100.0, 100.0 * used_kb / size_kb) if size_kb else 0
        free_pct = 100.0 - used_pct
        inner = (
            f'<span class="memory-viz-fill memory-viz-fill-used" '
            f'style="width:{used_pct:.2f}%;background:{used_color}"></span>'
            f'<span class="memory-viz-fill memory-viz-fill-free" '
            f'style="width:{free_pct:.2f}%;background:{free_color}"></span>'
        )

    tooltip_class = _tooltip_align_class(segment_start_pct, width_pct)
    return (
        f'<div class="memory-viz-segment memory-viz-segment-{part["id"]}{tooltip_class}" '
        f'style="flex:0 0 {width_pct:.4f}%" '
        f'data-tooltip="{html.escape(title, quote=True)}">'
        f"{inner}</div>",
        width_pct,
    )


def _render_bar(
    partitions: list[dict[str, Any]],
    total_kb: float,
    threshold_kb: float,
    aria_label: str,
) -> str:
    segments = []
    segment_start_pct = 0.0
    for part in partitions:
        segment, width_pct = _render_segment(part, total_kb, threshold_kb, segment_start_pct)
        if segment:
            segments.append(segment)
            segment_start_pct += width_pct
    return (
        f'<div class="memory-viz-bar" role="img" '
        f'aria-label="{html.escape(aria_label, quote=True)}">'
        f'{"".join(segments)}</div>'
    )


def _legend_swatch(color: str) -> str:
    return f'<span class="memory-viz-swatch" style="background:{color}"></span>'


def _legend_items_used_free(
    part_id: str,
    label_base: str,
    *,
    part: dict[str, Any] | None = None,
) -> list[str]:
    used_color, free_color = _partition_colors(part_id)
    items = []
    for suffix, color in (("used", used_color), ("free", free_color)):
        label = f"{label_base} ({suffix})"
        if suffix == "free" and part is not None:
            size_kb = float(part.get("size_kb", 0))
            used_kb = float(part.get("used_kb", 0))
            if size_kb > 0:
                free_pct = max(size_kb - used_kb, 0) / size_kb * 100.0
                label = f"{label_base} ({suffix}, {free_pct:.0f}%)"
        items.append(
            f'<span class="memory-viz-legend-item">'
            f"{_legend_swatch(color)}"
            f"{html.escape(label)}"
            f"</span>"
        )
    return items


def _collect_legend_items(
    nvm_partitions: list[dict[str, Any]],
    order: tuple[str, ...],
) -> list[str]:
    parts = {part["id"]: part for part in nvm_partitions}
    order_index = {part_id: index for index, part_id in enumerate(order)}
    sorted_ids = sorted(
        parts,
        key=lambda part_id: (order_index.get(part_id, len(order)), part_id),
    )

    items: list[str] = []
    for part_id in sorted_ids:
        part = parts[part_id]
        if part_id in SPLIT_USAGE_IDS:
            items.extend(_legend_items_used_free(part_id, part["label"], part=part))
        else:
            items.append(
                f'<span class="memory-viz-legend-item">'
                f"{_legend_swatch(_partition_colors(part_id)[0])}"
                f'{html.escape(part["label"])}'
                f"</span>"
            )
    return items


def _collect_board_nvm_legend_items(samples: list[dict[str, Any]]) -> list[str]:
    parts: dict[str, dict[str, Any]] = {}
    for sample in samples:
        for part in sample.get("nvm_partitions", []):
            parts.setdefault(part["id"], part)
    return _collect_legend_items(list(parts.values()), NVM_LEGEND_ORDER)


def _collect_board_external_legend_items(samples: list[dict[str, Any]]) -> list[str]:
    parts: dict[str, dict[str, Any]] = {}
    for sample in samples:
        for part in sample.get("external_nvm_partitions", []):
            if part.get("id") != "padding":
                parts.setdefault(part["id"], part)
    if not parts:
        return []
    return _collect_legend_items(list(parts.values()), EXTERNAL_NVM_LEGEND_ORDER)


def _render_ram_legend_items(ram_total_kb: float) -> list[str]:
    return _legend_items_used_free(
        "ram",
        "RAM",
        part={"size_kb": ram_total_kb, "used_kb": 0},
    )


def _nvm_width_pct(part_kb: float, reference_kb: float) -> float:
    if reference_kb <= 0:
        return 100.0
    return min(100.0, 100.0 * part_kb / reference_kb)


def _grid_style(nvm_total_kb: float, ram_total_kb: float) -> str:
    return (
        f"--memory-viz-nvm-fr:{int(nvm_total_kb)}fr;"
        f"--memory-viz-ram-fr:{int(ram_total_kb)}fr"
    )


def _parse_rst_label(directive: SphinxDirective, text: str) -> nodes.Element:
    label = nodes.paragraph()
    label["classes"] = ["memory-viz-sample-label"]
    content = StringList([text], "<memory_viz>")
    directive.state.nested_parse(content, 0, label)
    if len(label) == 1 and isinstance(label[0], nodes.paragraph):
        inner = label[0]
        label.remove(inner)
        label.extend(inner.children)
    return label


def _sample_plain_label(sample: dict[str, Any]) -> str:
    return plain_tab_label(sample_title(sample))


def _board_external_total_kb(samples: list[dict[str, Any]]) -> float | None:
    for sample in samples:
        total = sample.get("external_nvm_total_kb")
        if total:
            return float(total)
    return None


def _render_board_header(
    board: dict[str, Any],
    samples: list[dict[str, Any]],
) -> str:
    nvm_total_kb = float(board["nvm_total_kb"])
    ram_total_kb = float(board["ram_total_kb"])
    external_total_kb = _board_external_total_kb(samples)

    nvm_legend_items = _collect_board_nvm_legend_items(samples)
    external_legend_items = _collect_board_external_legend_items(samples)
    if external_legend_items:
        nvm_legend_items = nvm_legend_items + external_legend_items

    external_title = ""
    if external_total_kb is not None:
        ext_width = _nvm_width_pct(external_total_kb, nvm_total_kb)
        external_title = (
            f'<div class="memory-viz-panel-title memory-viz-panel-title-secondary" '
            f'style="width:{ext_width:.4f}%">'
            f"External NVM ({_kb_label(external_total_kb)})</div>"
        )

    nvm_legend = (
        f'<div class="memory-viz-legend memory-viz-legend-nvm">'
        f'{"".join(nvm_legend_items)}</div>'
    )
    ram_legend = (
        f'<div class="memory-viz-legend memory-viz-legend-ram">'
        f'{"".join(_render_ram_legend_items(ram_total_kb))}</div>'
    )

    return (
        f'<div class="memory-viz-chart-header">'
        f'<div class="memory-viz-panel-title memory-viz-panel-title-sample">Sample</div>'
        f'<div class="memory-viz-header-nvm">'
        f'<div class="memory-viz-panel-title">Internal NVM ({_kb_label(nvm_total_kb)})</div>'
        f"{external_title}"
        f"{nvm_legend}"
        f"</div>"
        f'<div class="memory-viz-header-ram">'
        f'<div class="memory-viz-panel-title">RAM ({_kb_label(ram_total_kb)})</div>'
        f"{ram_legend}"
        f"</div>"
        f"</div>"
    )


def _render_sample_nvm_html(
    sample: dict[str, Any],
    reference_nvm_kb: float,
    threshold_kb: float,
) -> str:
    title = _sample_plain_label(sample)
    internal_bar = _render_bar(
        sample.get("nvm_partitions", []),
        reference_nvm_kb,
        threshold_kb,
        f"{title} internal NVM",
    )

    external_parts = sample.get("external_nvm_partitions") or []
    external_total_kb = sample.get("external_nvm_total_kb")
    external_wrap = ""
    if external_parts and external_total_kb:
        ext_total_kb = float(external_total_kb)
        ext_width = _nvm_width_pct(ext_total_kb, reference_nvm_kb)
        external_bar = _render_bar(
            external_parts,
            ext_total_kb,
            threshold_kb,
            f"{title} external NVM",
        )
        external_wrap = (
            f'<div class="memory-viz-bar-wrap memory-viz-bar-wrap-external" '
            f'style="width:{ext_width:.4f}%">'
            f"{external_bar}</div>"
        )

    return (
        f'<div class="memory-viz-nvm-column">'
        f'<div class="memory-viz-bar-wrap">{internal_bar}</div>'
        f"{external_wrap}</div>"
    )


def _render_sample_ram_html(
    sample: dict[str, Any],
    threshold_kb: float,
) -> str:
    ram_partitions = [
        {
            "id": "ram",
            "label": "RAM",
            "size_kb": float(sample["ram_total_kb"]),
            "used_kb": float(sample["ram_used_kb"]),
        }
    ]
    ram_bar = _render_bar(
        ram_partitions,
        float(sample["ram_total_kb"]),
        threshold_kb,
        f'{_sample_plain_label(sample)} RAM',
    )
    return f'<div class="memory-viz-bar-wrap">{ram_bar}</div>'


def _build_board_nodes(
    directive: SphinxDirective,
    board: dict[str, Any],
    threshold_kb: float,
) -> nodes.Element:
    samples = board.get("samples", [])
    nvm_total_kb = float(board["nvm_total_kb"])
    ram_total_kb = float(board["ram_total_kb"])
    style = _grid_style(nvm_total_kb, ram_total_kb)

    wrapper = nodes.container()
    wrapper += nodes.raw(
        "",
        f'<div class="memory-viz-board" data-board="{html.escape(board["board_id"], quote=True)}" '
        f'style="{style}">',
        format="html",
    )

    board_node = nodes.container()
    board_node["classes"] = ["memory-viz-board-inner"]
    board_node += nodes.raw("", _render_board_header(board, samples), format="html")

    samples_node = nodes.container()
    samples_node["classes"] = ["memory-viz-samples"]

    for sample in samples:
        row = nodes.container()
        row["classes"] = ["memory-viz-sample-row"]
        row += _parse_rst_label(directive, sample_title(sample))
        row += nodes.raw(
            "",
            _render_sample_nvm_html(sample, nvm_total_kb, threshold_kb),
            format="html",
        )
        row += nodes.raw(
            "",
            _render_sample_ram_html(sample, threshold_kb),
            format="html",
        )
        samples_node += row

    board_node += samples_node
    wrapper += board_node
    wrapper += nodes.raw("", "</div>", format="html")
    return wrapper


class MemoryUsageBoard(SphinxDirective):
    """Render one board chart (used inside generated board tabs)."""

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False
    option_spec = {
        "board-id": directives.unchanged_required,
    }

    def run(self) -> list[nodes.Node]:
        boards = getattr(self.env, ENV_BOARD_KEY, {})
        entry = boards.get(self.options["board-id"])
        if entry is None:
            return []
        board, threshold_kb = entry
        return [_build_board_nodes(self, board, threshold_kb)]


def _build_tabs_rst(
    directive: SphinxDirective,
    boards: list[dict[str, Any]],
    threshold_kb: float,
) -> list[nodes.Node]:
    if not boards:
        note = nodes.paragraph()
        note += nodes.emphasis(text="No memory usage data found.")
        return [note]

    setattr(
        directive.env,
        ENV_BOARD_KEY,
        {str(board["board_id"]): (board, threshold_kb) for board in boards},
    )

    lines = [".. tabs::", ""]
    for board in boards:
        lines.append(f"   .. group-tab:: {plain_tab_label(board['tab_title'])}")
        lines.append("")
        for intro_line in board.get("tab_intro_rst", "").splitlines():
            lines.append(f"      {intro_line}")
        lines.append("")
        lines.append("      .. memory-usage-board::")
        lines.append(f"         :board-id: {board['board_id']}")
        lines.append("")

    container = nodes.container()
    directive.state.nested_parse(StringList(lines, "<memory_usage>"), 0, container)
    return container.children


class MemoryUsage(SphinxDirective):
    """Render sample memory usage bar charts from a YAML data file."""

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False
    option_spec = {
        "file": directives.unchanged_required,
    }

    def run(self) -> list[nodes.Node]:
        data = load_memory_yaml(self, self.options["file"])
        return _build_tabs_rst(
            self,
            sort_boards_by_internal_memory(data.get("boards", [])),
            _legend_threshold(data),
        )


def add_memory_viz_resources(app: Sphinx) -> None:
    static_path = RESOURCES_DIR.as_posix()
    if static_path not in app.config.html_static_path:
        app.config.html_static_path.append(static_path)
    app.add_css_file("memory_viz.css")


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("memory-usage", MemoryUsage)
    app.add_directive("memory-usage-board", MemoryUsageBoard)
    app.connect("builder-inited", add_memory_viz_resources)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
