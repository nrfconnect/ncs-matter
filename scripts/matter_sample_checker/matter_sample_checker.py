#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

"""
NCS Matter Sample Consistency Checker

This script checks the consistency of Matter samples in nRF Connect SDK.
It verifies file structure, configuration consistency, license years,
PM static files, ZAP files, and detects copy-paste mistakes.

Usage: python matter_sample_checker.py <sample_directory_path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from internal.check_discovery import CheckDiscovery
from internal.checker import MatterSampleChecker
from internal.cli_common import (
    add_common_arguments,
    checker_script_dir,
    parse_expected_years,
    resolve_config_path,
    resolve_workspace_base,
)
from internal.utils.utils import load_config, parse_samples_zap_yaml


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Matter sample consistency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog="""
Examples:
  python matter_sample_checker.py /path/to/ncs-matter/samples/template
  python matter_sample_checker.py /path/to/ncs-matter/samples/light_bulb
  python matter_sample_checker.py  # Use current directory (year checking skipped by default)
  python matter_sample_checker.py --year  # Enable year checking for current year
  python matter_sample_checker.py --year 2024  # Check for 2024 copyright year
  python matter_sample_checker.py --year 2023 2024 2025  # Allow multiple years
  python matter_sample_checker.py -y  # Short form for current year
  python matter_sample_checker.py -y 2021 2022  # Short form with specific years
  python matter_sample_checker.py --config /path/to/custom_config.yaml  # Custom config
  python matter_sample_checker.py -c custom.yaml -y 2024  # Combined options
  python matter_sample_checker.py --allow-names "light bulb" template  # Allow specific names in \
copy-paste checking
  python matter_sample_checker.py -a "light bulb" "door lock" -v  # Allow multiple names with \
verbose output
  python matter_sample_checker.py --samples-zap-yaml zap_samples.yml --base /path/to/ncs-matter
  python matter_sample_checker.py -s zap_samples.yml -b /path/to/ncs-matter -y 2024
        """,
    )
    parser.add_argument(
        "sample_path",
        nargs="?",
        default=".",
        help="Path to the Matter sample directory to check (default: current directory). "
        "Ignored if --samples-zap-yaml is used.",
    )
    parser.add_argument(
        "--samples-zap-yaml",
        "-s",
        type=str,
        help="Path to YAML file containing list of samples to check "
        "(similar to zap_samples.yml format)",
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        nargs="*",
        help="Enable copyright year checking. If no years specified, checks current year. "
        "Can specify multiple years (e.g., --year 2023 2024 2025). Default: skip year checking",
    )
    parser.add_argument(
        "--allow-names",
        "-a",
        type=str,
        nargs="*",
        default=[],
        help="List of names/terms to allow during copy-paste error checking (case-insensitive). "
        "Use quotes for multi-word names.",
    )
    add_common_arguments(parser)
    args = parser.parse_args()

    workspace_base = resolve_workspace_base(args.base)
    expected_years = parse_expected_years(args.year)

    if args.samples_zap_yaml:
        yaml_path = Path(args.samples_zap_yaml).resolve()
        if not yaml_path.exists():
            print(f"Error: YAML file does not exist: {yaml_path}", file=sys.stderr)
            return 1

        sample_paths = parse_samples_zap_yaml(yaml_path, workspace_base)
        if not sample_paths:
            print(f"Error: No valid samples found in YAML file: {yaml_path}", file=sys.stderr)
            return 1

        print(f"Found {len(sample_paths)} samples to check from {yaml_path}")
        if args.verbose:
            for sample in sample_paths:
                print(f"  - {sample}")
    else:
        sample_path = Path(args.sample_path).resolve()
        if not sample_path.exists():
            print(f"Error: Sample path does not exist: {sample_path}", file=sys.stderr)
            return 1
        if not sample_path.is_dir():
            print(f"Error: Sample path is not a directory: {sample_path}", file=sys.stderr)
            return 1
        sample_paths = [sample_path]

    config_dict = load_config(str(resolve_config_path(args.config)))

    checks_dir = checker_script_dir() / "checks"
    check_discovery = CheckDiscovery(checks_dir)
    check_classes = check_discovery.discover_checks()

    if args.verbose:
        print(f"Discovered {len(check_classes)} sample checks:")
        for check_class in check_classes:
            print(f"  - {check_class.__name__}")

    all_reports: list[str] = []
    total_issues = 0

    for sample_path in sample_paths:
        checker = MatterSampleChecker(
            config_dict,
            workspace_base,
            sample_path,
            verbose=args.verbose,
            allowed_names=args.allow_names,
            expected_years=expected_years,
            check_classes=check_classes,
        )
        report, issue_count = checker.run_checks()
        all_reports.append(report)
        total_issues += issue_count

    final_report = "\n\n".join(all_reports)

    if len(sample_paths) > 1:
        summary = f"\n{'=' * 80}\n"
        summary += "SUMMARY\n"
        summary += f"{'=' * 80}\n"
        summary += f"Total samples checked: {len(sample_paths)}\n"
        summary += f"Total issues found: {total_issues}\n"
        final_report = final_report + summary

    print(final_report)
    return total_issues


if __name__ == "__main__":
    sys.exit(main())
