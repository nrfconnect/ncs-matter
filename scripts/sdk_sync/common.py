# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for sdk_sync scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import re

import requests

GITHUB_API = "https://api.github.com"
REPORT_MARKER = "<!-- sdk-sync-report -->"
COPILOT_TRIGGER_MARKER = "<!-- sdk-sync-copilot-trigger -->"
SDK_SYNC_PR_MARKER = "<!-- sdk-sync-pr -->"
SYNC_PR_HEAD_BRANCH = "sdk-sync/test"
SYNC_PR_BASE_BRANCH = "sdk-nrf"

GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
POSITIVE_INT_RE = re.compile(r"^[0-9]+$")
GITHUB_ACTIONS_RUN_URL_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+/actions/runs/[0-9]+$")

NRF_REPO = "nrfconnect/sdk-nrf"
CHIP_REPO = "nrfconnect/sdk-connectedhomeip"


@dataclass
class CommitInfo:
    sha: str
    subject: str
    html_url: str


@dataclass
class ChipSyncReport:
    master_sha: str
    sdk_nrf_branch_sha: str
    merge_base_sha: str
    sdk_nrf_only_commits: list[CommitInfo]

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_sha": self.master_sha,
            "sdk_nrf_branch_sha": self.sdk_nrf_branch_sha,
            "merge_base_sha": self.merge_base_sha,
            "sdk_nrf_only_commits": [asdict(c) for c in self.sdk_nrf_only_commits],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChipSyncReport:
        commits = [CommitInfo(**item) for item in data["sdk_nrf_only_commits"]]
        return cls(
            master_sha=data["master_sha"],
            sdk_nrf_branch_sha=data["sdk_nrf_branch_sha"],
            merge_base_sha=data["merge_base_sha"],
            sdk_nrf_only_commits=commits,
        )


@dataclass
class SyncState:
    nrf_sha: str
    matter_sha: str
    chip_sync: ChipSyncReport
    pr_number: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SyncState:
        return cls(
            nrf_sha=data["nrf_sha"],
            matter_sha=data["matter_sha"],
            chip_sync=ChipSyncReport.from_dict(data["chip_sync"]),
            pr_number=data["pr_number"],
        )


def github_token() -> str:
    token = os.environ.get("NCS_NORDICBUILDER_ACTION_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("NCS_NORDICBUILDER_ACTION_TOKEN or GH_TOKEN must be set")
    return token


def github_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {github_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_get(path: str, *, params: dict[str, Any] | None = None) -> Any:
    url = path if path.startswith("https://") else f"{GITHUB_API}{path}"
    response = requests.get(url, headers=github_headers(), params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def github_get_paginated(path: str, *, params: dict[str, Any] | None = None) -> list[Any]:
    url = path if path.startswith("https://") else f"{GITHUB_API}{path}"
    items: list[Any] = []
    while url:
        response = requests.get(url, headers=github_headers(), params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return payload
        items.extend(payload)
        url = response.links.get("next", {}).get("url")
        params = None
    return items


def run_git(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def configure_git_user() -> None:
    run_git(["config", "user.email", "sdk-sync-bot@users.noreply.github.com"])
    run_git(["config", "user.name", "sdk-sync-bot"])


def short_sha(sha: str) -> str:
    return sha[:12]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def recent_commits(*, repo: str, branch: str, days: int) -> list[CommitInfo]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = github_get_paginated(
        f"/repos/{repo}/commits",
        params={"sha": branch, "since": since, "per_page": 100},
    )
    commits: list[CommitInfo] = []
    for commit in payload:
        commits.append(
            CommitInfo(
                sha=commit["sha"],
                subject=commit["commit"]["message"].splitlines()[0],
                html_url=commit["html_url"],
            )
        )
    return commits


@dataclass(frozen=True)
class TrustedWorkflowRun:
    head_sha: str
    head_branch: str
    head_repository: str
    workflow_run_id: str
    workflow_run_url: str


def load_trusted_workflow_run_event(*, expected_repo: str) -> TrustedWorkflowRun:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        sys.exit("GITHUB_EVENT_PATH is not set")

    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    workflow_run = payload.get("workflow_run")
    if not isinstance(workflow_run, dict):
        sys.exit("Missing workflow_run in GitHub event payload")

    if workflow_run.get("event") != "pull_request":
        sys.exit("workflow_run.event is not pull_request")

    repository = workflow_run.get("repository", {})
    head_repository = workflow_run.get("head_repository", {})
    if not isinstance(repository, dict) or not isinstance(head_repository, dict):
        sys.exit("workflow_run repository fields are malformed")

    repo_full = str(repository.get("full_name", ""))
    head_repo_full = str(head_repository.get("full_name", ""))
    if repo_full != expected_repo or head_repo_full != expected_repo:
        sys.exit("workflow_run repository is untrusted")

    head_branch = str(workflow_run.get("head_branch", ""))
    if head_branch != SYNC_PR_HEAD_BRANCH:
        sys.exit(f"Unexpected workflow_run.head_branch: {head_branch!r}")

    head_sha = str(workflow_run.get("head_sha", ""))
    if not GIT_SHA_RE.fullmatch(head_sha):
        sys.exit("Invalid workflow_run.head_sha")

    workflow_run_id = str(workflow_run.get("id", ""))
    if not POSITIVE_INT_RE.fullmatch(workflow_run_id):
        sys.exit("Invalid workflow_run.id")

    workflow_run_url = str(workflow_run.get("html_url", ""))
    if not GITHUB_ACTIONS_RUN_URL_RE.fullmatch(workflow_run_url):
        sys.exit("Invalid workflow_run.html_url")

    return TrustedWorkflowRun(
        head_sha=head_sha,
        head_branch=head_branch,
        head_repository=head_repo_full,
        workflow_run_id=workflow_run_id,
        workflow_run_url=workflow_run_url,
    )


def parse_verified_pr_number(raw: str) -> int:
    value = raw.strip()
    if not POSITIVE_INT_RE.fullmatch(value):
        sys.exit(f"Invalid PR number: {raw!r}")
    return int(value)


def parse_verified_workflow_run_id(raw: str) -> str:
    value = raw.strip()
    if not POSITIVE_INT_RE.fullmatch(value):
        sys.exit(f"Invalid workflow run id: {raw!r}")
    return value


def parse_verified_workflow_run_url(raw: str) -> str:
    value = raw.strip()
    if not GITHUB_ACTIONS_RUN_URL_RE.fullmatch(value):
        sys.exit(f"Invalid workflow run url: {raw!r}")
    return value
