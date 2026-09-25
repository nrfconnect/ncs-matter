# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

"""Load and resolve external C API symbols and file paths for Sphinx roles."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

SUPPORTED_KINDS = frozenset({'struct', 'func', 'var', 'enum', 'macro', 'type', 'member'})

EXTERNAL_CODE_ROLE_RE = re.compile(
    r':externa?l:c:(struct|func|var|enum|macro|type|member):`([^`]+)`'
)
EXTERNAL_FILE_ROLE_RE = re.compile(r':externa?l:file:`([^`]+)`')
LOCAL_CODE_ROLE_RE = re.compile(
    r':local:c:(struct|func|var|enum|macro|type|member):`([^`]+)`'
)
LOCAL_FILE_ROLE_RE = re.compile(r':local:file:`([^`]+)`')

LOCAL_SOURCE_NAMES = frozenset({'local', 'ncs_matter'})

_SUBSTITUTION_RE = re.compile(r'^\.\. \|([^|]+)\| replace:: (.+)$', re.MULTILINE)


@dataclass(frozen=True)
class SymbolEntry:
    source: str
    url: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class SourceConfig:
    name: str
    base_url: str | None
    workspace_prefixes: tuple[str, ...] = ()


@dataclass
class ExternalCodeRegistry:
    sources: dict[str, str | None] = field(default_factory=dict)
    source_configs: dict[str, SourceConfig] = field(default_factory=dict)
    prefix_map: list[tuple[str, str]] = field(default_factory=list)
    symbols: dict[tuple[str, str], SymbolEntry] = field(default_factory=dict)
    files: dict[str, SymbolEntry] = field(default_factory=dict)

    def is_registered(self, kind: str, name: str) -> bool:
        if (kind, name) in self.symbols:
            return True
        repo_path, _display = parse_local_ref(name)
        return repo_path and map_external_repo_path(repo_path, self.prefix_map) is not None

    def is_file_registered(self, path: str) -> bool:
        if path in self.files:
            return True
        return map_external_repo_path(path, self.prefix_map) is not None

    def resolve_url(
        self,
        kind: str,
        name: str,
        substitutions: dict[str, str] | None = None,
    ) -> str | None:
        entry = self.symbols.get((kind, name))
        if entry is None:
            return None
        return _resolve_entry_url(entry, self.sources, substitutions, default_path=None)

    def resolve_file_url(
        self,
        path: str,
        substitutions: dict[str, str] | None = None,
    ) -> str | None:
        entry = self.files.get(path)
        if entry is None:
            return None
        return _resolve_entry_url(entry, self.sources, substitutions, default_path=path)

    def resolve_local_repo_url(
        self,
        repo_path: str,
        substitutions: dict[str, str] | None = None,
        *,
        repo_root_path: Path | None = None,
    ) -> str | None:
        source_base = self.sources.get('local') or self.sources.get('ncs_matter')
        if not source_base:
            return None

        base = _apply_substitutions(source_base, substitutions)
        normalized_path = repo_path.strip().lstrip('/')
        if not normalized_path:
            return None

        if repo_root_path is not None:
            candidate = repo_root_path / normalized_path
            if candidate.is_dir():
                tree_base = base.replace('/blob/', '/tree/').rstrip('/')
                return f'{tree_base}/{normalized_path}'

        if not base.endswith('/'):
            base += '/'
        return base + normalized_path

    def resolve_external_repo_url(
        self,
        repo_path: str,
        substitutions: dict[str, str] | None = None,
        *,
        repo_root_path: Path | None = None,
    ) -> str | None:
        mapped = map_external_repo_path(repo_path, self.prefix_map)
        if mapped is None:
            return None

        source_name, relative_path = mapped
        source_base = self.sources.get(source_name)
        if not source_base:
            return None

        base = _apply_substitutions(source_base, substitutions)
        normalized_path = relative_path.strip().lstrip('/')
        tree_base = base.replace('/blob/', '/tree/').rstrip('/')

        if not normalized_path:
            return tree_base

        is_directory_ref = repo_path.rstrip().endswith('/')
        if repo_root_path is not None and not is_directory_ref:
            candidate = repo_root_path / repo_path.strip().lstrip('/')
            if candidate.is_dir():
                is_directory_ref = True

        if is_directory_ref:
            return f'{tree_base}/{normalized_path.rstrip("/")}'

        if not base.endswith('/'):
            base += '/'
        return base + normalized_path


def _normalize_workspace_prefix(prefix: str) -> str:
    return prefix.strip().strip('/')


def build_prefix_map(source_configs: dict[str, SourceConfig]) -> list[tuple[str, str]]:
    """Return workspace prefixes sorted longest-first for deterministic matching."""
    entries: list[tuple[str, str]] = []
    for source_name, source_cfg in source_configs.items():
        for prefix in source_cfg.workspace_prefixes:
            normalized_prefix = _normalize_workspace_prefix(prefix)
            if normalized_prefix:
                entries.append((normalized_prefix, source_name))
    entries.sort(key=lambda item: len(item[0]), reverse=True)
    return entries


def map_external_repo_path(
    path: str,
    prefix_map: list[tuple[str, str]],
) -> tuple[str, str] | None:
    normalized = path.strip().lstrip('/').split('#', 1)[0].strip('/')
    if not normalized:
        return None

    for prefix, source_name in prefix_map:
        if normalized == prefix or normalized.startswith(f'{prefix}/'):
            relative = normalized[len(prefix) :].lstrip('/')
            return source_name, relative
    return None


def _apply_substitutions(text: str, substitutions: dict[str, str] | None) -> str:
    if not substitutions:
        return text
    for key, value in substitutions.items():
        text = text.replace(f'{{{key}}}', value)
    return text


def _resolve_entry_url(
    entry: SymbolEntry,
    sources: dict[str, str | None],
    substitutions: dict[str, str] | None,
    *,
    default_path: str | None,
) -> str | None:
    if entry.url:
        return _apply_substitutions(entry.url, substitutions)

    source_base = sources.get(entry.source)
    if source_base is None or not source_base:
        return None

    resolved_path = entry.path if entry.path is not None else default_path
    if not resolved_path:
        return None

    base = _apply_substitutions(source_base, substitutions)
    if not base.endswith('/'):
        base += '/'
    return base + resolved_path.lstrip('/')


def _normalize_substitution_key(name: str) -> str:
    return name.replace('-', '_')


def parse_local_ref(text: str) -> tuple[str, str]:
    """Split ``repo/path#DisplayName`` into repository path and link label."""
    value = text.strip()
    if not value:
        return '', ''

    if '#' in value:
        repo_path, display_name = value.split('#', 1)
        repo_path = repo_path.strip()
        display_name = display_name.strip()
        if repo_path and display_name:
            return repo_path, display_name

    repo_path = value
    display_name = PurePosixPath(repo_path.replace('\\', '/')).name
    return repo_path, display_name


