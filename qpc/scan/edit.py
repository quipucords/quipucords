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
"""ScanEditCommand is used to edit existing scans."""

from __future__ import print_function

import sys

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import GET, PATCH, request
from qpc.scan.utils import (build_scan_payload,
                            get_enabled_products,
                            get_optional_products,
                            get_source_ids)
from qpc.translation import _

from requests import codes


# pylint: disable=too-few-public-methods
class ScanEditCommand(CliCommand):
    """Defines the edit command.

    This command is for editing existing scans.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.EDIT

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PATCH,
                            scan.SCAN_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.SCAN_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--sources', dest='sources', nargs='+',
                                 metavar='SOURCES', default=[],
                                 help=_(messages.SOURCES_NAME_HELP),
                                 required=False)
        self.parser.add_argument('--max-concurrency', dest='max_concurrency',
                                 metavar='MAX_CONCURRENCY',
                                 type=int, default=None,
                                 help=_(messages.SCAN_MAX_CONCURRENCY_HELP))
        self.parser.add_argument('--disabled-optional-products',
                                 dest='disabled_optional_products',
                                 nargs='*',
                                 choices=scan.OPTIONAL_PRODUCTS,
                                 metavar='DISABLED_PRODUCT_LIST',
                                 help=_(messages.DISABLE_OPT_PRODUCTS_HELP),
                                 required=False)
        self.parser.add_argument('--enabled-ext-product-search',
                                 dest='enabled_ext_product_search',
                                 nargs='*',
                                 choices=scan.OPTIONAL_PRODUCTS,
                                 metavar='EXTENDED_PRODUCT_SEARCH_LIST',
                                 help=_(messages.SCAN_ENABLED_PRODUCT_HELP),
                                 required=False)
        self.parser.add_argument('--ext-product-search-dirs',
                                 dest='ext_product_search_dirs',
                                 nargs='*',
                                 metavar='EXTENDED_PRODUCT_SEARCH_DIRS',
                                 help=_(messages.SCAN_EXT_SEARCH_DIRS_HELP),
                                 required=False)
        self.source_ids = []

    def _validate_args(self):
        """Validate the edit arguments."""
        CliCommand._validate_args(self)
        # Check to see if args were provided
        if not(self.args.sources or self.args.max_concurrency or
               (self.args.disabled_optional_products or
                self.args.disabled_optional_products == []) or
               (self.args.enabled_ext_product_search or
                self.args.enabled_ext_product_search == []) or
               (self.args.ext_product_search_dirs or
                self.args.ext_product_search_dirs == [])):
            print(_(messages.SCAN_EDIT_NO_ARGS % (self.args.name)))
            self.parser.print_help()
            sys.exit(1)

        # check for existence of scan
        exists = False
        response = request(parser=self.parser, method=GET,
                           path=scan.SCAN_URI,
                           params={'name': self.args.name},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            count = json_data.get('count', 0)
            results = json_data.get('results', [])
            if count >= 1:
                for result in results:
                    if result['name'] == self.args.name:
                        scan_entry = result
                        self.req_path \
                            = self.req_path + str(scan_entry['id']) + '/'
                        exists = True
            if not exists or count == 0:
                print(_(messages.SCAN_DOES_NOT_EXIST % self.args.name))
                sys.exit(1)
        else:
            print(_(messages.SCAN_DOES_NOT_EXIST % self.args.name))
            sys.exit(1)

        # check for valid source values
        source_ids = []
        if self.args.sources:
            # check for existence of sources
            not_found, source_ids = get_source_ids(self.parser,
                                                   self.args.sources)
            if not_found is True:
                sys.exit(1)
        self.source_ids = source_ids

    def _build_data(self):
        """Construct the payload for a scan edit given our arguments.

        :returns: a dictionary representing the scan changes
        """
        disabled_optional_products \
            = get_optional_products(self.args.disabled_optional_products)
        enabled_ext_product_search \
            = get_enabled_products(self.args.enabled_ext_product_search,
                                   self.args.ext_product_search_dirs, True)
        self.req_payload \
            = build_scan_payload(self.args,
                                 self.source_ids,
                                 disabled_optional_products,
                                 enabled_ext_product_search)

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.SCAN_UPDATED % json_data.get('name')))
