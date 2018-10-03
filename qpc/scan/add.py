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
"""ScanAddCommand is used to create a scan."""

from __future__ import print_function

import sys

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.scan.utils import (get_enabled_products,
                            get_optional_products,
                            get_source_ids)
from qpc.translation import _

from requests import codes


# pylint: disable=too-few-public-methods
class ScanAddCommand(CliCommand):
    """Defines the add command.

    This command is for creating scans with a source to gather system facts.
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
        self.parser.add_argument('--disabled-optional-products',
                                 dest='disabled_optional_products',
                                 nargs='+',
                                 choices=scan.OPTIONAL_PRODUCTS,
                                 metavar='DISABLED_PRODUCT_LIST',
                                 help=_(messages.DISABLE_OPT_PRODUCTS_HELP),
                                 required=False)
        self.parser.add_argument('--enabled-ext-product-search',
                                 dest='enabled_ext_product_search',
                                 nargs='+',
                                 choices=scan.OPTIONAL_PRODUCTS,
                                 metavar='EXTENDED_PRODUCT_SEARCH_LIST',
                                 help=_(messages.SCAN_ENABLED_PRODUCT_HELP),
                                 required='--ext-product-search-dirs' in
                                 sys.argv)
        self.parser.add_argument('--ext-product-search-dirs',
                                 dest='ext_product_search_dirs',
                                 nargs='+',
                                 metavar='EXTENDED_PRODUCT_SEARCH_DIRS',
                                 help=_(messages.SCAN_EXT_SEARCH_DIRS_HELP),
                                 required=False)
        self.source_ids = []

    def _validate_args(self):
        CliCommand._validate_args(self)
        source_ids = []
        if self.args.sources:
            # check for existence of sources
            not_found, source_ids = get_source_ids(self.parser,
                                                   self.args.sources)
            if not_found is True:
                sys.exit(1)
        self.source_ids = source_ids

    def _build_data(self):
        """Construct the payload for a scan given our arguments.

        :returns: a dictionary representing the scan being added
        """
        self.req_payload = {
            'name': self.args.name,
            'sources': self.source_ids,
            'scan_type': scan.SCAN_TYPE_INSPECT,
            'options': {
                'max_concurrency': self.args.max_concurrency}
        }
        disabled_optional_products \
            = get_optional_products(self.args.disabled_optional_products)
        enabled_ext_product_search \
            = get_enabled_products(self.args.enabled_ext_product_search,
                                   self.args.ext_product_search_dirs, False)
        if disabled_optional_products is not None:
            self.req_payload['options']['disabled_optional_products']\
                = disabled_optional_products
        if enabled_ext_product_search is not None:
            self.req_payload['options']['enabled_extended_product_search'] \
                = enabled_ext_product_search

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.SCAN_ADDED % json_data.get('name')))
