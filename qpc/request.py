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
"""Common module for handling request calls to the server."""

import sys
import requests
from qpc.utils import log
from qpc.translation import _
from qpc.messages import SSL_ERROR_MSG, CONNECTION_ERROR_MSG

# Need to determine how we get this information; config file at install?
BASE_URL = 'http://127.0.0.1:8000'

POST = 'POST'
GET = 'GET'
PATCH = 'PATCH'
DELETE = 'DELETE'
PUT = 'PUT'


def post(path, payload):
    """Post JSON payload to the given path with the configured server location.

    :param path: path after server and port (i.e. /api/v1/credentials/hosts)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.post(url, json=payload)


def get(path, params=None):
    """Get JSON data from the given path with the configured server location.

    :param path:  path after server and port (i.e. /api/v1/credentials/hosts)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.get(url, params=params)


def patch(path, payload):
    """Patch JSON payload to the given path with the configured server location.

    :param path: path after server and port (i.e. /api/v1/credentials/hosts/1)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.patch(url, json=payload)


def delete(path):
    """Delete the item with the given path with the configured server location.

    :param path: path after server and port (i.e. /api/v1/credentials/hosts/1)
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.delete(url)


def put(path, payload):
    """Put JSON payload to the given path with the configured server location.

    :param path: path after server and port (i.e. /api/v1/credentials/hosts)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.put(url, json=payload)


def request(method, path, params=None, payload=None, parser=None):
    """Create a generic handler for passing to specific request methods.

    :param method: the request method to execute
    :param path: path after server and port (i.e. /api/v1/credentials/hosts)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :param payload: dictionary of payload to be posted
    :param parser: parser for printing usage on failure
    :returns: reponse object
    :raises: AssertionError error if method is not supported
    """
    try:
        if method == POST:
            return post(path, payload)
        elif method == GET:
            return get(path, params)
        elif method == PATCH:
            return patch(path, payload)
        elif method == DELETE:
            return delete(path)
        elif method == PUT:
            return put(path, payload)
        else:
            log.error('Unsupported request method %s', method)
            parser.print_help()
            sys.exit(1)
    except requests.exceptions.SSLError as ssl_error:
        print(_(SSL_ERROR_MSG))
        log.error(ssl_error)
        if parser is not None:
            parser.print_help()
        sys.exit(1)
    except requests.exceptions.ConnectionError as conn_err:
        print(_(CONNECTION_ERROR_MSG))
        log.error(conn_err)
        if parser is not None:
            parser.print_help()
        sys.exit(1)
