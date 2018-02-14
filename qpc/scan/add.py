#!/usr/bin/env python
#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanAddCommand is used to create a host scan."""

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
class ScanAddCommand(CliCommand):
    """Defines the add command.

    This command is for creating host scans with a source to gather system
    facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.ADD

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            scan.SCAN_URI, [codes.created])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.SCAN_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--sources', dest='sources', nargs='+',
                                 metavar='SOURCES', default=[],
                                 help=_(messages.SOURCES_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--max-concurrency', dest='max_concurrency',
                                 metavar='MAX_CONCURRENCY',
                                 type=int, default=50,
                                 help=_(messages.SCAN_MAX_CONCURRENCY_HELP))
        self.parser.add_argument('--disable-optional-products',
                                 dest='disable_optional_products',
                                 nargs='+',
                                 choices=scan.OPTIONAL_PRODUCTS,
                                 metavar='DISABLE_OPTIONAL_PRODUCTS',
                                 help=_(messages.DISABLE_OPT_PRODUCTS_HELP),
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
                count = json_data.get('count', 0)
                results = json_data.get('results', [])
                if count == 1:
                    source_entry = results[0]
                    source_ids.append(source_entry['id'])
                else:
                    print(_(messages.SOURCE_DOES_NOT_EXIST % source_name))
                    not_found = True
            else:
                print(_(messages.SOURCE_DOES_NOT_EXIST % source_name))
                not_found = True
        return not_found, source_ids

    def _get_optional_products(self):
        """Construct a dictionary based on the disable-optional-products args.

        :returns: a dictionary representing the collection status of optional
        products
        """
        optional_product_status = {}

        if self.args.disable_optional_products:
            for product in self.args.disable_optional_products:
                optional_product_status[product] = False
        else:
            return None

        return optional_product_status

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
                'max_concurrency': self.args.max_concurrency}
        }
        disable_optional_products = self._get_optional_products()
        if disable_optional_products is not None:
            self.req_payload['options']['disable_optional_products']\
                = disable_optional_products

    def _handle_response_success(self):
        json_data = self.response.json()
        # Change id to name whenever name is added to scan model
        print(_(messages.SCAN_ADDED % json_data['id']))
