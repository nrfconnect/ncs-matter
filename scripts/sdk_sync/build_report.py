# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Build and post the sdk-sync summary comment on the test PR."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    NRF_REPO,
    REPORT_MARKER,
    CommitInfo,
    SyncState,
    github_get_paginated,
    github_headers,
    github_token,
    read_json,
    recent_commits,
    short_sha,
)


def render_commit_list(commits: list[CommitInfo], *, empty_message: str) -> str:
    if not commits:
        return f"{empty_message}\n"
    lines = [f"- [{commit.subject}]({commit.html_url}) (`{short_sha(commit.sha)}`)" for commit in commits]
    return "\n".join(lines) + "\n"


def build_report_body(*, state: SyncState, days: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    merged_commits = recent_commits(repo=NRF_REPO, branch="main", days=days)
    chip_only = state.chip_sync.sdk_nrf_only_commits

    return f"""{REPORT_MARKER}
## Weekly SDK sync report

Generated: {now}

### Manifest revisions under test

| Project | Revision |
|---------|----------|
| `sdk-nrf` (`main`) | `{state.nrf_sha}` |
| `sdk-connectedhomeip` (`sdk-nrf`) | `{state.matter_sha}` |

<details>
<summary>sdk-nrf merged commits (last {days} days, {len(merged_commits)})</summary>

{render_commit_list(merged_commits, empty_message=f"_No commits merged to `main` in the last {days} days._")}
</details>

<details>
<summary>sdk-connectedhomeip commits on `sdk-nrf` not in `master` ({len(chip_only)})</summary>

{render_commit_list(chip_only, empty_message="_No commits on `sdk-nrf` ahead of `master`._")}
</details>
"""


def find_existing_comment(*, repo: str, pr_number: int) -> int | None:
    comments = github_get_paginated(f"/repos/{repo}/issues/{pr_number}/comments")
    for comment in comments:
        if REPORT_MARKER in comment.get("body", ""):
            return int(comment["id"])
    return None


def upsert_pr_comment(*, repo: str, pr_number: int, body: str) -> None:
    existing_id = find_existing_comment(repo=repo, pr_number=pr_number)
    headers = github_headers()
    if existing_id is not None:
        response = requests.patch(
            f"https://api.github.com/repos/{repo}/issues/comments/{existing_id}",
            headers=headers,
            json={"body": body},
            timeout=60,
        )
        action = "Updated"
    else:
        response = requests.post(
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
            headers=headers,
            json={"body": body},
            timeout=60,
        )
        action = "Posted"
    if response.status_code >= 400:
        sys.exit(f"Failed to comment on PR #{pr_number}: {response.status_code} {response.text}")
    print(f"{action} report comment on PR #{pr_number}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nrfconnect/ncs-matter"))
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    _ = github_token()
    raw = read_json(args.state_file)
    if "pr_number" not in raw:
        print("No PR was opened; skipping report comment")
        return

    body = build_report_body(state=SyncState.from_dict(raw), days=args.days)
    upsert_pr_comment(repo=args.repo, pr_number=raw["pr_number"], body=body)


if __name__ == "__main__":
    main()
