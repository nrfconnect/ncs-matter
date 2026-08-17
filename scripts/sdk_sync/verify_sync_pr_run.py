# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Verify a workflow_run belongs to a trusted sdk-sync PR before consuming artifacts."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    SDK_SYNC_PR_MARKER,
    SYNC_PR_BASE_BRANCH,
    SYNC_PR_HEAD_BRANCH,
    TrustedWorkflowRun,
    github_get,
    github_token,
    load_trusted_workflow_run_event,
)


def write_github_output(name: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def verify_sync_pr(*, repo: str, workflow_run: TrustedWorkflowRun) -> int:
    owner = repo.split("/", 1)[0]
    pulls = github_get(
        f"/repos/{repo}/pulls",
        params={
            "state": "open",
            "head": f"{owner}:{SYNC_PR_HEAD_BRANCH}",
            "base": SYNC_PR_BASE_BRANCH,
            "per_page": 10,
        },
    )
    if not isinstance(pulls, list) or not pulls:
        sys.exit("No open sdk-sync PR found for trusted workflow run")
    if len(pulls) != 1:
        sys.exit(f"Expected exactly one sdk-sync PR, found {len(pulls)}")

    pull = pulls[0]
    pr_number = int(pull["number"])
    if pull["head"]["sha"] != workflow_run.head_sha:
        sys.exit("PR head SHA does not match workflow_run.head_sha")
    if pull["head"]["ref"] != SYNC_PR_HEAD_BRANCH:
        sys.exit("PR head ref does not match sdk-sync/test")
    if pull["base"]["ref"] != SYNC_PR_BASE_BRANCH:
        sys.exit("PR base ref is not sdk-nrf")
    if pull["head"]["repo"]["full_name"] != repo:
        sys.exit("PR head repository is not the base repository (fork PR)")
    if SDK_SYNC_PR_MARKER not in pull.get("body", ""):
        sys.exit("PR body is missing sdk-sync marker")

    return pr_number


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nrfconnect/ncs-matter"))
    parser.add_argument(
        "--from-event",
        action="store_true",
        help="Read and validate workflow_run fields from GITHUB_EVENT_PATH",
    )
    args = parser.parse_args()

    if not args.from_event:
        sys.exit("--from-event is required")

    _ = github_token()
    workflow_run = load_trusted_workflow_run_event(expected_repo=args.repo)
    pr_number = verify_sync_pr(repo=args.repo, workflow_run=workflow_run)

    write_github_output("pr_number", str(pr_number))
    write_github_output("workflow_run_id", workflow_run.workflow_run_id)
    write_github_output("workflow_run_url", workflow_run.workflow_run_url)
    print(f"Verified trusted sdk-sync PR #{pr_number}")


if __name__ == "__main__":
    main()
