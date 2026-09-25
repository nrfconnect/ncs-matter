#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

"""
NCS Matter Documentation Checker

Validates add-on documentation consistency: index versions, hardware requirements,
and Sphinx cross-references / external links.

Usage: python matter_doc_checker.py --base /path/to/ncs-matter
"""

from __future__ import annotations

import argparse
import sys

from internal.check_discovery import CheckDiscovery
from internal.checker import MatterSampleChecker
from internal.cli_common import (
    add_common_arguments,
    checker_script_dir,
    resolve_config_path,
    resolve_workspace_base,
)
from internal.utils.utils import load_config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check ncs-matter documentation consistency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog="""
Examples:
  python matter_doc_checker.py --base /path/to/ncs-matter
  python matter_doc_checker.py -b /path/to/ncs-matter -v
  python matter_doc_checker.py -c custom.yaml -b /path/to/ncs-matter
        """,
    )
    add_common_arguments(parser)
    args = parser.parse_args()

    workspace_base = resolve_workspace_base(args.base)
    config_dict = load_config(str(resolve_config_path(args.config)))

    checks_dir = checker_script_dir() / "checks"
    check_discovery = CheckDiscovery(checks_dir)
    doc_check_classes = check_discovery.discover_doc_checks()

    if args.verbose:
        print(f"Discovered {len(doc_check_classes)} documentation checks:")
        for check_class in doc_check_classes:
            print(f"  - {check_class.__name__}")

    if not doc_check_classes:
        print("Error: No documentation checks discovered.", file=sys.stderr)
        return 1

    checker = MatterSampleChecker(
        config_dict,
        workspace_base,
        verbose=args.verbose,
        check_classes=doc_check_classes,
        live_progress=True,
    )

    report, issue_count = checker.run_checks()
    if report.strip():
        print(report)
    return issue_count


if __name__ == "__main__":
    sys.exit(main())
