#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
"""Validate Sphinx documentation links for the ncs-matter add-on.

Sphinx linkcheck (nitpicky mode) validates :ref:/:doc:/intersphinx targets.
External http(s) URLs are collected by scanning RST sources directly (including
links.txt with substitutions applied) and verified with a browser-like HTTP
client (see docs/checks/conf.py linkcheck_ignore).

Integrated as an optional matter_sample_checker doc check (CheckDocLinksTestCase)
and runnable standalone:

    python3 scripts/matter_sample_checker/checks/docs/check_doc_links.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ProgressCallback = Callable[[str, str], None]

from internal.checker import MatterSampleTestCase
from internal.utils.utils import get_doc_root, get_matter_module_path, get_workspace_root

SPHINX_ISSUE_RE = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+): (?P<level>WARNING|ERROR): (?P<message>.+)$"
)
IGNORED_WARNING_FRAGMENTS = (
    "Duplicate explicit target name",
    "Duplicate target name",
    "image file not readable",
    "Pygments lexer name",
)
API_REF_CATEGORIES = (
    "[ref.struct]",
    "[ref.func]",
    "[ref.var]",
    "[ref.macro]",
    "[ref.enum]",
    "[ref.envvar]",
)
EXTERNAL_CODE_REF_FRAGMENT = "external c:"
EXTERNAL_FILE_REF_FRAGMENT = "external file"
EXTERNAL_CODE_SOURCES_FILE = "external_code_sources.yaml"
LINKCHECK_LINE_RE = re.compile(
    r"^(?:"
    r"(?P<source>.+?):(?P<line>\d+):\s*"
    r"|(?P<output_line>\d+)\s+"
    r")\[(?P<status>[^\]]+)\]\s+"
    r"(?P<uri>\S+?)(?:\s*:\s+(?P<detail>.*))?$"
)


def _normalize_linkcheck_uri(uri: str) -> str:
    """Strip delimiter colons accidentally captured from linkcheck output lines."""
    return uri.rstrip(":")


_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
_LINKCHECK_VERIFY_TIMEOUT_SECS = 30.0
_SPHINX_EXTERNAL_DISCOVERY_PATTERN = r"^https?://"
_RST_SUBSTITUTION_RE = re.compile(r"\.\.\s+\|([^|]+)\|\s+replace::\s+(.*)")
_RAW_HTTP_URL_RE = re.compile(r"https?://[^\s\)\]<>'\"`,]+")
_RST_TARGET_URL_RE = re.compile(r"^\.\.\s+_[^:]+:\s+(https?://\S+)")
_RST_INLINE_LINK_RE = re.compile(r"<(https?://[^>]+)>")
_IFRAME_SRC_RE = re.compile(r'\bsrc="(https?://[^"]+)"')
_UNEXPANDED_SUBSTITUTION_RE = re.compile(r"\|[^|]+\|")


def _load_linkcheck_ignore_patterns(checks_conf: Path) -> list[re.Pattern[str]]:
    """Load ``linkcheck_ignore`` regexes from docs/checks/conf.py."""
    spec = importlib.util.spec_from_file_location("doc_link_checks_conf", checks_conf)
    if spec is None or spec.loader is None:
        return []

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw_patterns = getattr(module, "linkcheck_ignore", [])
    return [re.compile(pattern) for pattern in raw_patterns]


def _matches_linkcheck_ignore(uri: str, skip_patterns: Sequence[re.Pattern[str]]) -> bool:
    """Return True when a URL matches a linkcheck_ignore entry (except the catch-all)."""
    for pattern in skip_patterns:
        if pattern.pattern == _SPHINX_EXTERNAL_DISCOVERY_PATTERN:
            continue
        if pattern.search(uri):
            return True
    return False


def _structural_url_issues(uri: str) -> list[str]:
    """Detect malformed URLs that do not require HTTP to identify as broken."""
    issues: list[str] = []

    if re.search(r"nrfconnectdocs\.nordicsemi\.com/ncs/nrf/", uri):
        issues.append(
            "nrfconnectdocs URL is missing an NCS version segment "
            "(expected /ncs/<version>/nrf/...)"
        )

    if re.search(
        r"github\.com/nrfconnect/sdk-connectedhomeip/tree/"
        r"(scripts|examples|src|config|docs|third_party)/",
        uri,
    ):
        issues.append(
            "sdk-connectedhomeip tree URL is missing a revision segment "
            "(expected /tree/<revision>/...)"
        )

    if "/ncs//" in uri:
        issues.append("URL contains an empty NCS version segment (/ncs//...)")

    return issues


def _verify_external_url(uri: str) -> tuple[bool | None, str]:
    """Verify a URL with a browser-like GET request.

    Returns:
        (True, detail) when the page responds successfully,
        (False, detail) when the link is confirmed broken (e.g. HTTP 404),
        (None, detail) when the server blocks automated clients (e.g. HTTP 403).
    """
    page_url, _, _anchor = uri.partition("#")
    request = Request(
        page_url,
        method="GET",
        headers={
            "User-Agent": _BROWSER_USER_AGENT,
            "Accept": _BROWSER_ACCEPT,
        },
    )
    try:
        with urlopen(request, timeout=_LINKCHECK_VERIFY_TIMEOUT_SECS) as response:
            status = response.status
    except HTTPError as err:
        status = err.code
        if status in {404, 410}:
            return False, f"HTTP {status}"
        if status == 403:
            return None, f"HTTP {status} (remote WAF blocked verification)"
        return False, f"HTTP {status}"
    except URLError as err:
        return None, str(err.reason)

    if 200 <= status < 400:
        return True, f"HTTP {status}"
    if status in {404, 410}:
        return False, f"HTTP {status}"
    if status == 403:
        return None, f"HTTP {status} (remote WAF blocked verification)"
    return False, f"HTTP {status}"


@dataclass(frozen=True)
class DiscoveredExternalLink:
    source: str
    line: int | None
    uri: str
    status: str


def _apply_doc_substitutions(text: str, substitutions: dict[str, str]) -> str:
    previous = None
    current = text
    while previous != current:
        previous = current
        for name, value in substitutions.items():
            current = current.replace(f"|{name}|", value)
    return current


def _clean_extracted_url(raw: str) -> str:
    return raw.rstrip(".,;:)]'\"`")


def _register_substitution(substitutions: dict[str, str], name: str, value: str) -> None:
    """Register a substitution under hyphen and underscore spellings."""
    key = name.strip()
    substitutions[key] = value
    for alt in {key.replace("-", "_"), key.replace("_", "-")}:
        if alt != key:
            substitutions[alt] = value


def _read_rst_substitutions(path: Path) -> dict[str, str]:
    """Load ``.. |name| replace::`` entries preserving the original key spelling."""
    if not path.is_file():
        return {}

    substitutions: dict[str, str] = {}
    for match in _RST_SUBSTITUTION_RE.finditer(path.read_text(encoding="utf-8", errors="replace")):
        _register_substitution(substitutions, match.group(1), match.group(2).strip())
    return substitutions


def _load_doc_substitutions(paths: DocLinksPaths) -> dict[str, str]:
    """Mirror docs/conf.py substitution loading for link URL expansion."""
    sys.path.insert(0, str(paths.docs_dir / "_extensions"))
    substitutions = _read_rst_substitutions(paths.docs_dir / "shortcuts.txt")

    try:
        from west_substitutions import load_west_substitutions
    except ImportError:
        return substitutions

    matter_module = get_matter_module_path(paths.repo_root)
    try:
        for name, value in load_west_substitutions(
            paths.repo_root / "west.yml",
            matter_module=matter_module,
        ).items():
            _register_substitution(substitutions, name, value)
    except (FileNotFoundError, OSError, ValueError):
        pass

    return substitutions


def _unexpanded_substitution_placeholders(uri: str) -> list[str]:
    """Return RST substitution placeholders still present in a URL."""
    return _UNEXPANDED_SUBSTITUTION_RE.findall(uri)


def _collect_link_scan_paths(paths: DocLinksPaths) -> list[Path]:
    """Paths searched for external http(s) URLs (RST bodies plus link registries)."""
    docs_rst = sorted(paths.docs_dir.rglob("*.rst"))
    sample_rst = sorted(paths.repo_root.glob("samples/**/*.rst"))
    extra: list[Path] = []
    links_txt = paths.docs_dir / "links.txt"
    if links_txt.is_file():
        extra.append(links_txt)
    return extra + docs_rst + sample_rst


def _relative_rst_source(paths: DocLinksPaths, path: Path) -> str:
    for root in (paths.docs_dir, paths.repo_root):
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)


def _extract_http_urls_from_line(line: str) -> list[str]:
    urls: list[str] = []
    for pattern in (_RST_TARGET_URL_RE, _RST_INLINE_LINK_RE, _IFRAME_SRC_RE):
        urls.extend(match.group(1) for match in pattern.finditer(line))
    urls.extend(_RAW_HTTP_URL_RE.findall(line))
    return [_clean_extracted_url(url) for url in urls if url.startswith(("http://", "https://"))]


def _scan_rst_file_for_external_links(
    paths: DocLinksPaths,
    path: Path,
    *,
    substitutions: dict[str, str],
) -> list[DiscoveredExternalLink]:
    rel_source = _relative_rst_source(paths, path)
    links: list[DiscoveredExternalLink] = []
    seen: set[tuple[str, int, str]] = set()

    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(),
        start=1,
    ):
        for raw_url in _extract_http_urls_from_line(raw_line):
            uri = _apply_doc_substitutions(raw_url, substitutions)
            if not uri.startswith(("http://", "https://")):
                continue
            key = (rel_source, line_no, uri)
            if key in seen:
                continue
            seen.add(key)
            links.append(
                DiscoveredExternalLink(
                    source=rel_source,
                    line=line_no,
                    uri=uri,
                    status="rst-scan",
                )
            )
    return links


def _scan_rst_sources_for_external_links(
    paths: DocLinksPaths,
    *,
    progress: ProgressLog,
) -> list[DiscoveredExternalLink]:
    """Scan documentation RST sources for http(s) URLs."""
    substitutions = _load_doc_substitutions(paths)
    rst_paths = _collect_link_scan_paths(paths)
    progress.info(f"Scanning {len(rst_paths)} documentation source file(s) for external URLs...")

    links: list[DiscoveredExternalLink] = []
    seen: set[tuple[str, int, str]] = set()
    for path in rst_paths:
        for link in _scan_rst_file_for_external_links(paths, path, substitutions=substitutions):
            key = (link.source, link.line or 0, link.uri)
            if key in seen:
                continue
            seen.add(key)
            links.append(link)

    progress.info(f"RST scan found {len(links)} external URL reference(s)")
    return links


def _verify_discovered_external_links(
    links: Sequence[DiscoveredExternalLink],
    *,
    skip_patterns: Sequence[re.Pattern[str]],
    progress: ProgressLog,
) -> tuple[list[LinkIssue], list[LinkIssue], set[str]]:
    """Verify external URLs discovered from RST sources.

    Every URL is checked with a browser-like GET. Confirmed broken responses
    (HTTP 404/410) are errors even for hosts listed in linkcheck_ignore.
    HTTP 403 on linkcheck_ignore hosts is reported as one aggregated manual-check
    warning because CI runners are often WAF-blocked there. Other unverifiable
    URLs still produce one warning per link.
    """
    verify_cache: dict[str, tuple[bool | None, str]] = {}
    issues: list[LinkIssue] = []
    needs_manual_check: list[LinkIssue] = []
    verified_uris: set[str] = set()
    waf_relaxed_count = 0
    checked_pages = 0
    broken_count = 0
    unverifiable_count = 0

    for link in links:
        issue_source = f"{link.source}:{link.line}" if link.line is not None else link.source
        waf_relaxed = _matches_linkcheck_ignore(link.uri, skip_patterns)

        unexpanded = _unexpanded_substitution_placeholders(link.uri)
        if unexpanded:
            broken_count += 1
            issues.append(
                LinkIssue(
                    check="external-link",
                    source=issue_source,
                    line=link.line,
                    message=(
                        "Unexpanded substitution placeholder(s): "
                        f"{', '.join(unexpanded)}"
                    ),
                    target=link.uri,
                )
            )
            continue

        structural_issues = _structural_url_issues(link.uri)
        if structural_issues:
            broken_count += 1
            issues.append(
                LinkIssue(
                    check="external-link",
                    source=issue_source,
                    line=link.line,
                    message=structural_issues[0],
                    target=link.uri,
                )
            )
            continue

        page_url = link.uri.partition("#")[0]
        if page_url not in verify_cache:
            verify_cache[page_url] = _verify_external_url(link.uri)
            checked_pages += 1

        ok, detail = verify_cache[page_url]

        if ok is True:
            verified_uris.add(link.uri)
            progress.debug(f"Verified OK ({detail}): {link.uri}")
            continue
        if ok is False:
            broken_count += 1
            issues.append(
                LinkIssue(
                    check="external-link",
                    source=issue_source,
                    line=link.line,
                    message=detail,
                    target=link.uri,
                )
            )
            continue

        unverifiable_count += 1
        if waf_relaxed:
            waf_relaxed_count += 1
            progress.debug(
                f"Unverifiable from CI ({detail}, linkcheck_ignore host): "
                f"{issue_source} -> {link.uri}"
            )
            continue

        needs_manual_check.append(
            LinkIssue(
                check="external-link",
                source=issue_source,
                line=link.line,
                message=(
                    f"Unverifiable from CI ({detail}). Open {page_url} in a browser "
                    "to confirm the link is valid."
                ),
                target=link.uri,
            )
        )
        progress.debug(f"Needs manual check ({detail}): {issue_source} -> {link.uri}")

    if waf_relaxed_count:
        needs_manual_check.insert(
            0,
            LinkIssue(
                check="external-link",
                source=str(Path("docs/checks/conf.py")),
                line=None,
                message=(
                    f"{waf_relaxed_count} external link reference(s) on linkcheck_ignore "
                    "hosts returned HTTP 403 from CI (WAF). These URLs were not verified "
                    "automatically; spot-check representative links in a browser if needed."
                ),
            ),
        )

    progress.info(
        "External link verification (RST scan): "
        f"{len(links)} reference(s), {checked_pages} unique page(s) checked, "
        f"{broken_count} broken, {unverifiable_count} unverifiable from CI "
        f"({waf_relaxed_count} on linkcheck_ignore hosts, reported as one summary warning)"
    )
    return issues, needs_manual_check, verified_uris


SPHINX_PERCENT_RE = re.compile(r"\[\s*(\d+)%\]\s*(.*)$")
SPHINX_PHASE_RE = re.compile(
    r"(reading sources|looking for now-outdated files|checking consistency|"
    r"pickling environment|preparing documents|writing output|"
    r"running linkcheck|loading pickled environment)",
    re.IGNORECASE,
)


class ProgressLog:
    """Route progress messages to stderr (CLI) or checker info/debug callbacks."""

    def __init__(
        self,
        *,
        quiet: bool = False,
        callback: ProgressCallback | None = None,
    ) -> None:
        self.quiet = quiet
        self.callback = callback
        self._last_percent = -1

    def info(self, message: str) -> None:
        if self.callback is not None:
            self.callback("info", message)
        elif not self.quiet:
            print(message, file=sys.stderr)

    def debug(self, message: str) -> None:
        if self.callback is not None:
            self.callback("debug", message)
        elif not self.quiet:
            print(message, file=sys.stderr)

    def sphinx_line(self, line: str) -> None:
        stripped = line.strip()
        if not stripped:
            return

        percent_match = SPHINX_PERCENT_RE.search(stripped)
        if percent_match:
            percent = int(percent_match.group(1))
            detail = percent_match.group(2).strip()
            if percent >= self._last_percent + 10 or percent == 100:
                self._last_percent = percent
                suffix = f": {detail}" if detail else ""
                self.info(f"Sphinx progress {percent}%{suffix}")
            elif detail.endswith(".rst"):
                self.debug(f"Reading {detail}")
            return

        if SPHINX_PHASE_RE.search(stripped):
            self.info(stripped)
            return

        if stripped.endswith(".rst") or ".rst:" in stripped:
            self.debug(stripped)

    def reset_percent(self) -> None:
        self._last_percent = -1

    def replay_log(self, heading: str, lines: Sequence[str]) -> None:
        if self.quiet or not lines:
            return
        self.info(heading)
        for line in lines:
            self.info(f"  {line}")


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _sphinx_log_lines(log_text: str) -> list[str]:
    """Extract warning/error lines from a Sphinx build or warning log."""
    lines: list[str] = []
    seen: set[str] = set()

    for raw_line in log_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("$ ") or stripped.startswith("exit_code:"):
            continue
        if SPHINX_PERCENT_RE.search(stripped) or SPHINX_PHASE_RE.search(stripped):
            continue

        normalized = stripped
        match = SPHINX_ISSUE_RE.match(raw_line)
        if match:
            normalized = (
                f"{match.group('file')}:{match.group('line')}: "
                f"{match.group('level')}: {match.group('message')}"
            )
        elif stripped.startswith("WARNING: ") or stripped.startswith("ERROR: "):
            normalized = stripped
        elif " WARNING:" not in raw_line and " ERROR:" not in raw_line:
            continue

        if normalized not in seen:
            seen.add(normalized)
            lines.append(normalized)

    return lines


_SPHINX_FAILURE_KEYWORDS = (
    "error",
    "exception",
    "traceback",
    "failed",
    "fatal",
    "not found",
    "does not exist",
)


def _is_sphinx_progress_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("$ ") or stripped.startswith("exit_code:"):
        return True
    if SPHINX_PERCENT_RE.search(stripped) or SPHINX_PHASE_RE.search(stripped):
        return True
    return stripped.endswith(".rst") and ":" not in stripped


def _extract_unparsed_sphinx_failures(log_text: str, *, max_lines: int = 20) -> list[str]:
    """Return diagnostic lines when sphinx-build failed but normal parsers found nothing."""
    parsed = _sphinx_log_lines(log_text)
    if parsed:
        return parsed[:max_lines]

    candidates: list[str] = []
    seen: set[str] = set()
    for raw_line in log_text.splitlines():
        if _is_sphinx_progress_noise(raw_line):
            continue
        stripped = raw_line.strip()
        lower = stripped.lower()
        if any(keyword in lower for keyword in _SPHINX_FAILURE_KEYWORDS):
            if stripped not in seen:
                seen.add(stripped)
                candidates.append(stripped)

    if candidates:
        return candidates[:max_lines]

    tail: list[str] = []
    for raw_line in reversed(log_text.splitlines()):
        if _is_sphinx_progress_noise(raw_line):
            continue
        tail.append(raw_line.strip())
        if len(tail) >= max_lines:
            break
    return list(reversed(tail))


def _link_issue_from_sphinx_log_line(line: str, *, fallback_source: str) -> LinkIssue:
    match = SPHINX_ISSUE_RE.match(line)
    if match:
        return LinkIssue(
            check="cross-reference",
            source=match.group("file"),
            line=int(match.group("line")),
            message=match.group("message"),
        )

    if line.startswith("WARNING: ") or line.startswith("ERROR: "):
        return LinkIssue(
            check="cross-reference",
            source="conf.py",
            line=None,
            message=line.removeprefix("WARNING: ").removeprefix("ERROR: ").strip(),
        )

    return LinkIssue(
        check="cross-reference",
        source=fallback_source,
        line=None,
        message=line,
    )


def _linkcheck_output_lines(
    output_text: str,
    *,
    verified_uris: set[str] | None = None,
    needs_check_uris: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Split linkcheck output.txt lines into info (broken) and debug (other) buckets."""
    info_lines: list[str] = []
    debug_lines: list[str] = []
    seen: set[str] = set()

    for raw_line in output_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)

        match = LINKCHECK_LINE_RE.match(stripped)
        if match:
            status = match.group("status")
            uri = _normalize_linkcheck_uri(match.group("uri"))
            detail = (match.group("detail") or "").strip()
            source = match.group("source")
            line_no = match.group("line") or match.group("output_line")
            location = f"{source}:{line_no}" if source and line_no else f"linkcheck:{line_no or '?'}"
            suffix = f" ({detail})" if detail else ""
            message = f"{location}: [{status}] {uri}{suffix}"
            if status.startswith("broken"):
                if verified_uris and uri in verified_uris:
                    debug_lines.append(f"{message} (verified externally after Sphinx discovery)")
                elif needs_check_uris and uri in needs_check_uris:
                    debug_lines.append(
                        f"{message} (NOT a confirmed failure -- see the "
                        "'needs manual verification' warnings for what to do)"
                    )
                else:
                    info_lines.append(message)
            else:
                debug_lines.append(message)
            continue

        if "[broken" in stripped.lower():
            info_lines.append(stripped)
        elif "[redirected" in stripped.lower() or "[ignored" in stripped.lower():
            debug_lines.append(stripped)
        else:
            debug_lines.append(stripped)

    return info_lines, debug_lines