def local_ref_display_name(text: str) -> str:
    return parse_local_ref(text)[1]


def local_ref_repo_path(text: str) -> str:
    return parse_local_ref(text)[0]


def _git_output(repo_root: Path, *args: str) -> str | None:
    proc = subprocess.run(
        ['git', '-C', str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _git_short_revision(repo_root: Path, ref: str = 'HEAD') -> str | None:
    return _git_output(repo_root, 'rev-parse', '--short', ref)


def resolve_ncs_matter_revision(
    repo_root: Path | None,
    *,
    addon_version: str = 'latest',
) -> str:
    """Return a GitHub ref for ncs-matter source links from the current checkout."""
    if repo_root is not None and repo_root.is_dir():
        if os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
            sha = os.environ.get('GITHUB_SHA', '').strip()
            short_sha = _git_short_revision(repo_root, sha) if sha else _git_short_revision(repo_root)
            if short_sha:
                return short_sha

        exact_tag = _git_output(repo_root, 'describe', '--exact-match', '--tags', 'HEAD')
        if exact_tag:
            return exact_tag

        branch = _git_output(repo_root, 'rev-parse', '--abbrev-ref', 'HEAD')
        if branch and branch != 'HEAD' and branch == 'main':
            return 'main'

        short_sha = _git_short_revision(repo_root)
        if short_sha:
            return short_sha

    version = addon_version.removeprefix('v')
    return f'v{version}'


def load_documentation_substitutions(
    shortcuts_path: Path,
    *,
    repo_root_path: Path | None = None,
    west_manifest_path: Path | None = None,
    matter_module_path: Path | None = None,
) -> dict[str, str]:
    substitutions: dict[str, str] = {
        'ncs_version': 'latest',
        'addon_version': 'latest',
        'ncs_matter_revision': 'main',
        'sdk_connectedhomeip_revision': 'latest',
    }

    if shortcuts_path.is_file():
        for match in _SUBSTITUTION_RE.finditer(shortcuts_path.read_text(encoding='utf-8')):
            substitutions[_normalize_substitution_key(match.group(1))] = match.group(2).strip()

    if repo_root_path is None and west_manifest_path is not None:
        repo_root_path = west_manifest_path.parent

    substitutions['ncs_matter_revision'] = resolve_ncs_matter_revision(
        repo_root_path,
        addon_version=substitutions.get('addon_version', 'latest'),
    )

    if west_manifest_path is not None:
        try:
            from west_substitutions import load_west_substitutions

            west_substitutions = load_west_substitutions(
                west_manifest_path,
                matter_module=matter_module_path,
            )
            for key, value in west_substitutions.items():
                substitutions[_normalize_substitution_key(key)] = value
        except (FileNotFoundError, OSError, ValueError):
            pass

    return substitutions


def load_ncs_version_substitutions(shortcuts_path: Path) -> dict[str, str]:
    """Backward-compatible alias for callers that only need shortcuts-based values."""
    return load_documentation_substitutions(shortcuts_path)


def load_external_code_registry(
    path: Path,
    *,
    substitutions: dict[str, str] | None = None,
) -> ExternalCodeRegistry:
    if not path.is_file():
        raise FileNotFoundError(f'Missing external code sources registry: {path}')

    raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError(f'{path}: registry root must be a mapping')

    registry = ExternalCodeRegistry()
    sources = raw.get('sources', {})
    if not isinstance(sources, dict):
        raise ValueError(f'{path}: "sources" must be a mapping')

    for source_name, source_cfg in sources.items():
        if source_cfg is None:
            registry.sources[source_name] = None
            registry.source_configs[source_name] = SourceConfig(
                name=str(source_name),
                base_url=None,
            )
            continue
        if not isinstance(source_cfg, dict):
            raise ValueError(f'{path}: source "{source_name}" must be a mapping')
        base_url = source_cfg.get('base_url')
        workspace_prefixes_raw = source_cfg.get('workspace_prefixes', [])
        if workspace_prefixes_raw is None:
            workspace_prefixes_raw = []
        if not isinstance(workspace_prefixes_raw, list):
            raise ValueError(f'{path}: source "{source_name}".workspace_prefixes must be a list')
        workspace_prefixes = tuple(
            _normalize_workspace_prefix(str(prefix))
            for prefix in workspace_prefixes_raw
            if _normalize_workspace_prefix(str(prefix))
        )
        resolved_base_url = (
            None if base_url is None else _apply_substitutions(str(base_url), substitutions)
        )
        registry.sources[source_name] = resolved_base_url
        registry.source_configs[source_name] = SourceConfig(
            name=str(source_name),
            base_url=resolved_base_url,
            workspace_prefixes=workspace_prefixes,
        )

    registry.prefix_map = build_prefix_map(registry.source_configs)

    symbols = raw.get('symbols', {})
    if not isinstance(symbols, dict):
        raise ValueError(f'{path}: "symbols" must be a mapping')

    for kind, kind_symbols in symbols.items():
        if kind not in SUPPORTED_KINDS:
            raise ValueError(f'{path}: unsupported symbol kind "{kind}"')
        if not isinstance(kind_symbols, dict):
            raise ValueError(f'{path}: symbols.{kind} must be a mapping')
        for name, symbol_cfg in kind_symbols.items():
            if not isinstance(symbol_cfg, dict):
                raise ValueError(f'{path}: symbols.{kind}.{name} must be a mapping')
            source = symbol_cfg.get('source')
            if not source:
                raise ValueError(f'{path}: symbols.{kind}.{name} missing "source"')
            if source not in registry.sources:
                raise ValueError(
                    f'{path}: symbols.{kind}.{name} references unknown source "{source}"'
                )
            entry = SymbolEntry(
                source=str(source),
                url=symbol_cfg.get('url'),
                path=symbol_cfg.get('path'),
            )
            registry.symbols[(kind, name)] = entry

    files = raw.get('files', {})
    if not isinstance(files, dict):
        raise ValueError(f'{path}: "files" must be a mapping')

    for name, file_cfg in files.items():
        if not isinstance(file_cfg, dict):
            raise ValueError(f'{path}: files.{name} must be a mapping')
        source = file_cfg.get('source')
        if not source:
            raise ValueError(f'{path}: files.{name} missing "source"')
        if source not in registry.sources:
            raise ValueError(f'{path}: files.{name} references unknown source "{source}"')
        registry.files[str(name)] = SymbolEntry(
            source=str(source),
            url=file_cfg.get('url'),
            path=file_cfg.get('path'),
        )

    return registry


def iter_external_code_role_usages(rst_path: Path) -> list[tuple[int, str, str]]:
    usages: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(rst_path.read_text(encoding='utf-8').splitlines(), start=1):
        for match in EXTERNAL_CODE_ROLE_RE.finditer(line):
            usages.append((line_no, match.group(1), match.group(2)))
    return usages


def iter_local_code_role_usages(rst_path: Path) -> list[tuple[int, str, str]]:
    usages: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(rst_path.read_text(encoding='utf-8').splitlines(), start=1):
        for match in LOCAL_CODE_ROLE_RE.finditer(line):
            usages.append((line_no, match.group(1), match.group(2)))
    return usages


def iter_local_file_role_usages(rst_path: Path) -> list[tuple[int, str]]:
    usages: list[tuple[int, str]] = []
    for line_no, line in enumerate(rst_path.read_text(encoding='utf-8').splitlines(), start=1):
        for match in LOCAL_FILE_ROLE_RE.finditer(line):
            usages.append((line_no, match.group(1)))
    return usages


def iter_external_file_role_usages(rst_path: Path) -> list[tuple[int, str]]:
    usages: list[tuple[int, str]] = []
    for line_no, line in enumerate(rst_path.read_text(encoding='utf-8').splitlines(), start=1):
        for match in EXTERNAL_FILE_ROLE_RE.finditer(line):
            usages.append((line_no, match.group(1)))
    return usages


def validate_external_code_references(
    docs_dir: Path,
    registry: ExternalCodeRegistry,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    for rst_path in sorted(docs_dir.rglob('*.rst')):
        rel_source = str(rst_path.relative_to(docs_dir))
        for line_no, kind, name in iter_external_code_role_usages(rst_path):
            if not registry.is_registered(kind, name):
                issues.append(
                    {
                        'source': rel_source,
                        'line': line_no,
                        'kind': kind,
                        'name': name,
                        'message': (
                            f'external c:{kind} reference target not found in '
                            f'external_code_sources: {name}'
                        ),
                    }
                )
                continue

            entry = registry.symbols.get((kind, name))
            if entry is not None and entry.source not in registry.sources:
                issues.append(
                    {
                        'source': rel_source,
                        'line': line_no,
                        'kind': kind,
                        'name': name,
                        'message': (
                            f'external c:{kind} "{name}" references unknown source '
                            f'"{entry.source}"'
                        ),
                    }
                )

    return issues


def validate_external_file_references(
    docs_dir: Path,
    registry: ExternalCodeRegistry,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    for rst_path in sorted(docs_dir.rglob('*.rst')):
        rel_source = str(rst_path.relative_to(docs_dir))
        for line_no, path in iter_external_file_role_usages(rst_path):
            if not registry.is_file_registered(path):
                issues.append(
                    {
                        'source': rel_source,
                        'line': line_no,
                        'name': path,
                        'message': (
                            f'external file reference target not found in '
                            f'external_code_sources: {path}'
                        ),
                    }
                )
                continue

            entry = registry.files.get(path)
            if entry is not None and entry.source not in registry.sources:
                issues.append(
                    {
                        'source': rel_source,
                        'line': line_no,
                        'name': path,
                        'message': (
                            f'external file "{path}" references unknown source '
                            f'"{entry.source}"'
                        ),
                    }
                )

    return issues


def validate_local_references(
    docs_dir: Path,
    *,
    repo_root_path: Path | None = None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    for rst_path in sorted(docs_dir.rglob('*.rst')):
        rel_source = str(rst_path.relative_to(docs_dir))
        for line_no, raw_text in iter_local_file_role_usages(rst_path):
            repo_path, _display = parse_local_ref(raw_text)
            issues.extend(
                _validate_local_repo_path(
                    rel_source,
                    line_no,
                    repo_path,
                    repo_root_path=repo_root_path,
                )
            )

        for line_no, _kind, raw_text in iter_local_code_role_usages(rst_path):
            repo_path, _display = parse_local_ref(raw_text)
            issues.extend(
                _validate_local_repo_path(
                    rel_source,
                    line_no,
                    repo_path,
                    repo_root_path=repo_root_path,
                )
            )

    return issues


def _validate_local_repo_path(
    rel_source: str,
    line_no: int,
    repo_path: str,
    *,
    repo_root_path: Path | None,
) -> list[dict[str, Any]]:
    if not repo_path:
        return [
            {
                'source': rel_source,
                'line': line_no,
                'name': repo_path,
                'message': 'local reference is missing a repository path',
            }
        ]

    if repo_root_path is None:
        return []

    candidate = repo_root_path / repo_path
    if candidate.exists():
        return []

    return [
        {
            'source': rel_source,
            'line': line_no,
            'name': repo_path,
            'message': f'local reference path not found in repository: {repo_path}',
        }
    ]


@dataclass(frozen=True)
class LinkRedirectAllowlistEntry:
    url: str
    redirect_pattern: str
    reason: str = ''


def load_link_redirect_allowlist(path: Path) -> list[LinkRedirectAllowlistEntry]:
    """Load external URL redirect allowlist entries from external_code_sources.yaml."""
    if not path.is_file():
        return []

    raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        return []

    entries_raw = raw.get('link_redirect_allowlist', [])
    if not isinstance(entries_raw, list):
        raise ValueError(f'{path}: "link_redirect_allowlist" must be a list')

    entries: list[LinkRedirectAllowlistEntry] = []
    for index, entry in enumerate(entries_raw):
        if not isinstance(entry, dict):
            raise ValueError(f'{path}: link_redirect_allowlist[{index}] must be a mapping')
        url = entry.get('url')
        redirect = entry.get('redirect')
        if not url or not redirect:
            raise ValueError(
                f'{path}: link_redirect_allowlist[{index}] requires "url" and "redirect"'
            )
        entries.append(
            LinkRedirectAllowlistEntry(
                url=str(url),
                redirect_pattern=str(redirect),
                reason=str(entry.get('reason', '')),
            )
        )
    return entries


def link_redirect_allowlist_for_sphinx(path: Path) -> dict[str, str]:
    """Return Sphinx linkcheck_allowed_redirects entries keyed by escaped source URLs."""
    return {
        re.escape(entry.url): entry.redirect_pattern
        for entry in load_link_redirect_allowlist(path)
    }


def is_allowlisted_redirect_warning(
    message: str,
    allowlist: list[LinkRedirectAllowlistEntry],
) -> bool:
    if not message.startswith('redirect'):
        return False
    return any(entry.url in message for entry in allowlist)
