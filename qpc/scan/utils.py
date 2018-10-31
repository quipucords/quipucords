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

from qpc import messages, scan, source
from qpc.request import GET, request
from qpc.translation import _

from requests import codes


def get_source_ids(parser, source_names):
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


def get_scan_object_id(parser, name):
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


def get_optional_products(disabled_optional_products):
    """Construct a dictionary based on the disable-optional-products args.

    :returns: a dictionary representing the collection status of optional
    products
    """
    disabled_products = {}
    disabled_default = {scan.JBOSS_FUSE: False,
                        scan.JBOSS_EAP: False,
                        scan.JBOSS_BRMS: False,
                        scan.JBOSS_WS: False}

    if disabled_optional_products:
        for product in disabled_optional_products:
            disabled_products[product] = True
    elif disabled_optional_products == []:
        return disabled_default
    else:
        return None

    return disabled_products


def get_enabled_products(enabled_ext_product_search,
                         ext_product_search_dirs, edit):
    """Construct a dictionary based on the enabled extended product search args.

    :param enabled_ext_product_search The products to enable
    :param ext_product_search_dirs: The search dirs for the extended products
    :param edit: boolean regarding if we are editing the extended products
    :returns: a dictionary representing the enabled search status of extended
    products
    """
    enabled_products = {}
    # if both the extended products and extended product dirs are [],
    # do a reset of all
    if enabled_ext_product_search == [] and ext_product_search_dirs == []:
        enabled_default = {scan.JBOSS_FUSE: False,
                           scan.JBOSS_EAP: False,
                           scan.JBOSS_BRMS: False,
                           scan.JBOSS_WS: False,
                           'search_directories': []}
        return enabled_default
    if ext_product_search_dirs == []:
        enabled_default = {'search_directories': []}
        # if just the dirs are reset, check if products are provided
        if enabled_ext_product_search:
            for product in enabled_ext_product_search:
                enabled_default[product] = True
        return enabled_default
    # pylint: disable=no-else-return
    if enabled_ext_product_search == []:
        enabled_default = {scan.JBOSS_FUSE: False,
                           scan.JBOSS_EAP: False,
                           scan.JBOSS_BRMS: False,
                           scan.JBOSS_WS: False}
        # if just the products are reset, check if dirs are provided
        if ext_product_search_dirs:
            enabled_default['search_directories'] = ext_product_search_dirs
        return enabled_default
    # else we grab the provided products
    elif enabled_ext_product_search:
        for product in enabled_ext_product_search:
            enabled_products[product] = True
        if ext_product_search_dirs:
            enabled_products['search_directories'] = ext_product_search_dirs
        return enabled_products
    elif ext_product_search_dirs and not enabled_ext_product_search:
        # if only search dirs are provided, we must make sure that it is an
        # edit. We set the dirs but not products
        if edit:
            enabled_products['search_directories'] = ext_product_search_dirs
            return enabled_products
    return None


# pylint: disable=R0912
def build_scan_payload(args, sources, disabled_optional_products,
                       enabled_ext_product_search):
    """Construct payload from command line arguments.

    :param args: the command line arguments
    :param sources: the source ids
    :param disabled_optional_products: the disabled products dictionary
    :param enabled_extended_product_search: the enabled products dictionary
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
    if hasattr(args, 'disabled_optional_products') \
            and (args.disabled_optional_products or
                 args.disabled_optional_products == []):
        if options is None:
            options = \
                {'disabled_optional_products': disabled_optional_products}
        else:
            options['disabled_optional_products'] = disabled_optional_products
    # pylint: disable=too-many-boolean-expressions
    if (hasattr(args, 'enabled_ext_product_search') or
            (hasattr(args, 'ext-product-search-dirs'))) and \
            (args.enabled_ext_product_search or
             args.enabled_ext_product_search == [] or
             args.ext_product_search_dirs or
             args.ext_product_search_dirs == []):
        if options is None:
            options = {'enabled_extended_product_search':
                       enabled_ext_product_search}
        else:
            options['enabled_extended_product_search'] = \
                enabled_ext_product_search
    if options is not None:
        req_payload['options'] = options
    req_payload['scan_type'] = scan.SCAN_TYPE_INSPECT

    return req_payload
