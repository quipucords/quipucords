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
"""Common module for handling request calls to the server"""

import requests

# Need to determine how we get this information; config file at install?
BASE_URL = 'http://127.0.0.1:8000'

POST = 'POST'
GET = 'GET'
PUT = 'PUT'
DELETE = 'DELETE'


UNKNOWN_ERROR_MSG = 'An unknown error occurred while attempting to create' \
                    ' the host credential.'

CONNECTION_ERROR_MSG = 'A connection error has occurred attempting to' \
                       ' communicate with the server. Check the ' \
                       'configuration and/or the status of the server.'

SSL_ERROR_MSG = 'A connection error has occurred attempting to' \
                ' communicate with the server over "https". Check the' \
                ' configuration and/or the status of the server.'


def post(path, payload):
    """Post JSON payload to the given path with the configured server location

    :param path: uri path after server and port (i.e. /api/v1/credentias/hosts)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.post(url, json=payload)


def get(path, params=None):
    """Get JSON data from the given path with the configured server location

    :param path: uri path after server and port (i.e. /api/v1/credentias/hosts)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :returns: reponse object
    """
    url = BASE_URL + path
    return requests.get(url, params=params)


def request(method, path, params=None, payload=None):
    """Generic handler for passing to specific request methods.

    :param method: the request method to execute
    :param path: uri path after server and port (i.e. /api/v1/credentias/hosts)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    :raises: AssertionError error if method is not supported
    """
    if method == POST:
        return post(path, payload)
    elif method == GET:
        return get(path, params)
    else:
        raise AssertionError('Unsupported request method %s' % (method))
