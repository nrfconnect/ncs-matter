# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Update west.yml with new sdk-nrf and sdk-connectedhomeip revisions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import configure_git_user, read_json, run_git  # noqa: E402

REVISION_LINE = re.compile(r"^(\s*)revision:\s*(.+?)\s*$")


def project_revisions(text: str) -> dict[str, str]:
    revisions: dict[str, str] = {}
    current_project: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("- name: "):
            current_project = stripped.removeprefix("- name: ").strip()
            continue
        match = REVISION_LINE.match(line)
        if match and current_project in {"nrf", "matter"}:
            revisions[current_project] = match.group(2).strip()
    return revisions


def update_manifest_text(*, text: str, nrf_sha: str, matter_sha: str) -> str:
    current_project: str | None = None
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("- name: "):
            current_project = stripped.removeprefix("- name: ").strip()

        match = REVISION_LINE.match(line.rstrip("\n"))
        if match and current_project in {"nrf", "matter"}:
            indent = match.group(1)
            new_revision = nrf_sha if current_project == "nrf" else matter_sha
            newline = "\n" if line.endswith("\n") else ""
            updated_lines.append(f"{indent}revision: {new_revision}{newline}")
            continue

        updated_lines.append(line)

    return "".join(updated_lines)


def update_manifest_file(*, west_yml: Path, nrf_sha: str, matter_sha: str) -> bool:
    original = west_yml.read_text(encoding="utf-8")
    revisions = project_revisions(original)
    old_nrf = revisions.get("nrf")
    old_matter = revisions.get("matter")

    if old_nrf == nrf_sha and old_matter == matter_sha:
        return False

    updated = update_manifest_text(text=original, nrf_sha=nrf_sha, matter_sha=matter_sha)
    west_yml.write_text(updated, encoding="utf-8")
    return True


def commit_and_push(*, west_yml: Path, branch: str, nrf_sha: str, matter_sha: str) -> None:
    configure_git_user()
    run_git(["add", str(west_yml)])
    message = (
        "manifest: Bump nrf/matter revisions for weekly sync\n\n"
        f"nrf revision: {nrf_sha}\n"
        f"matter revision: {matter_sha}\n"
    )
    run_git(["commit", "-m", message])
    push = run_git(["push", "origin", branch], check=False)
    if push.returncode != 0:
        print(push.stderr, file=sys.stderr)
        sys.exit(f"Failed to push manifest update to {branch}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--west-yml", type=Path, default=Path("west.yml"))
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--branch", default="sdk-sync/test")
    args = parser.parse_args()

    state = read_json(args.state_file)
    nrf_sha = state["nrf_sha"]
    matter_sha = state["matter_sha"]

    changed = update_manifest_file(
        west_yml=args.west_yml,
        nrf_sha=nrf_sha,
        matter_sha=matter_sha,
    )
    if not changed:
        print("west.yml already points at the requested revisions")
        return

    commit_and_push(
        west_yml=args.west_yml,
        branch=args.branch,
        nrf_sha=nrf_sha,
        matter_sha=matter_sha,
    )
    print("Updated west.yml and pushed manifest bump commit")


if __name__ == "__main__":
    main()
