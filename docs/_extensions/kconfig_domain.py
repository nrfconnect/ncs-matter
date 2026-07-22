# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

"""Minimal Kconfig Sphinx domain for add-on documentation builds."""

from collections.abc import Iterable
from typing import Optional

from docutils import nodes
from sphinx.addnodes import pending_xref
from sphinx.builders import Builder
from sphinx.domains import Domain, ObjType
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode


class KconfigDomain(Domain):
    """Kconfig domain used with Intersphinx for NCS options."""

    name = 'kconfig'
    label = 'Kconfig'
    object_types = {'option': ObjType('option', 'option')}
    roles = {'option': XRefRole()}
    initial_data = {'options': set()}

    def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
        yield from self.data['options']

    def merge_domaindata(self, docnames: list[str], otherdata: dict) -> None:
        self.data['options'].update(otherdata['options'])

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: nodes.Element,
    ) -> Optional[nodes.Element]:
        match = [
            (docname, anchor)
            for name, _, _, docname, anchor, _ in self.get_objects()
            if name == target
        ]

        if match:
            todocname, anchor = match[0]
            return make_refnode(builder, fromdocname, todocname, anchor, contnode, anchor)

        return None

    def add_option(self, option: str, docname: str = 'index') -> None:
        self.data['options'].add((option, option, 'option', docname, option, 1))
