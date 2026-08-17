# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Collect sdk-nrf and sdk-connectedhomeip revision data for sync."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    CHIP_REPO,
    NRF_REPO,
    ChipSyncReport,
    CommitInfo,
    github_get,
    read_json,
    write_json,
)


def branch_tip(*, repo: str, branch: str) -> str:
    ref = github_get(f"/repos/{repo}/git/ref/heads/{branch}")
    return ref["object"]["sha"]


def commits_not_in_master(*, repo: str) -> list[CommitInfo]:
    comparison = github_get(f"/repos/{repo}/compare/master...sdk-nrf")
    commits: list[CommitInfo] = []
    for commit in comparison.get("commits", []):
        commits.append(
            CommitInfo(
                sha=commit["sha"],
                subject=commit["commit"]["message"].splitlines()[0],
                html_url=commit["html_url"],
            )
        )
    return commits


def build_chip_sync_report() -> ChipSyncReport:
    master_sha = branch_tip(repo=CHIP_REPO, branch="master")
    sdk_nrf_sha = branch_tip(repo=CHIP_REPO, branch="sdk-nrf")
    merge_base_sha = github_get(f"/repos/{CHIP_REPO}/compare/master...sdk-nrf")["merge_base_commit"]["sha"]
    sdk_nrf_only = commits_not_in_master(repo=CHIP_REPO)
    return ChipSyncReport(
        master_sha=master_sha,
        sdk_nrf_branch_sha=sdk_nrf_sha,
        merge_base_sha=merge_base_sha,
        sdk_nrf_only_commits=sdk_nrf_only,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=Path, required=True)
    args = parser.parse_args()

    chip_report = build_chip_sync_report()
    nrf_sha = branch_tip(repo=NRF_REPO, branch="main")

    state = read_json(args.state_file) if args.state_file.exists() else {}
    state["chip_sync"] = chip_report.to_dict()
    state["matter_sha"] = chip_report.sdk_nrf_branch_sha
    state["nrf_sha"] = nrf_sha
    write_json(args.state_file, state)

    print(f"sdk-nrf main: {nrf_sha}")
    print(f"sdk-connectedhomeip master: {chip_report.master_sha}")
    print(f"sdk-connectedhomeip sdk-nrf: {chip_report.sdk_nrf_branch_sha}")
    print(f"sdk-connectedhomeip commits not in master: {len(chip_report.sdk_nrf_only_commits)}")


if __name__ == "__main__":
    main()
