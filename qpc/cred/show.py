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
"""CredShowCommand is used to show a specific credential."""

from __future__ import print_function

import sys

import qpc.cred as credential
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_print

from requests import codes


# pylint: disable=too-few-public-methods
class CredShowCommand(CliCommand):
    """Defines the show command.

    This command is for showing a credential which can
    be associated with sources to gather facts.
    """

    SUBCOMMAND = credential.SUBCOMMAND
    ACTION = credential.SHOW

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            credential.CREDENTIAL_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.CRED_NAME_HELP),
                                 required=True)

    def _build_req_params(self):
        self.req_params = {'name': self.args.name}

    def _handle_response_success(self):
        json_data = self.response.json()
        count = json_data.get('count', 0)
        if count == 1:
            cred_entry = json_data.get('results')[0]
            data = pretty_print(cred_entry)
            print(data)
        else:
            print(_(messages.CRED_DOES_NOT_EXIST % self.args.name))
            sys.exit(1)
