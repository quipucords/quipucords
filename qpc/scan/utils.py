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
"""Utilities for the scan module."""

from __future__ import print_function
from requests import codes
from qpc.request import GET, request
import qpc.source as source
import qpc.scan as scan
from qpc.translation import _
import qpc.messages as messages


def _get_source_ids(parser, source_names):
    """Grab the source ids from the source if it exists.

    :returns Boolean regarding the existence of source &
    the source ids
    """
    not_found = False
    source_ids = []
    for source_name in set(source_names):
        # check for existence of source
        response = request(parser=parser, method=GET,
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


def _get_scan_object_id(parser, name):
    """Grab the scan id from the scan object if it exists.

    :returns Boolean regarding the existence of the object &
    the scan object id
    """
    found = False
    scan_object_id = None
    response = request(parser=parser, method=GET,
                       path=scan.SCAN_URI,
                       params={'name': name},
                       payload=None)
    if response.status_code == codes.ok:  # pylint: disable=no-member
        json_data = response.json()
        count = json_data.get('count', 0)
        results = json_data.get('results', [])
        if count >= 1:
            for result in results:
                if result['name'] == name:
                    scan_object_id = str(result['id']) + '/'
                    found = True
        if not found or count == 0:
            print(_(messages.SCAN_DOES_NOT_EXIST % name))
    else:
        print(_(messages.SCAN_DOES_NOT_EXIST % name))
    return found, scan_object_id


def _get_optional_products(disable_optional_products):
    """Construct a dictionary based on the disable-optional-products args.

    :returns: a dictionary representing the collection status of optional
    products
    """
    optional_product_status = {}

    if disable_optional_products:
        for product in disable_optional_products:
            optional_product_status[product] = False
    else:
        return None

    return optional_product_status


# pylint: disable=R0912
def build_scan_payload(args, sources, disable_optional_products):
    """Construct payload from command line arguments.

    :param args: the command line arguments
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the dictionary for the request payload
    """
    req_payload = {'name': args.name}
    options = None

    if hasattr(args, 'sources') and args.sources:
        req_payload['sources'] = sources

    if hasattr(args, 'max_concurrency') and args.max_concurrency:
        if options is None:
            options = {'max_concurrency': args.max_concurrency}
        else:
            options['max_concurrency'] = args.max_concurrency
    if hasattr(args, 'disable_optional_products') \
            and args.disable_optional_products:
        if options is None:
            options = \
                {'disable_optional_products': args.disable_optional_products}
        else:
            options['disable_optional_products'] = disable_optional_products
    if options is not None:
        req_payload['options'] = options
    req_payload['scan_type'] = scan.SCAN_TYPE_INSPECT

    return req_payload
