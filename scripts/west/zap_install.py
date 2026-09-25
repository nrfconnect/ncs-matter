#!/usr/bin/env python3
# Copyright (c) 2025 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

import argparse
import sys
from pathlib import Path
from textwrap import dedent

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from zap_common import DEFAULT_MATTER_PATH, ZapInstaller, existing_dir_path


def run_zap_install(matter_path: Path = DEFAULT_MATTER_PATH) -> None:
    """
    Ensure ZAP is installed and matches the version recommended by the Matter SDK.
    """
    zap_installer = ZapInstaller(matter_path)
    zap_installer.update_zap_if_needed()


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Install Matter ZCL Advanced Platform (ZAP) GUI if needed.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent('''
        Checks whether ZAP is installed and up to date with the version
        recommended by the Matter SDK, and installs or updates it when needed.'''))
    parser.add_argument('-m', '--matter-path', type=existing_dir_path,
                        default=DEFAULT_MATTER_PATH,
                        help=f'Path to Matter SDK. Default is {DEFAULT_MATTER_PATH}')
    args = parser.parse_args()

    try:
        run_zap_install(args.matter_path)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
else:
    from west.commands import WestCommand

    class ZapInstall(WestCommand):

        def __init__(self):
            super().__init__(
                'zap-install',
                'Install Matter ZCL Advanced Platform (ZAP) GUI',
                dedent('''
                Install Matter ZCL Advanced Platform (ZAP) GUI.

                The ZAP GUI in a node.js tool for configuring the data model
                of a Matter application, which defines clusters, commands,
                attributes and events enabled for the given application.'''))

        def do_add_parser(self, parser_adder):
            parser = parser_adder.add_parser(self.name,
                                             help=self.help,
                                             formatter_class=argparse.RawDescriptionHelpFormatter,
                                             description=self.description)
            parser.add_argument('-m', '--matter-path', type=existing_dir_path,
                                default=DEFAULT_MATTER_PATH, help=f'Path to Matter SDK. Default is set to {DEFAULT_MATTER_PATH}')
            return parser

        def do_run(self, args, unknown_args):
            run_zap_install(args.matter_path)
