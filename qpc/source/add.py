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
"""SourceAddCommand is used to add sources for system scans."""

from __future__ import print_function
import sys
from requests import codes
from qpc.request import POST, GET, request
from qpc.clicommand import CliCommand
from qpc.utils import read_in_file
import qpc.source as source
from qpc.source.utils import validate_port, build_source_payload
import qpc.cred as cred
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class SourceAddCommand(CliCommand):
    """Defines the add command.

    This command is for creating new sources which can be later used
    with scans to gather facts.
    """

    SUBCOMMAND = source.SUBCOMMAND
    ACTION = source.ADD

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            source.SOURCE_URI, [codes.created])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.SOURCE_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--type', dest='type',
                                 choices=[source.NETWORK_SOURCE_TYPE,
                                          source.VCENTER_SOURCE_TYPE],
                                 metavar='TYPE',
                                 help=_(messages.SOURCE_TYPE_HELP),
                                 required=True)
        self.parser.add_argument('--hosts', dest='hosts', nargs='+',
                                 metavar='HOSTS', default=[],
                                 help=_(messages.SOURCE_HOSTS_HELP),
                                 required=True)
        self.parser.add_argument('--cred', dest='cred',
                                 metavar='CRED',
                                 nargs='+', default=[],
                                 help=_(messages.SOURCE_CREDS_HELP),
                                 required=True)
        self.parser.add_argument('--port', dest='port',
                                 metavar='PORT', type=validate_port,
                                 help=_(messages.SOURCE_PORT_HELP),
                                 required=False)

    def _validate_args(self):
        CliCommand._validate_args(self)

        if ('hosts' in self.args and self.args.hosts and
                len(self.args.hosts) == 1):
            # check if a file and read in values
            try:
                self.args.hosts = read_in_file(self.args.hosts[0])
            except ValueError:
                pass

        # check for valid cred values
        cred_list = ','.join(self.args.cred)
        response = request(parser=self.parser, method=GET,
                           path=cred.CREDENTIAL_URI,
                           params={'name': cred_list},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            if len(json_data) == len(self.args.cred):
                self.args.credentials = []
                for cred_entry in json_data:
                    self.args.credentials.append(cred_entry['id'])
            else:
                for cred_entry in json_data:
                    cred_name = cred_entry['name']
                    self.args.cred.remove(cred_name)
                not_found_str = ','.join(self.args.cred)
                print(_(messages.SOURCE_ADD_CREDS_NOT_FOUND %
                        (not_found_str, self.args.name)))
                sys.exit(1)
        else:
            print(_(messages.SOURCE_ADD_CRED_PROCESS_ERR % self.args.name))
            sys.exit(1)

    def _build_data(self):
        """Construct the dictionary cred given our arguments.

        :returns: a dictionary representing the source being added
        """
        self.req_payload = build_source_payload(self.args)

    def _handle_response_success(self):
        print(_(messages.SOURCE_ADDED % self.args.name))
