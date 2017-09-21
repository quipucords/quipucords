#!/usr/bin/env python
#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
""" AuthAddCommand is used to add authentication credentials
for system access
"""

from __future__ import print_function
import sys
from cli.clicommand import CliCommand
import cli.auth as auth


# pylint: disable=too-few-public-methods
class AuthAddCommand(CliCommand):
    """
    This command is for creating new auths which can be later associated with
    profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.ADD

    def __init__(self, subparsers):
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION)
        self.parser = subparsers.add_parser(self.ACTION)
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help='auth credential name')

    def _validate_args(self):
        CliCommand._validate_args(self)

        if not self.args.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        print('Auth "%s" was added' % self.args.name)
