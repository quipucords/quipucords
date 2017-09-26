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
""" AuthListCommand is used to list authentication credentials
for system access
"""

from __future__ import print_function
from requests import codes
from cli.utils import pretty_print
from cli.clicommand import CliCommand
import cli.auth as auth
from cli.request import GET


# pylint: disable=too-few-public-methods
class AuthListCommand(CliCommand):
    """
    This command is for listing auths which can be later associated with
    profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.LIST

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            auth.AUTH_URI, [codes.ok])

    def _handle_response_success(self):
        json_data = self.response.json()
        if json_data == []:
            print('No credentials exist yet.')
        else:
            data = pretty_print(json_data)
            print(data)
