# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

"""Post Twister results on the sync PR and dispatch Copilot analysis."""

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

from common import (  # noqa: E402
    COPILOT_TRIGGER_MARKER,
    github_get_paginated,
    github_headers,
    github_token,
    parse_verified_pr_number,
    parse_verified_workflow_run_id,
    parse_verified_workflow_run_url,
)

AGENT_API_VERSION = "2026-03-10"
COPILOT_COMMENT_TRIGGER = "/copilot analyze-sdk-sync-twister"
CUSTOM_AGENT = "sdk-sync-twister-analyzer"
MAX_PROMPT_CHARS = 12000
MAX_ARTIFACT_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_ARTIFACT_FILES = frozenset(
    {
        "pr_number.txt",
        "workflow_conclusion.txt",
        "twister-console.log",
        "twister.log",
        "twister.json",
    }
)
ALLOWED_WORKFLOW_CONCLUSIONS = frozenset({"success", "failure", "cancelled"})


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")


def validate_artifact_dir(*, artifact_dir: Path, expected_pr_number: int) -> None:
    if not artifact_dir.is_dir():
        sys.exit(f"Artifact directory not found: {artifact_dir}")

    found_files = {path.name for path in artifact_dir.iterdir() if path.is_file()}
    unexpected = found_files - ALLOWED_ARTIFACT_FILES
    if unexpected:
        sys.exit(f"Unexpected artifact files: {sorted(unexpected)}")

    for name in found_files:
        size = (artifact_dir / name).stat().st_size
        if size > MAX_ARTIFACT_FILE_BYTES:
            sys.exit(f"Artifact file too large: {name} ({size} bytes)")

    artifact_pr = read_text(artifact_dir / "pr_number.txt").strip()
    if artifact_pr:
        if not artifact_pr.isdigit():
            sys.exit(f"Invalid PR number in artifact: {artifact_pr!r}")
        if int(artifact_pr) != expected_pr_number:
            sys.exit(
                f"Artifact pr_number ({artifact_pr}) does not match verified PR "
                f"({expected_pr_number})"
            )

    conclusion = read_text(artifact_dir / "workflow_conclusion.txt").strip()
    if conclusion and conclusion not in ALLOWED_WORKFLOW_CONCLUSIONS:
        sys.exit(f"Invalid workflow conclusion in artifact: {conclusion!r}")


