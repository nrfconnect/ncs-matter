#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

"""Shared CLI helpers for matter_sample_checker and matter_doc_checker."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def checker_script_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def default_config_path() -> Path:
    return checker_script_dir() / "matter_sample_checker_config.yaml"


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base",
        "-b",
        type=str,
        help="Base directory for resolving workspace paths. If not specified, uses the "
        "ncs-matter repository root containing this script.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output during checks",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to custom configuration YAML file. Default: matter_sample_checker_config.yaml "
        "in the checker script directory.",
    )


def resolve_workspace_base(base_arg: str | None) -> Path:
    if base_arg:
        return Path(base_arg).resolve()

    script_repo_root = checker_script_dir().parent.parent
    if (script_repo_root / "west.yml").exists() and (script_repo_root / "samples").is_dir():
        return script_repo_root

    zephyr_base = os.environ.get("ZEPHYR_BASE")
    if not zephyr_base:
        print(
            "Error: --base not specified and ncs-matter repository root could not be inferred.",
            file=sys.stderr,
        )
        sys.exit(1)

    nrf_base = Path(zephyr_base).resolve().parent / "ncs-matter"
    if not nrf_base.is_dir():
        print(f"Error: Could not infer ncs-matter workspace base: {nrf_base}", file=sys.stderr)
        sys.exit(1)
    return nrf_base


def resolve_config_path(config_arg: str | None) -> Path:
    return Path(config_arg) if config_arg else default_config_path()


def parse_expected_years(year_arg: list[int] | None) -> list[int]:
    if year_arg is None:
        return []
    if len(year_arg) == 0:
        return [datetime.now().year]
    return year_arg
