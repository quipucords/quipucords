#!/usr/bin/env python
#
# Copyright (c) 2017-2018 Red Hat, Inc.
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

from qpc import cred, messages, source
from qpc.clicommand import CliCommand
from qpc.request import GET, POST, request
from qpc.source.utils import build_source_payload, validate_port
from qpc.translation import _
from qpc.utils import read_in_file

from requests import codes


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
                                          source.VCENTER_SOURCE_TYPE,
                                          source.SATELLITE_SOURCE_TYPE],
                                 metavar='TYPE',
                                 help=_(messages.SOURCE_TYPE_HELP),
                                 required=True)
        self.parser.add_argument('--hosts', dest='hosts', nargs='+',
                                 metavar='HOSTS', default=[],
                                 help=_(messages.SOURCE_HOSTS_HELP),
                                 required=True)
        self.parser.add_argument('--exclude-hosts', dest='exclude_hosts',
                                 nargs='+', metavar='EXCLUDE_HOSTS',
                                 help=_(messages.SOURCE_EXCLUDE_HOSTS_HELP),
                                 required=False)
        self.parser.add_argument('--cred', dest='cred',
                                 metavar='CRED',
                                 nargs='+', default=[],
                                 help=_(messages.SOURCE_CREDS_HELP),
                                 required=True)
        self.parser.add_argument('--port', dest='port',
                                 metavar='PORT', type=validate_port,
                                 help=_(messages.SOURCE_PORT_HELP),
                                 required=False)
        self.parser.add_argument('--ssl-cert-verify', dest='ssl_cert_verify',
                                 choices=source.BOOLEAN_CHOICES,
                                 help=_(messages.SOURCE_SSL_CERT_HELP),
                                 required=False)
        self.parser.add_argument('--ssl-protocol', dest='ssl_protocol',
                                 choices=source.VALID_SSL_PROTOCOLS,
                                 help=_(messages.SOURCE_SSL_PROTOCOL_HELP),
                                 required=False)
        self.parser.add_argument('--disable-ssl', dest='disable_ssl',
                                 choices=source.BOOLEAN_CHOICES,
                                 help=_(messages.SOURCE_SSL_DISABLE_HELP),
                                 required=False)
        self.parser.add_argument('--use-paramiko', dest='use_paramiko',
                                 choices=source.BOOLEAN_CHOICES,
                                 help=_(messages.SOURCE_PARAMIKO_HELP),
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

        if ('exclude_hosts' in self.args and self.args.exclude_hosts and
                len(self.args.exclude_hosts) == 1):
            # check if a file and read in values
            try:
                self.args.exclude_hosts = \
                    read_in_file(self.args.exclude_hosts[0])
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
            count = json_data.get('count', 0)
            results = json_data.get('results', [])
            if count == len(self.args.cred):
                self.args.credentials = []
                results_by_name_dict = {cred['name']: cred for cred in results}
                for cred_name in self.args.cred:
                    self.args.credentials.append(
                        results_by_name_dict[cred_name]['id'])
            else:
                for cred_entry in results:
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
