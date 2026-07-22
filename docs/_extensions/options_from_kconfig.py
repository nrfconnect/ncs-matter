# Copyright (c) 2020 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: Apache-2.0

"""Expand Kconfig files into std domain option entries for Sphinx."""

from __future__ import annotations

import os
from pathlib import Path

import kconfiglib
from docutils import statemachine
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

__version__ = '0.0.1'


def _monkey_patch_kconfiglib() -> None:
    """Parse only symbols from the requested Kconfig tree."""
    kconfiglib._SOURCE_TOKENS = kconfiglib._REL_SOURCE_TOKENS
    kconfiglib.Kconfig._parse_error = lambda self_, msg: None


class OptionsFromKconfig(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        'prefix': directives.unchanged,
        'suffix': directives.unchanged,
        'show-type': directives.flag,
        'only-visible': directives.flag,
    }

    def _resolve_kconfig_path(self) -> str:
        if self.arguments:
            _, path = self.env.relfn2path(self.arguments[0])
            return path

        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1
        )
        source_dir = os.path.dirname(os.path.abspath(source))
        rel_path = os.path.relpath(source_dir, self.env.srcdir)
        return os.path.join(
            self.config.options_from_kconfig_base_dir,
            rel_path,
            'Kconfig',
        )

    def run(self):
        base_dir = Path(self.config.options_from_kconfig_base_dir)
        path = self._resolve_kconfig_path()

        _monkey_patch_kconfiglib()
        os.environ['SRCTREE'] = str(base_dir)

        kconfig = kconfiglib.Kconfig(filename=path, warn=False)

        prefix = self.options.get('prefix')
        suffix = self.options.get('suffix')

        lines: list[str] = []
        for sym in kconfig.unique_defined_syms:
            if 'only-visible' in self.options:
                visible = kconfiglib.TRI_TO_STR[sym.visibility]
                if visible == 'n':
                    continue

            lines.append(f'.. option:: CONFIG_{sym.name}\n')

            text = ''
            if 'show-type' in self.options:
                typ_ = kconfiglib.TYPE_TO_STR[sym.type]
                text += '``(' + typ_ + ')`` '

            if prefix is not None:
                if (prefix.startswith('"') and prefix.endswith('"')) or \
                   (prefix.startswith("'") and prefix.endswith("'")):
                    prefix = prefix[1:-1]
                text += prefix

            try:
                prompt_ = f'{sym.nodes[0].prompt[0]}'
            except Exception:
                prompt_ = ''

            if prefix is not None and prompt_:
                text += prompt_[:1].lower() + prompt_[1:]
            else:
                text += prompt_

            if suffix is not None:
                if (suffix.startswith('"') and suffix.endswith('"')) or \
                   (suffix.startswith("'") and suffix.endswith("'")):
                    suffix = suffix[1:-1]
                text += suffix

            if text:
                lines.append(f'{text}\n')

            try:
                help_ = sym.nodes[0].help
                if help_ is not None:
                    lines.append(f'{help_}\n')
            except Exception:
                pass

        self.state_machine.insert_input(
            statemachine.string2lines('\n'.join(lines)),
            path,
        )
        return []


def setup(app: Sphinx):
    app.add_config_value('options_from_kconfig_base_dir', None, 'env')
    directives.register_directive('options-from-kconfig', OptionsFromKconfig)

    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
