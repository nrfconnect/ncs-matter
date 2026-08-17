# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Prepare the sdk-sync test branch and open its pull request."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import configure_git_user, github_get, github_headers, run_git, write_json  # noqa: E402


def find_open_pr(*, repo: str, head_branch: str, base_branch: str) -> int | None:
    pulls = github_get(f"/repos/{repo}/pulls", params={"state": "open", "per_page": 100})
    owner = repo.split("/", 1)[0]
    head_ref = f"{owner}:{head_branch}"
    for pull in pulls:
        if pull.get("base", {}).get("ref") != base_branch:
            continue
        if pull.get("head", {}).get("ref") == head_branch or pull.get("head", {}).get("label") == head_ref:
            return int(pull["number"])
    return None


def commits_ahead(*, repo: str, base_branch: str, head_branch: str) -> int:
    comparison = github_get(f"/repos/{repo}/compare/{base_branch}...{head_branch}")
    return int(comparison.get("ahead_by", 0))


def prepare_pr_branch(*, source_branch: str, pr_branch: str, remote: str) -> None:
    configure_git_user()
    run_git(["fetch", remote, source_branch])
    run_git(["checkout", source_branch])
    run_git(["checkout", "-B", pr_branch])
    push = run_git(["push", "--force-with-lease", remote, pr_branch], check=False)
    if push.returncode != 0:
        print(push.stderr, file=sys.stderr)
        sys.exit(f"Failed to push branch {pr_branch}")


def ensure_repo_label(*, repo: str, label: str) -> None:
    encoded = requests.utils.quote(label, safe="")
    response = requests.get(
        f"https://api.github.com/repos/{repo}/labels/{encoded}",
        headers=github_headers(),
        timeout=60,
    )
    if response.status_code == 200:
        return
    create = requests.post(
        f"https://api.github.com/repos/{repo}/labels",
        headers=github_headers(),
        json={
            "name": label,
            "color": "0E8A16",
            "description": "Skip Jenkins additional/full Twister (sdk-sync PR)",
        },
        timeout=60,
    )
    if create.status_code >= 400 and create.status_code != 422:
        sys.exit(f"Failed to create label {label!r}: {create.status_code} {create.text}")


def ensure_pr_label(*, repo: str, pr_number: int, label: str) -> None:
    ensure_repo_label(repo=repo, label=label)
    response = requests.post(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels",
        headers=github_headers(),
        json=[label],
        timeout=60,
    )
    if response.status_code >= 400:
        sys.exit(f"Failed to add label {label!r} to PR #{pr_number}: {response.status_code} {response.text}")
    print(f"Ensured label {label!r} on PR #{pr_number}")


def open_sync_pr(
    *,
    repo: str,
    base_branch: str,
    head_branch: str,
    state_file: Path,
    pr_label: str | None = "ci-disabled",
) -> int | None:
    ahead = commits_ahead(repo=repo, base_branch=base_branch, head_branch=head_branch)
    if ahead == 0:
        existing = find_open_pr(repo=repo, head_branch=head_branch, base_branch=base_branch)
        if existing is not None:
            print(f"No new commits, reusing open PR #{existing}")
            if pr_label:
                ensure_pr_label(repo=repo, pr_number=existing, label=pr_label)
            return existing
        print(f"No commits between {base_branch} and {head_branch}; skipping PR creation")
        return None

    existing = find_open_pr(repo=repo, head_branch=head_branch, base_branch=base_branch)
    if existing is not None:
        print(f"Reusing open PR #{existing} for {head_branch} -> {base_branch} ({ahead} commits ahead)")
        if pr_label:
            ensure_pr_label(repo=repo, pr_number=existing, label=pr_label)
        return existing

    title = "manifest: Weekly sdk-nrf / sdk-connectedhomeip sync test"
    body = (
        "Automated weekly sync PR testing updated `sdk-nrf` and "
        "`sdk-connectedhomeip` revisions in `west.yml`.\n\n"
        "Do not merge without review.\n\n"
        "<!-- sdk-sync-pr -->"
    )
    response = requests.post(
        f"https://api.github.com/repos/{repo}/pulls",
        headers=github_headers(),
        json={
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
        },
        timeout=60,
    )
    if response.status_code >= 400:
        sys.exit(f"Failed to create PR: {response.status_code} {response.text}")
    number = int(response.json()["number"])
    print(f"Created PR #{number} ({head_branch} -> {base_branch}, {ahead} commits ahead)")
    if pr_label:
        ensure_pr_label(repo=repo, pr_number=number, label=pr_label)
    return number


def store_pr_number(*, state_file: Path, pr_number: int | None) -> None:
    if pr_number is None:
        return
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
    else:
        state = {}
    state["pr_number"] = pr_number
    write_json(state_file, state)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nrfconnect/ncs-matter"))
    parser.add_argument("--command", choices=["prepare-branch", "open-pr"], required=True)
    parser.add_argument("--source-branch", default="sdk-nrf")
    parser.add_argument("--pr-branch", default="sdk-sync/test")
    parser.add_argument("--base-branch", default="sdk-nrf")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--pr-label", default="ci-disabled")
    parser.add_argument("--state-file", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "prepare-branch":
        prepare_pr_branch(
            source_branch=args.source_branch,
            pr_branch=args.pr_branch,
            remote=args.remote,
        )
        return

    pr_number = open_sync_pr(
        repo=args.repo,
        base_branch=args.base_branch,
        head_branch=args.pr_branch,
        state_file=args.state_file,
        pr_label=args.pr_label or None,
    )
    store_pr_number(state_file=args.state_file, pr_number=pr_number)


if __name__ == "__main__":
    main()
