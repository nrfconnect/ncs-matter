#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Nordic Semiconductor ASA

"""Return 0 when Twister should run for a PR, 1 when CI can be skipped."""

import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path

import yaml

_CI_DIR = Path(__file__).resolve().parent
_ADDON_ROOT = _CI_DIR.parent.parent.parent


def _load_ignore_patterns(path: Path) -> list[str]:
    patterns = []
    with path.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def _ignored(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _west_manifest_changed(files: list[str]) -> bool:
    return any(f == "west.yml" or f.endswith("/west.yml") for f in files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modified-files", required=True, help="JSON file with changed paths")
    parser.add_argument(
        "--ignore-path",
        default=str(_CI_DIR / "twister_ignore.txt"),
        help="Ignore patterns (no Twister when only these change)",
    )
    parser.add_argument(
        "--label",
        default=os.environ.get("CI_RUN_TWISTER_LABEL", "CI-run-twister"),
        help="PR label that forces Twister",
    )
    args = parser.parse_args()

    if os.environ.get("FORCE_TWISTER", "").lower() in ("1", "true", "yes"):
        return 0

    pr_labels = os.environ.get("CHANGE_LABELS", "")
    if args.label.lower() in [label.strip().lower() for label in pr_labels.split(",") if label.strip()]:
        return 0

    with open(args.modified_files, encoding="utf-8") as fp:
        files = json.load(fp)

    if not files:
        print("No changed files, skipping Twister")
        return 1

    if _west_manifest_changed(files):
        print("west.yml changed, running Twister")
        return 0

    ignore_patterns = _load_ignore_patterns(Path(args.ignore_path))
    relevant = [f for f in files if not _ignored(f, ignore_patterns)]
    if not relevant:
        print("Only ignored/meta files changed, skipping Twister")
        return 1

    print("Relevant files changed, running Twister")
    return 0


if __name__ == "__main__":
    sys.exit(main())
