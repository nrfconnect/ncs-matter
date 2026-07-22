# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import re
import sys
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Matter add-on for nRF Connect SDK'
copyright = '2026, Nordic Semiconductor'
author = 'Nordic Semiconductor'
release = '1.0.0'

# Paths

NCS_MATTER_BASE = Path(__file__).resolve().parents[1]
DOC_BASE = Path(__file__).resolve().parent
NCS_ROOT = NCS_MATTER_BASE.parent
MATTER_MODULE = NCS_ROOT / 'modules' / 'lib' / 'matter'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.insert(0, str(DOC_BASE / '_extensions'))

extensions = [
    'table_from_rows',
    'breathe',
    'sphinxcontrib.mscgen',
    'sphinx_tabs.tabs',
    'sphinx_togglebutton',
    'sphinx_copybutton',
    'page_filter',
    'ncs_matter_kconfig',
    'memory_table',
    'memory_viz',
    'memory_layout_viz',
    'options_from_kconfig',
]

root_doc = 'index'

templates_path = ['_templates']
exclude_patterns = ['_build_sphinx', '_build_doxygen', 'venv', '.venv', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_ncs_theme'

html_theme_options = {
    'docsets': {},
}

# Copied into the HTML output for the hosted documentation version switcher.
html_extra_path = ['versions.json']

## -- Options for Breathe ----------------------------------------------------
# https://breathe.readthedocs.io/en/latest/index.html
#
# WARNING: please, check breathe maintainership status before using this
# extension in production!

breathe_projects = {'ncs-matter': '_build_doxygen/xml'}
breathe_default_project = 'ncs-matter'
breathe_default_members = ('members', )

# Include following files at the end of each .rst file.
# Substitutions such as |ncs_version| are not expanded in external link URIs by
# Sphinx, so apply them when loading links.txt.
def _read_rst_substitutions(path: Path) -> dict[str, str]:
    substitutions: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.match(r'\.\. \|([^|]+)\| replace:: (.*)', line)
        if match:
            substitutions[match.group(1)] = match.group(2)
    return substitutions


def _apply_substitutions(text: str, substitutions: dict[str, str]) -> str:
    for name, value in substitutions.items():
        text = text.replace(f'|{name}|', value)
    return text


_shortcuts_path = DOC_BASE / 'shortcuts.txt'
_substitutions = _read_rst_substitutions(_shortcuts_path)
_links = _apply_substitutions(
    (DOC_BASE / 'links.txt').read_text(encoding='utf-8'),
    _substitutions,
)

rst_epilog = f"""{_links}
.. include:: /shortcuts.txt
"""

# -- Options for table_from_rows (local add-on copy) -------------------------

table_from_rows_base_dir = NCS_MATTER_BASE
table_from_sample_yaml_board_reference = '/includes/sample_board_rows.txt'

# -- Options for ncs_matter_kconfig ----------------------------------------

ncs_matter_kconfig_base_dir = str(NCS_MATTER_BASE)
ncs_matter_kconfig_extra_dirs = [str(MATTER_MODULE)]

# -- Options for options_from_kconfig (local add-on copy) --------------------

options_from_kconfig_base_dir = str(NCS_MATTER_BASE)

suppress_warnings = [
    'ref.option',
    'ref.ref',
    'ref.doc',
]


def setup(app):
    import logging

    class _FilterDuplicateTargets(logging.Filter):
        def filter(self, record):
            msg = record.getMessage()
            return (
                'Duplicate explicit target name' not in msg
                and 'Duplicate target name' not in msg
            )

    logging.getLogger('sphinx').addFilter(_FilterDuplicateTargets())
