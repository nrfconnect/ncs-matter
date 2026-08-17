# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Rebase sdk-connectedhomeip sdk-nrf branch onto master."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import CHIP_REPO, configure_git_user, github_token, run_git  # noqa: E402


def sync_chip_branch(*, chip_repo_name: str, base_branch: str, integration_branch: str) -> None:
    configure_git_user()
    token = github_token()
    workdir = Path(tempfile.mkdtemp(prefix="sdk-connectedhomeip-sync-"))
    clone_url = f"https://x-access-token:{token}@github.com/{chip_repo_name}.git"

    try:
        clone = run_git(["clone", clone_url, str(workdir)], check=False)
        if clone.returncode != 0:
            print(clone.stderr, file=sys.stderr)
            sys.exit(f"Failed to clone {chip_repo_name}")

        run_git(["fetch", "origin", base_branch, integration_branch], cwd=workdir)

        checkout = run_git(["checkout", integration_branch], cwd=workdir, check=False)
        if checkout.returncode != 0:
            run_git(["checkout", "-B", integration_branch, f"origin/{integration_branch}"], cwd=workdir)

        rebase = run_git(["rebase", f"origin/{base_branch}"], cwd=workdir, check=False)
        if rebase.returncode != 0:
            run_git(["rebase", "--abort"], cwd=workdir, check=False)
            print(rebase.stderr, file=sys.stderr)
            sys.exit(f"Rebase of {chip_repo_name}:{integration_branch} onto {base_branch} failed")

        push = run_git(["push", "--force-with-lease", "origin", integration_branch], cwd=workdir, check=False)
        if push.returncode != 0:
            print(push.stderr, file=sys.stderr)
            sys.exit(f"Failed to push rebased {integration_branch} to {chip_repo_name}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"Rebased {chip_repo_name}:{integration_branch} onto {base_branch} and pushed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-branch", default="master")
    parser.add_argument("--integration-branch", default="sdk-nrf")
    args = parser.parse_args()
    sync_chip_branch(
        chip_repo_name=CHIP_REPO,
        base_branch=args.base_branch,
        integration_branch=args.integration_branch,
    )


if __name__ == "__main__":
    main()
