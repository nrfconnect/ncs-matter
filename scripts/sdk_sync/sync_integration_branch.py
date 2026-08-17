# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Synchronize the integration branch with main."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import configure_git_user, run_git  # noqa: E402


def sync_branch(*, main_branch: str, integration_branch: str, remote: str) -> None:
    configure_git_user()
    run_git(["fetch", remote, main_branch, integration_branch])

    run_git(["checkout", "-B", integration_branch, f"{remote}/{main_branch}"])
    push = run_git(["push", "--force-with-lease", remote, integration_branch], check=False)
    if push.returncode != 0:
        print(push.stderr, file=sys.stderr)
        sys.exit(f"Failed to push synchronized {integration_branch} to {remote}")

    print(f"Synchronized {integration_branch} with {remote}/{main_branch}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-branch", default="main")
    parser.add_argument("--integration-branch", default="sdk-nrf")
    parser.add_argument("--remote", default="origin")
    args = parser.parse_args()
    sync_branch(
        main_branch=args.main_branch,
        integration_branch=args.integration_branch,
        remote=args.remote,
    )


if __name__ == "__main__":
    main()
