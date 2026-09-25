# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
# Sphinx configuration overlay used by the documentation links check
# (scripts/matter_sample_checker/checks/docs/check_doc_links.py).
# This file must be named conf.py because Sphinx requires that name in -c DIR.
# Imports the production conf.py, then enables strict cross-reference checking
# and optional intersphinx mappings to locally built NCS docset inventories.

from __future__ import annotations

import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOCS_DIR))
sys.path.insert(0, str(DOCS_DIR / "_extensions"))

from conf import *  # noqa: F401,F403

from external_code_registry import link_redirect_allowlist_for_sphinx

extensions = list(extensions)
if "sphinx.ext.intersphinx" not in extensions:
    extensions.append("sphinx.ext.intersphinx")

# Paths in conf.py are relative to docs/, but Sphinx resolves some settings against
# the -c directory (docs/checks/). Re-root those entries for link-check builds.
html_extra_path = [str(DOCS_DIR / "versions.json")]
templates_path = [str(DOCS_DIR / "_templates")]
breathe_projects = {"ncs-matter": str(DOCS_DIR / "_build_doxygen" / "xml")}

# Do not suppress missing :ref:, :doc:, or :option: warnings during link checks.
suppress_warnings = []

NCS_ROOT = DOCS_DIR.parent.parent
intersphinx_mapping: dict[str, tuple[str, str]] = {}

_DOCSET_INVENTORIES = (
    ("nrf", "nrf/doc/_build/html/nrf/objects.inv"),
    ("zephyr", "nrf/doc/_build/html/zephyr/objects.inv"),
    ("kconfig", "nrf/doc/_build/html/kconfig/objects.inv"),
    ("nrfxlib", "nrf/doc/_build/html/nrfxlib/objects.inv"),
    ("mcuboot", "nrf/doc/_build/html/mcuboot/objects.inv"),
    ("tfm", "nrf/doc/_build/html/tfm/objects.inv"),
    ("matter", "nrf/doc/_build/html/matter/objects.inv"),
)

for docset, rel_path in _DOCSET_INVENTORIES:
    inventory = NCS_ROOT / rel_path
    if inventory.is_file():
        intersphinx_mapping[docset] = (f"../{docset}", str(inventory))

# Align with sdk-nrf linkcheck defaults where practical.
linkcheck_ignore = [
    # External URLs are discovered by scanning RST sources in check_doc_links.py
    # and verified there with a browser-like HTTP client (not by Sphinx).
    r"^https?://",
    # Relative links resolved by intersphinx or Doxygen.
    r"\.\.(\\|/)",
    # Redirecting and used in release notes.
    r"https://github\.com/nrfconnect/nrfxlib",
    # Local preview URL used in examples.
    "http://localhost:8000/latest/index.html",
    # SES download links.
    r"https://(www\.)?segger\.com/downloads/embedded-studio/embeddedstudio_arm_nordic_.+(_x\d+)?",
    # Requires login.
    "https://portal.azure.com/",
    "https://threadgroup.atlassian.net/wiki/spaces/",
    # Used as example in Doxygen.
    "https://google.com:443",
    # WAF often blocks CI runners on these hosts. URLs are still HTTP-checked;
    # confirmed 404/410 responses fail the build, but HTTP 403 is one aggregated
    # warning (not one line per link).
    r"https://academy\.nordicsemi\.com/",
    r"https://devzone\.nordicsemi\.com/",
    r"https://docs\.nordicsemi\.com/",
    r"https://nrfconnectdocs\.nordicsemi\.com/",
]

# Keep Sphinx default ^! for Kconfig hashbang anchors (#!CONFIG_*), plus page=.
linkcheck_anchors_ignore = [r"^!", r"page="]

# docs.nordicsemi.com redirects to nrfconnectdocs.nordicsemi.com and many section
# anchors are rendered client-side, so verify the page responds but not anchors.
# Member-login redirects are listed in docs/external_code_sources.yaml.
linkcheck_allowed_redirects = {
    r"https://docs\.nordicsemi\.com/.*": r"https://nrfconnectdocs\.nordicsemi\.com/.*",
    **link_redirect_allowlist_for_sphinx(DOCS_DIR / "external_code_sources.yaml"),
}
linkcheck_anchors_ignore_for_url = (
    r"https://docs\.nordicsemi\.com/.*",
    r"https://nrfconnectdocs\.nordicsemi\.com/.*",
)

linkcheck_timeout = 30
linkcheck_retries = 2
linkcheck_workers = 5
