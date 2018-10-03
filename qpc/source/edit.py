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
"""SourceEditCommand is used to edit existing sources for system scans."""

from __future__ import print_function

import sys

from qpc import cred, messages, source
from qpc.clicommand import CliCommand
from qpc.request import GET, PATCH, request
from qpc.source.utils import build_source_payload, validate_port
from qpc.translation import _
from qpc.utils import read_in_file

from requests import codes

# pylint: disable=too-few-public-methods


class SourceEditCommand(CliCommand):
    """Defines the edit command.

    This command is for editing existing sources  which can be used
    for system scans to gather facts.
    """

    SUBCOMMAND = source.SUBCOMMAND
    ACTION = source.EDIT

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PATCH,
                            source.SOURCE_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.SOURCE_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--hosts', dest='hosts', nargs='+',
                                 metavar='HOSTS', default=[],
                                 help=_(messages.SOURCE_HOSTS_HELP),
                                 required=False)
        self.parser.add_argument('--exclude-hosts', dest='exclude_hosts',
                                 nargs='+', metavar='EXCLUDE_HOSTS',
                                 help=_(messages.SOURCE_EXCLUDE_HOSTS_HELP),
                                 required=False)
        self.parser.add_argument('--cred', dest='cred', metavar='CRED',
                                 nargs='+', default=[],
                                 help=_(messages.SOURCE_CREDS_HELP),
                                 required=False)
        self.parser.add_argument('--port', dest='port',
                                 metavar='PORT', type=validate_port,
                                 help=_(messages.SOURCE_PORT_HELP))
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

    # pylint: disable=too-many-branches
    def _validate_args(self):
        CliCommand._validate_args(self)

        if not(self.args.hosts or self.args.exclude_hosts or self.args.cred or
               self.args.port or self.args.use_paramiko or
               self.args.ssl_cert_verify or self.args.disable_ssl or
               self.args.ssl_protocol):
            print(_(messages.SOURCE_EDIT_NO_ARGS % (self.args.name)))
            self.parser.print_help()
            sys.exit(1)

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

        # check for existence of source
        response = request(parser=self.parser, method=GET,
                           path=source.SOURCE_URI,
                           params={'name': self.args.name},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            count = json_data.get('count', 0)
            results = json_data.get('results', [])
            if count == 1:
                source_entry = results[0]
                self.req_path = self.req_path + str(source_entry['id']) + '/'
            else:
                print(_(messages.SOURCE_DOES_NOT_EXIST % self.args.name))
                sys.exit(1)
        else:
            print(_(messages.SOURCE_DOES_NOT_EXIST % self.args.name))
            sys.exit(1)

        # check for valid cred values
        if len(self.args.cred) > 0:  # pylint: disable=len-as-condition
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
                    for cred_entry in results:
                        self.args.credentials.append(cred_entry['id'])
                else:
                    for cred_entry in results:
                        cred_name = cred_entry['name']
                        self.args.cred.remove(cred_name)
                    not_found_str = ','.join(self.args.cred)
                    print(_(messages.SOURCE_EDIT_CREDS_NOT_FOUND %
                            (not_found_str, self.args.name)))
                    sys.exit(1)
            else:
                print(_(messages.SOURCE_EDIT_CRED_PROCESS_ERR %
                        self.args.name))
                sys.exit(1)

    def _build_data(self):
        """Construct the dictionary cred given our arguments.

        :returns: a dictionary representing the cred being added
        """
        self.req_payload = build_source_payload(self.args, add_none=False)

    def _handle_response_success(self):
        print(_(messages.SOURCE_UPDATED % self.args.name))