def extract_failed_tests(twister_json_path: Path) -> list[dict[str, str]]:
    if not twister_json_path.is_file():
        return []

    try:
        payload = json.loads(twister_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    failures: list[dict[str, str]] = []
    for testsuite in payload.get("testsuites", []):
        status = str(testsuite.get("status", "")).upper()
        if status not in {"FAIL", "ERROR", "SKIPPED", "FILTERED"}:
            continue
        if status == "SKIPPED":
            continue
        failures.append(
            {
                "platform": str(testsuite.get("platform", "unknown")),
                "scenario": str(testsuite.get("name", "unknown")),
                "status": status,
                "reason": str(testsuite.get("reason", "")).strip(),
            }
        )
    return failures


def build_failure_summary(*, artifact_dir: Path) -> tuple[str, bool]:
    conclusion = read_text(artifact_dir / "workflow_conclusion.txt").strip() or "unknown"
    failures = extract_failed_tests(artifact_dir / "twister.json")
    console_log = read_text(artifact_dir / "twister-console.log")
    twister_log = read_text(artifact_dir / "twister.log")

    has_errors = conclusion != "success" or bool(failures)
    lines = [
        f"Workflow conclusion: `{conclusion}`",
        f"Failed Twister scenarios: {len(failures)}",
    ]

    if failures:
        lines.append("")
        lines.append("Failed builds:")
        for item in failures[:40]:
            reason = f" — {item['reason']}" if item["reason"] else ""
            lines.append(
                f"- `{item['platform']}` / `{item['scenario']}` ({item['status']}){reason}"
            )
        if len(failures) > 40:
            lines.append(f"- … and {len(failures) - 40} more")

    log_source = twister_log or console_log
    if log_source:
        error_lines = [
            line
            for line in log_source.splitlines()
            if any(token in line for token in ("ERROR", "error:", "FAILED", "Failure", "CMake Error"))
        ]
        if error_lines:
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>Extracted error lines</summary>")
            lines.append("")
            lines.append("```text")
            lines.extend(error_lines[-80:])
            lines.append("```")
            lines.append("</details>")

    return "\n".join(lines), has_errors


def find_existing_trigger_comment(*, repo: str, pr_number: int, workflow_run_id: str) -> int | None:
    marker = f"{COPILOT_TRIGGER_MARKER} run:{workflow_run_id}"
    comments = github_get_paginated(f"/repos/{repo}/issues/{pr_number}/comments")
    for comment in comments:
        body = comment.get("body", "")
        if marker in body:
            return int(comment["id"])
    return None


def upsert_trigger_comment(
    *,
    repo: str,
    pr_number: int,
    workflow_run_id: str,
    workflow_run_url: str,
    summary: str,
    task_url: str | None,
) -> None:
    marker = f"{COPILOT_TRIGGER_MARKER} run:{workflow_run_id}"
    task_line = f"- Copilot task: {task_url}" if task_url else "- Copilot task: dispatch failed (see workflow logs)"
    body = f"""{marker}

## SDK sync Twister analysis requested

Workflow run: {workflow_run_url}

{summary}

{COPILOT_COMMENT_TRIGGER}

Automated follow-up:
{task_line}
"""
    existing_id = find_existing_trigger_comment(
        repo=repo, pr_number=pr_number, workflow_run_id=workflow_run_id
    )
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
    print(f"{action} Copilot trigger comment on PR #{pr_number}")


def agent_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {github_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": AGENT_API_VERSION,
    }


def dispatch_copilot_task(
    *,
    repo: str,
    prompt: str,
    head_ref: str,
    base_ref: str,
) -> str | None:
    response = requests.post(
        f"https://api.github.com/agents/repos/{repo}/tasks",
        headers=agent_headers(),
        json={
            "prompt": prompt,
            "head_ref": head_ref,
            "base_ref": base_ref,
            "create_pull_request": False,
            "custom_agent": CUSTOM_AGENT,
        },
        timeout=60,
    )
    if response.status_code >= 400:
        print(
            f"Copilot agent dispatch failed: {response.status_code} {response.text}",
            file=sys.stderr,
        )
        return None

    payload = response.json()
    task_id = payload.get("id")
    if not task_id:
        print(f"Copilot agent dispatch returned no task id: {payload}", file=sys.stderr)
        return None

    owner, name = repo.split("/", 1)
    return f"https://github.com/{owner}/{name}/agents/tasks/{task_id}"


def build_agent_prompt(
    *,
    pr_number: int,
    workflow_run_url: str,
    summary: str,
    artifact_dir: Path,
) -> str:
    console_tail = read_text(artifact_dir / "twister-console.log")
    twister_tail = read_text(artifact_dir / "twister.log")
    log_tail = (twister_tail or console_tail)[-MAX_PROMPT_CHARS:]

    return f"""Analyze the SDK sync Twister build results for PR #{pr_number}.

Context:
- This is the weekly automated sync PR (`sdk-sync/test` -> `sdk-nrf`) for nrfconnect/ncs-matter.
- Twister scenario: `sample.matter.template.debug` on all integration platforms.
- Workflow run: {workflow_run_url}

Summary:
{summary}

Instructions:
1. Investigate the Twister failures and identify root causes (manifest drift, Kconfig, sample code, upstream sdk-nrf/Matter regressions).
2. Group failures by error pattern and affected platforms.
3. Post a concise analysis comment on PR #{pr_number} with recommended next steps.
4. Do not open a new pull request. Only propose code changes in the analysis comment unless a one-line manifest fix is obvious and safe.

Recent Twister log tail:
```text
{log_tail}
```
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nrfconnect/ncs-matter"))
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--from-env", action="store_true", help="Read verified values from environment")
    parser.add_argument("--head-ref", default="sdk-sync/test")
    parser.add_argument("--base-ref", default="sdk-nrf")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Dispatch Copilot even when Twister succeeded with no failures",
    )
    args = parser.parse_args()

    if not args.from_env:
        sys.exit("--from-env is required")

    _ = github_token()

    pr_number = parse_verified_pr_number(os.environ.get("PR_NUMBER", ""))
    workflow_run_id = parse_verified_workflow_run_id(os.environ.get("WORKFLOW_RUN_ID", ""))
    workflow_run_url = parse_verified_workflow_run_url(os.environ.get("WORKFLOW_RUN_URL", ""))

    validate_artifact_dir(artifact_dir=args.artifact_dir, expected_pr_number=pr_number)

    summary, has_errors = build_failure_summary(artifact_dir=args.artifact_dir)
    if not args.force and not has_errors:
        print("Twister run succeeded with no failures; skipping Copilot dispatch")
        return

    prompt = build_agent_prompt(
        pr_number=pr_number,
        workflow_run_url=workflow_run_url,
        summary=summary,
        artifact_dir=args.artifact_dir,
    )
    task_url = dispatch_copilot_task(
        repo=args.repo,
        prompt=prompt,
        head_ref=args.head_ref,
        base_ref=args.base_ref,
    )
    upsert_trigger_comment(
        repo=args.repo,
        pr_number=pr_number,
        workflow_run_id=workflow_run_id,
        workflow_run_url=workflow_run_url,
        summary=summary,
        task_url=task_url,
    )


if __name__ == "__main__":
    main()
