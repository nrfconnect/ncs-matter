# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Parse SDK sync configuration from environment variables."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

KV_PAIR_RE = re.compile(r"(\w+)=([^\s]+)")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class SyncProject:
    name: str
    repo: str
    branch: str
    rebase: bool
    base_branch: str | None


@dataclass(frozen=True)
class SyncConfig:
    projects: tuple[SyncProject, ...]
    main_branch: str
    integration_branch: str
    pr_branch: str
    pr_label: str


def _parse_kv_record(value: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in KV_PAIR_RE.finditer(value)}


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _env(name: str, *, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or not value.strip():
        sys.exit(f"Missing required environment variable: {name}")
    return value.strip()


def load_sync_config() -> SyncConfig:
    project_names = _split_csv(_env("SDK_SYNC_PROJECTS"))
    if not project_names:
        sys.exit("SDK_SYNC_PROJECTS must list at least one project")

    projects: list[SyncProject] = []
    for name in project_names:
        raw = os.environ.get(f"SDK_SYNC_PROJECT_{name}")
        if not raw:
            sys.exit(f"Missing SDK_SYNC_PROJECT_{name}")
        pairs = _parse_kv_record(raw)
        repo = pairs.get("repo", "")
        branch = pairs.get("branch", "")
        rebase = pairs.get("rebase", "false").lower() == "true"
        base_branch = pairs.get("base")

        if not repo or not REPO_RE.fullmatch(repo):
            sys.exit(f"Invalid repo in SDK_SYNC_PROJECT_{name}: {repo!r}")
        if not branch:
            sys.exit(f"Missing branch in SDK_SYNC_PROJECT_{name}")
        if rebase and not base_branch:
            sys.exit(f"rebase=true requires base= in SDK_SYNC_PROJECT_{name}")

        projects.append(
            SyncProject(
                name=name,
                repo=repo,
                branch=branch,
                rebase=rebase,
                base_branch=base_branch,
            )
        )

    return SyncConfig(
        projects=tuple(projects),
        main_branch=_env("SDK_SYNC_MAIN_BRANCH", default="main"),
        integration_branch=_env("SDK_SYNC_INTEGRATION_BRANCH", default="ncs-sync"),
        pr_branch=_env("SDK_SYNC_PR_BRANCH", default="sdk-sync/test"),
        pr_label=_env("SDK_SYNC_PR_LABEL", default="ci-disabled"),
    )


def parse_revision_overrides(raw: str | None) -> dict[str, str]:
    if not raw or not raw.strip():
        return {}

    overrides: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            sys.exit(f"Invalid revision override (expected name=sha): {item!r}")
        name, sha = item.split("=", 1)
        name = name.strip()
        sha = sha.strip()
        if not name or len(sha) < 7:
            sys.exit(f"Invalid revision override: {item!r}")
        overrides[name] = sha
    return overrides
