# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for sdk_sync."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

GITHUB_API = "https://api.github.com"
SDK_SYNC_PR_MARKER = "<!-- sdk-sync-pr -->"
GIT_USER_NAME = "Nordic Builder"
GIT_USER_EMAIL = "pylon@nordicsemi.no"


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


def run_git(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def configure_git_user() -> None:
    run_git(["config", "--global", "user.email", GIT_USER_EMAIL])
    run_git(["config", "--global", "user.name", GIT_USER_NAME])


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


def branch_tip(*, repo: str, branch: str) -> str:
    ref = github_get(f"/repos/{repo}/git/ref/heads/{branch}")
    return ref["object"]["sha"]


def display_revision(sha: str) -> str:
    return sha if len(sha) <= 6 else f"{sha[:6]}…"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
