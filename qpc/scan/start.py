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
"""ScanStartCommand is used to trigger a host scan."""

from __future__ import print_function
import sys
from requests import codes
from qpc.request import POST, GET, request
from qpc.clicommand import CliCommand
import qpc.source as source
import qpc.scan as scan
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class ScanStartCommand(CliCommand):
    """Defines the start command.

    This command is for triggering host scans with a source to gather system
    facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.START

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            scan.SCAN_URI, [codes.created])
        self.parser.add_argument('--sources', dest='sources', nargs='+',
                                 metavar='SOURCES', default=[],
                                 help=_(messages.SOURCES_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--max-concurrency', dest='max_concurrency',
                                 metavar='MAX_CONCURRENCY',
                                 type=int, default=50,
                                 help=_(messages.SCAN_MAX_CONCURRENCY_HELP))
        self.parser.add_argument('--optional-products', dest='optional_products',
                                 choices=[scan.SCAN_JBOSS_EAP,
                                          scan.SCAN_JBOSS_FUSE,
                                          scan.SCAN_JBOSS_BRMS],
                                 metavar='OPTIONAL_PRODUCTS',
                                 help=_(messages.SCAN_OPTIONAL_PRODUCTS_HELP),
                                 required=False)
        self.source_ids = []

    def _get_source_ids(self, source_names):
        not_found = False
        source_ids = []
        for source_name in set(source_names):
            # check for existence of source
            response = request(parser=self.parser, method=GET,
                               path=source.SOURCE_URI,
                               params={'name': source_name},
                               payload=None)
            if response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = response.json()
                if len(json_data) == 1:
                    source_entry = json_data[0]
                    source_ids.append(source_entry['id'])
                else:
                    print(_(messages.SOURCE_DOES_NOT_EXIST % source_name))
                    not_found = True
            else:
                print(_(messages.SOURCE_DOES_NOT_EXIST % source_name))
                not_found = True
        return not_found, source_ids

    def _validate_args(self):
        CliCommand._validate_args(self)
        source_ids = []
        if self.args.sources:
            # check for existence of sources
            not_found, source_ids = self._get_source_ids(self.args.sources)
            if not_found is True:
                sys.exit(1)
        self.source_ids = source_ids

    def _build_data(self):
        """Construct the dictionary credential given our arguments.

        :returns: a dictionary representing the credential being added
        """
        self.req_payload = {
            'sources': self.source_ids,
            'scan_type': scan.SCAN_TYPE_INSPECT,
            'options': {
                'max_concurrency': self.args.max_concurrency
            },
            'optional_products': {
                'products' : self.args.optional_products
            }
        }

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.SCAN_STARTED % json_data['id']))
