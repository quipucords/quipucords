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
""" AuthShowCommand is used to show info on a specific credential
for system access
"""

from __future__ import print_function
import sys
from requests import codes
from cli.utils import pretty_print
from cli.clicommand import CliCommand
import cli.auth as auth
from cli.request import GET


# pylint: disable=too-few-public-methods
class AuthShowCommand(CliCommand):
    """
    This command is for showing an auth which can be later associated with
    profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.SHOW

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            auth.AUTH_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help='auth credential name', required=True)

    def _build_req_params(self):
        self.req_params = {'name': self.args.name}

    def _handle_response_success(self):
        json_data = self.response.json()
        if len(json_data) == 1:
            cred_entry = json_data[0]
            data = pretty_print(cred_entry)
            print(data)
        else:
            print('Auth "%s" does not exist' % self.args.name)
            sys.exit(1)