def _emit_documentation_link_logs(
    progress: ProgressLog,
    log_path: Path,
    output_path: Path,
    *,
    sphinx_exit_code: int = 0,
    verified_uris: set[str] | None = None,
    needs_check_uris: set[str] | None = None,
) -> None:
    log_text = _read_text(log_path)
    warning_lines = _sphinx_log_lines(log_text)
    broken_lines, other_lines = _linkcheck_output_lines(
        _read_text(output_path),
        verified_uris=verified_uris,
        needs_check_uris=needs_check_uris,
    )

    if warning_lines:
        progress.replay_log("Sphinx documentation link log:", warning_lines)
    elif sphinx_exit_code != 0 and not progress.quiet:
        diagnostic_lines = _extract_unparsed_sphinx_failures(log_text)
        if diagnostic_lines:
            progress.replay_log(
                f"Sphinx linkcheck exited with code {sphinx_exit_code}; diagnostic log excerpt:",
                diagnostic_lines,
            )
        else:
            progress.info(
                f"Sphinx linkcheck exited with code {sphinx_exit_code}; "
                f"see {log_path} for details"
            )
    elif not progress.quiet:
        progress.info("Sphinx documentation link log: no warnings or errors recorded")

    if broken_lines:
        progress.replay_log("External linkcheck broken URLs:", broken_lines)
    elif not progress.quiet:
        progress.info("External linkcheck broken URLs: none")

    if other_lines:
        progress.info("External linkcheck other results:")
        for line in other_lines:
            progress.debug(f"  {line}")


