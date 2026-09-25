# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

"""Sphinx roles for external and local C API / file cross-references."""

from __future__ import annotations

import re
from pathlib import Path

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util.docutils import SphinxRole

from external_code_registry import (
    ExternalCodeRegistry,
    SUPPORTED_KINDS,
    load_documentation_substitutions,
    load_external_code_registry,
    parse_local_ref,
)

__version__ = '0.0.3'

# ``:external:c:struct:`bt_uuid``` is rewritten to ``:external-c-struct:`bt_uuid```
# before parsing so nested ``:c:struct:`` markup is not interpreted.
_REWRITE_EXTERNAL_CODE_ROLE_RE = re.compile(
    r':externa?l:c:(struct|func|var|enum|macro|type|member):`([^`]+)`'
)
_REWRITE_EXTERNAL_FILE_ROLE_RE = re.compile(r':externa?l:file:`([^`]+)`')
_REWRITE_LOCAL_CODE_ROLE_RE = re.compile(
    r':local:c:(struct|func|var|enum|macro|type|member):`([^`]+)`'
)
_REWRITE_LOCAL_FILE_ROLE_RE = re.compile(r':local:file:`([^`]+)`')


class ExternalCodeRefRole(SphinxRole):
    kind: str

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        symbol = self.text.strip()
        registry: ExternalCodeRegistry = self.env.external_code_registry
        substitutions: dict[str, str] = self.env.external_code_substitutions
        display = symbol
        url = registry.resolve_url(self.kind, symbol, substitutions)

        if url is None and ('/' in symbol or '#' in symbol):
            repo_path, display = parse_local_ref(symbol)
            url = registry.resolve_external_repo_url(repo_path, substitutions)

        if url:
            ref = nodes.reference(
                self.rawtext,
                display,
                refuri=url,
                internal=False,
            )
            return [ref], []

        if registry.is_registered(self.kind, symbol):
            literal = nodes.literal(self.rawtext, display)
            return [literal], []

        literal = nodes.literal(self.rawtext, display)
        return [literal], []


class ExternalFileRefRole(SphinxRole):
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        path = self.text.strip()
        registry: ExternalCodeRegistry = self.env.external_code_registry
        substitutions: dict[str, str] = self.env.external_code_substitutions
        repo_root_path = getattr(self.env, 'external_code_workspace_root_path', None)
        display = parse_local_ref(path)[1]
        url = registry.resolve_file_url(path, substitutions)

        if url is None:
            url = registry.resolve_external_repo_url(
                path,
                substitutions,
                repo_root_path=repo_root_path,
            )

        if url:
            ref = nodes.reference(
                self.rawtext,
                display,
                refuri=url,
                internal=False,
            )
            return [ref], []

        if registry.is_file_registered(path):
            literal = nodes.literal(self.rawtext, display)
            return [literal], []

        literal = nodes.literal(self.rawtext, display)
        return [literal], []


class LocalCodeRefRole(SphinxRole):
    kind: str

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        return _run_local_ref(self)


class LocalFileRefRole(SphinxRole):
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        return _run_local_ref(self)


def _run_local_ref(role: SphinxRole) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    repo_path, display_name = parse_local_ref(role.text)
    registry: ExternalCodeRegistry = role.env.external_code_registry
    substitutions: dict[str, str] = role.env.external_code_substitutions
    repo_root_path = getattr(role.env, 'external_code_repo_root_path', None)
    url = registry.resolve_local_repo_url(
        repo_path,
        substitutions,
        repo_root_path=repo_root_path,
    )

    if url:
        ref = nodes.reference(
            role.rawtext,
            display_name,
            refuri=url,
            internal=False,
        )
        return [ref], []

    literal = nodes.literal(role.rawtext, display_name or repo_path)
    return [literal], []


def _rewrite_external_roles(_app: Sphinx, _docname: str, source: list[str]) -> None:
    for idx, line in enumerate(source):
        line = _REWRITE_EXTERNAL_CODE_ROLE_RE.sub(
            lambda match: f':external-c-{match.group(1)}:`{match.group(2)}`',
            line,
        )
        line = _REWRITE_EXTERNAL_FILE_ROLE_RE.sub(
            lambda match: f':external-file:`{match.group(1)}`',
            line,
        )
        line = _REWRITE_LOCAL_CODE_ROLE_RE.sub(
            lambda match: f':local-c-{match.group(1)}:`{match.group(2)}`',
            line,
        )
        source[idx] = _REWRITE_LOCAL_FILE_ROLE_RE.sub(
            lambda match: f':local-file:`{match.group(1)}`',
            line,
        )


def _attach_registry(app: Sphinx, env: BuildEnvironment, _docnames) -> None:
    registry_path = Path(app.config.external_code_sources_file)
    shortcuts_path = Path(
        getattr(app.config, 'external_code_shortcuts_file', app.confdir / 'shortcuts.txt')
    )
    west_manifest_path = getattr(app.config, 'west_manifest_path', None)
    matter_module_path = getattr(app.config, 'matter_module_path', None)
    repo_root_path = getattr(app.config, 'repo_root_path', None)
    if repo_root_path is None and west_manifest_path is not None:
        repo_root_path = str(Path(west_manifest_path).parent)
    repo_root = Path(repo_root_path) if repo_root_path else None
    workspace_root = None
    if matter_module_path is not None:
        workspace_root = Path(matter_module_path).parents[2]
    elif west_manifest_path is not None:
        workspace_root = Path(west_manifest_path).parent.parent
    substitutions = load_documentation_substitutions(
        shortcuts_path,
        repo_root_path=repo_root,
        west_manifest_path=Path(west_manifest_path) if west_manifest_path else None,
        matter_module_path=Path(matter_module_path) if matter_module_path else None,
    )
    env.external_code_substitutions = substitutions
    env.external_code_repo_root_path = repo_root
    env.external_code_workspace_root_path = workspace_root
    env.external_code_registry = load_external_code_registry(
        registry_path,
        substitutions=substitutions,
    )


def setup(app: Sphinx) -> dict[str, bool | str]:
    app.add_config_value('external_code_sources_file', 'external_code_sources.yaml', 'env')
    app.add_config_value('external_code_shortcuts_file', 'shortcuts.txt', 'env')
    app.add_config_value('repo_root_path', None, 'env', [str])

    for kind in sorted(SUPPORTED_KINDS):
        external_role = ExternalCodeRefRole()
        external_role.kind = kind
        app.add_role(f'external-c-{kind}', external_role)
        app.add_role(f'externa-c-{kind}', external_role)

        local_role = LocalCodeRefRole()
        local_role.kind = kind
        app.add_role(f'local-c-{kind}', local_role)

    app.add_role('external-file', ExternalFileRefRole())
    app.add_role('externa-file', ExternalFileRefRole())
    app.add_role('local-file', LocalFileRefRole())

    app.connect('source-read', _rewrite_external_roles)
    app.connect('env-before-read-docs', _attach_registry)

    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