@dataclass(frozen=True)
class DocLinksPaths:
    docs_dir: Path
    checks_conf_dir: Path
    repo_root: Path
    ncs_root: Path

    @property
    def checks_conf(self) -> Path:
        return self.checks_conf_dir / "conf.py"

    @property
    def requirements(self) -> Path:
        return self.docs_dir / "requirements-doc.txt"


@dataclass
class LinkIssue:
    check: str
    source: str
    line: int | None
    message: str
    target: str = ""


@dataclass
class CheckReport:
    success: bool
    refs_checked: bool
    external_checked: bool
    intersphinx_docsets: list[str] = field(default_factory=list)
    issues: list[LinkIssue] = field(default_factory=list)
    needs_manual_check: list[LinkIssue] = field(default_factory=list)
    log_paths: dict[str, str] = field(default_factory=dict)


def resolve_doc_links_paths(
    base: Path,
    config: dict[str, Any] | None = None,
) -> DocLinksPaths:
    """Resolve documentation paths relative to the ncs-matter workspace base."""
    repo_root = get_workspace_root(base) if config is not None else base.resolve()
    doc_root = get_doc_root(base, config) if config is not None else repo_root
    docs_dir = doc_root / "docs"
    return DocLinksPaths(
        docs_dir=docs_dir,
        checks_conf_dir=docs_dir / "checks",
        repo_root=repo_root,
        ncs_root=repo_root.parent,
    )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def count_doc_sources(paths: DocLinksPaths) -> int:
    """Count RST files that Sphinx will scan in the add-on documentation set."""
    docs_rst = list(paths.docs_dir.rglob("*.rst"))
    sample_rst = list(paths.repo_root.glob("samples/**/*.rst"))
    return len(docs_rst) + len(sample_rst)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_sphinx(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "sphinx-build.exe"
    return venv_dir / "bin" / "sphinx-build"


def ensure_sphinx(paths: DocLinksPaths, venv_dir: Path, *, progress: ProgressLog) -> Path:
    sphinx = _venv_sphinx(venv_dir)
    if sphinx.is_file():
        progress.debug(f"Using existing Sphinx venv: {venv_dir}")
        return sphinx

    if not paths.requirements.is_file():
        raise FileNotFoundError(f"Missing documentation requirements: {paths.requirements}")

    progress.info(f"Creating documentation venv at {venv_dir}")

    venv.create(venv_dir, with_pip=True)
    python = _venv_python(venv_dir)
    pip_cmd = [str(python), "-m", "pip", "install", "-r", str(paths.requirements)]
    if progress.quiet:
        pip_cmd.extend(["-q", "--progress-bar", "off"])

    subprocess.run(pip_cmd, check=True)
    if not sphinx.is_file():
        raise RuntimeError(f"sphinx-build not found after installing {paths.requirements}")
    return sphinx


def run_doxygen_if_needed(paths: DocLinksPaths, *, quiet: bool) -> bool:
    doxyfile = paths.docs_dir / "Doxyfile"
    xml_index = paths.docs_dir / "_build_doxygen" / "xml" / "index.xml"
    if xml_index.is_file() or not doxyfile.is_file():
        return xml_index.is_file()

    if shutil.which("doxygen") is None:
        if not quiet:
            print(
                "Doxygen XML not found; skipping Breathe C API reference checks. "
                "Install doxygen and rebuild, or run a normal docs build first.",
                file=sys.stderr,
            )
        return False

    if not quiet:
        print("Running Doxygen for Breathe cross-references...", file=sys.stderr)

    proc = subprocess.run(
        ["doxygen", "Doxyfile"],
        cwd=str(paths.docs_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 and not quiet:
        print(
            f"Doxygen failed (exit {proc.returncode}); C API references may be reported "
            "as broken.",
            file=sys.stderr,
        )
    return xml_index.is_file()


def _external_code_registry_path(paths: DocLinksPaths) -> Path:
    return paths.docs_dir / EXTERNAL_CODE_SOURCES_FILE


def _load_redirect_allowlist(paths: DocLinksPaths) -> list[Any]:
    sys.path.insert(0, str(paths.docs_dir / "_extensions"))
    try:
        from external_code_registry import load_link_redirect_allowlist
    except ImportError:
        return []
    return load_link_redirect_allowlist(_external_code_registry_path(paths))


def _is_allowlisted_redirect_warning(message: str, allowlist: Sequence[Any]) -> bool:
    if not message.startswith("redirect"):
        return False
    return any(getattr(entry, "url", "") in message for entry in allowlist)


def check_external_code_registry(paths: DocLinksPaths) -> list[LinkIssue]:
    """Verify :external:c:*: and :external:file: roles against external_code_sources.yaml."""
    sys.path.insert(0, str(paths.docs_dir / "_extensions"))
    try:
        from external_code_registry import (
            load_documentation_substitutions,
            load_external_code_registry,
            validate_external_code_references,
            validate_external_file_references,
            validate_local_references,
        )
    except ImportError as exc:
        return [
            LinkIssue(
                check="external-code",
                source=str(_external_code_registry_path(paths)),
                line=None,
                message=f"unable to import external code registry helpers: {exc}",
            )
        ]

    registry_path = _external_code_registry_path(paths)
    if not registry_path.is_file():
        return [
            LinkIssue(
                check="external-code",
                source=str(registry_path),
                line=None,
                message=f"missing external code sources registry: {registry_path.name}",
            )
        ]

    try:
        substitutions = load_documentation_substitutions(
            paths.docs_dir / "shortcuts.txt",
            repo_root_path=paths.repo_root,
            west_manifest_path=paths.repo_root / "west.yml",
            matter_module_path=paths.ncs_root / "modules" / "lib" / "matter",
        )
        registry = load_external_code_registry(registry_path, substitutions=substitutions)
        raw_issues = validate_external_code_references(paths.docs_dir, registry)
        raw_issues.extend(validate_external_file_references(paths.docs_dir, registry))
        raw_issues.extend(
            validate_local_references(
                paths.docs_dir,
                repo_root_path=paths.repo_root,
            )
        )
    except (OSError, ValueError) as exc:
        return [
            LinkIssue(
                check="external-code",
                source=str(registry_path),
                line=None,
                message=str(exc),
            )
        ]

    return [
        LinkIssue(
            check="external-code",
            source=issue["source"],
            line=issue["line"],
            message=issue["message"],
            target=issue["name"],
        )
        for issue in raw_issues
    ]


def discover_intersphinx_docsets(paths: DocLinksPaths) -> list[str]:
    docsets: list[str] = []
    for docset, rel_path in (
        ("nrf", "nrf/doc/_build/html/nrf/objects.inv"),
        ("zephyr", "nrf/doc/_build/html/zephyr/objects.inv"),
        ("kconfig", "nrf/doc/_build/html/kconfig/objects.inv"),
        ("nrfxlib", "nrf/doc/_build/html/nrfxlib/objects.inv"),
        ("mcuboot", "nrf/doc/_build/html/mcuboot/objects.inv"),
        ("tfm", "nrf/doc/_build/html/tfm/objects.inv"),
        ("matter", "nrf/doc/_build/html/matter/objects.inv"),
    ):
        if (paths.ncs_root / rel_path).is_file():
            docsets.append(docset)
    return docsets


def _parse_ref_issues(
    log_text: str,
    *,
    include_api_refs: bool,
    redirect_allowlist: Sequence[Any] | None = None,
) -> list[LinkIssue]:
    issues: list[LinkIssue] = []
    seen: set[tuple[str, int, str]] = set()

    for raw_line in log_text.splitlines():
        if raw_line.startswith("WARNING: ") and "does not exist" in raw_line:
            issues.append(
                LinkIssue(
                    check="cross-reference",
                    source="conf.py",
                    line=None,
                    message=raw_line.removeprefix("WARNING: ").strip(),
                )
            )
            continue

        match = SPHINX_ISSUE_RE.match(raw_line)
        if not match:
            continue

        message = match.group("message")
        if redirect_allowlist and _is_allowlisted_redirect_warning(message, redirect_allowlist):
            continue
        if any(fragment in message for fragment in IGNORED_WARNING_FRAGMENTS):
            continue
        if EXTERNAL_CODE_REF_FRAGMENT in message:
            pass
        elif not include_api_refs and any(category in message for category in API_REF_CATEGORIES):
            continue

        key = (match.group("file"), int(match.group("line")), message)
        if key in seen:
            continue
        seen.add(key)

        issues.append(
            LinkIssue(
                check="cross-reference",
                source=match.group("file"),
                line=int(match.group("line")),
                message=message,
            )
        )
    return issues


def run_sphinx(
    paths: DocLinksPaths,
    sphinx: Path,
    builder: str,
    out_dir: Path,
    log_path: Path,
    *,
    extra_args: Sequence[str] = (),
    progress: ProgressLog | None = None,
) -> subprocess.CompletedProcess[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(sphinx),
        "-c",
        str(paths.checks_conf_dir),
        "-b",
        builder,
        str(paths.docs_dir),
        str(out_dir),
        "-w",
        str(log_path),
        *extra_args,
    ]
    merged_output: list[str] = []
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(cmd)}\n\n")
        log_file.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=str(paths.docs_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            merged_output.append(line)
            log_file.write(line)
            log_file.flush()
            if progress is not None:
                progress.sphinx_line(line)

        returncode = proc.wait()
        log_file.write(f"\nexit_code: {returncode}\n")

    return subprocess.CompletedProcess(cmd, returncode, "".join(merged_output), "")


def check_documentation_links(
    paths: DocLinksPaths,
    sphinx: Path,
    work_dir: Path,
    *,
    progress: ProgressLog,
    include_api_refs: bool = False,
) -> tuple[list[LinkIssue], list[LinkIssue], str, str]:
    """Run Sphinx linkcheck for cross-refs; verify external URLs from RST scan."""
    log_path = work_dir / "linkcheck.log"
    out_dir = work_dir / "linkcheck"
    progress.info(
        "Checking documentation cross-references (:ref:, :doc:, intersphinx) "
        f"across {count_doc_sources(paths)} RST files..."
    )

    progress.reset_percent()
    proc = run_sphinx(
        paths,
        sphinx,
        "linkcheck",
        out_dir,
        log_path,
        extra_args=["-n", "-W", "--keep-going"],
        progress=progress,
    )

    log_text = _read_text(log_path)
    if proc.stdout:
        log_text = f"{log_text}\n{proc.stdout}".strip()

    output_txt = out_dir / "output.txt"
    redirect_allowlist = _load_redirect_allowlist(paths)
    skip_patterns = _load_linkcheck_ignore_patterns(paths.checks_conf)
    ref_issues = _parse_ref_issues(
        log_text,
        include_api_refs=include_api_refs,
        redirect_allowlist=redirect_allowlist,
    )
    discovered_links = _scan_rst_sources_for_external_links(paths, progress=progress)
    ext_issues, needs_manual_check, verified_uris = _verify_discovered_external_links(
        discovered_links,
        skip_patterns=skip_patterns,
        progress=progress,
    )
    issues = ref_issues + ext_issues

    if proc.returncode != 0 and not issues and not needs_manual_check:
        failure_lines = _extract_unparsed_sphinx_failures(log_text)
        if failure_lines:
            issues.extend(
                _link_issue_from_sphinx_log_line(line, fallback_source=str(log_path))
                for line in failure_lines
            )
        else:
            issues.append(
                LinkIssue(
                    check="cross-reference",
                    source=str(log_path),
                    line=None,
                    message=(
                        f"sphinx-build linkcheck failed (exit {proc.returncode}) "
                        "without parseable diagnostics; inspect the Sphinx log above"
                    ),
                )
            )

    progress.info(
        "Documentation link check finished with "
        f"{len(ref_issues)} cross-reference issue(s), "
        f"{len(ext_issues)} broken external URL(s), and "
        f"{len(needs_manual_check)} external URL(s) needing manual verification"
    )
    _emit_documentation_link_logs(
        progress,
        log_path,
        output_txt,
        sphinx_exit_code=proc.returncode,
        verified_uris=verified_uris,
        needs_check_uris={issue.target for issue in needs_manual_check},
    )
    return issues, needs_manual_check, str(log_path), str(output_txt)


def run_checks(
    paths: DocLinksPaths,
    *,
    venv_dir: Path | None = None,
    quiet: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> CheckReport:
    if not paths.checks_conf.is_file():
        raise FileNotFoundError(f"Missing link check configuration: {paths.checks_conf}")

    progress = ProgressLog(quiet=quiet, callback=progress_callback)
    source_count = count_doc_sources(paths)
    progress.info(f"Documentation link check started ({source_count} RST sources)")
    progress.debug(f"Docs directory: {paths.docs_dir}")
    progress.debug(f"Sphinx overlay: {paths.checks_conf}")

    chosen_venv = venv_dir or Path(
        os.environ.get(
            "DOC_LINKCHECK_VENV",
            str(Path(tempfile.gettempdir()) / "ncs-matter-doc-linkcheck-venv"),
        )
    )
    sphinx = ensure_sphinx(paths, chosen_venv, progress=progress)
    intersphinx_docsets = discover_intersphinx_docsets(paths)

    if intersphinx_docsets:
        progress.info("Using intersphinx inventories: " + ", ".join(intersphinx_docsets))
    else:
        progress.info(
            "No local NCS docset inventories found; only in-addon :ref: targets "
            "will be validated. Build sdk-nrf docs to enable cross-docset checks."
        )

    work_dir = Path(tempfile.mkdtemp(prefix="ncs-matter-linkcheck-"))
    progress.debug(f"Temporary work directory: {work_dir}")
    all_issues: list[LinkIssue] = []
    all_needs_manual_check: list[LinkIssue] = []
    log_paths: dict[str, str] = {}

    try:
        external_code_issues = check_external_code_registry(paths)
        if external_code_issues:
            progress.info(
                f"Found {len(external_code_issues)} external code reference issue(s) "
                f"in {EXTERNAL_CODE_SOURCES_FILE}"
            )
        all_issues.extend(external_code_issues)

        link_issues, needs_manual_check, link_log, link_output = check_documentation_links(
            paths,
            sphinx,
            work_dir,
            progress=progress,
            include_api_refs=False,
        )
        all_issues.extend(link_issues)
        all_needs_manual_check.extend(needs_manual_check)
        log_paths["linkcheck_log"] = link_log
        log_paths["linkcheck_output"] = link_output

        progress.info(
            f"Documentation link check completed with {len(all_issues)} real error(s) and "
            f"{len(all_needs_manual_check)} link(s) needing manual verification"
        )

        return CheckReport(
            success=not all_issues,
            refs_checked=True,
            external_checked=True,
            intersphinx_docsets=intersphinx_docsets,
            issues=all_issues,
            needs_manual_check=all_needs_manual_check,
            log_paths=log_paths,
        )
    finally:
        if os.environ.get("DOC_LINKCHECK_KEEP_WORKDIR") != "1":
            shutil.rmtree(work_dir, ignore_errors=True)


def _format_link_issue(issue: LinkIssue) -> str:
    location = issue.source
    if issue.line is not None and not re.search(r":\d+$", issue.source):
        location = f"{issue.source}:{issue.line}"
    if issue.target:
        return f"[{issue.check}] {location}: {issue.message} ({issue.target})"
    return f"[{issue.check}] {location}: {issue.message}"


def _print_human_report(report: CheckReport) -> None:
    if report.success and not report.needs_manual_check:
        print("All documentation link checks passed.")
        if report.intersphinx_docsets:
            print("Intersphinx docsets:", ", ".join(report.intersphinx_docsets))
        return

    if report.issues:
        print(f"Stage 1 -- {len(report.issues)} real error(s) (fail the build):")
        print("!" * 60)
        for index, issue in enumerate(report.issues, start=1):
            print(f"  [{index}] {_format_link_issue(issue)}")
        print("!" * 60)
        print()
    else:
        print("Stage 1 -- no real errors.\n")

    if report.needs_manual_check:
        print(
            f"Stage 2 -- {len(report.needs_manual_check)} manual verification "
            "note(s) (do NOT fail the build):\n"
        )
        for issue in report.needs_manual_check:
            print(_format_link_issue(issue))
            if issue.target:
                print()

    if report.log_paths:
        print("Logs:")
        for name, path in report.log_paths.items():
            print(f"  {name}: {path}")


class CheckDocLinksTestCase(MatterSampleTestCase):
    """Validate Sphinx :ref:, :doc:, and external documentation links (optional check)."""

    def __init__(self):
        super().__init__()
        self.paths: DocLinksPaths | None = None
        self.skip_check = False

    def name(self) -> str:
        return "Documentation links check"

    def prepare(self):
        try:
            self.paths = resolve_doc_links_paths(
                self.config.nrf_path,
                self.config.config_file,
            )
            if not self.paths.checks_conf.is_file():
                raise FileNotFoundError(f"Missing link check configuration: {self.paths.checks_conf}")
        except Exception as exc:
            self.skip_check = True
            self.info(f"Optional documentation links check skipped: {exc}")

    def _log_progress(self, level: str, message: str) -> None:
        if level == "info":
            self.info(message)
        else:
            self.debug(message)

    def check(self):
        if self.skip_check or self.paths is None:
            return

        try:
            report = run_checks(
                self.paths,
                quiet=False,
                progress_callback=self._log_progress,
            )
        except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
            self.warning(f"Optional documentation links check skipped: {exc}")
            return

        for link_issue in report.issues:
            self.issue(_format_link_issue(link_issue))

        for link_issue in report.needs_manual_check:
            self.warning(_format_link_issue(link_issue))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Sphinx :ref:/:doc: cross-references and live external URLs in ncs-matter docs."
        ),
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=_default_repo_root(),
        help="Path to the ncs-matter repository root.",
    )
    parser.add_argument(
        "--venv-dir",
        type=Path,
        default=None,
        help="Reuse or create a Python venv with Sphinx (default: temp venv).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Reduce progress output (still prints failures unless --json).",
    )
    args = parser.parse_args(argv)

    paths = resolve_doc_links_paths(args.repo_path.resolve())

    try:
        report = run_checks(
            paths,
            venv_dir=args.venv_dir,
            quiet=args.quiet or args.json,
        )
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        if args.json:
            print(json.dumps({"success": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    elif not args.quiet or not report.success or report.needs_manual_check:
        _print_human_report(report)

    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
