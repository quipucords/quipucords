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
"""Common module for handling request calls to the server."""

import json
import sys

from qpc import messages
from qpc.translation import _
from qpc.utils import (get_server_location,
                       get_ssl_verify,
                       handle_error_response,
                       log,
                       log_request_info,
                       read_client_token)

import requests


# Need to determine how we get this information; config file at install?

POST = 'POST'
GET = 'GET'
PATCH = 'PATCH'
DELETE = 'DELETE'
PUT = 'PUT'

CONNECTION_ERROR_MSG = messages.CONNECTION_ERROR_MSG
SSL_ERROR_MSG = messages.SSL_ERROR_MSG

# pylint: disable=invalid-name
try:
    exception_class = json.decoder.JSONDecodeError
except AttributeError:
    exception_class = ValueError


def handle_general_errors(response):
    """Handle general errors.

    :param response: The response object.
    :returns: The response object.
    """
    token_expired = {'detail': 'Token has expired'}
    response_data = None
    try:
        response_data = response.json()
    except exception_class:
        pass

    if response.status_code == 401:
        handle_error_response(response)
        log.error(_(messages.SERVER_LOGIN_REQUIRED))
        log.error('$ qpc server login')
        sys.exit(1)
    elif (response.status_code == 400 and
          response_data == token_expired):
        handle_error_response(response)
        log.error(_(messages.SERVER_LOGIN_REQUIRED))
        log.error('$ qpc server login')
        sys.exit(1)
    elif response.status_code == 500:
        handle_error_response(response)
        log.error(_(messages.SERVER_INTERNAL_ERROR))
        sys.exit(1)

    return response


def post(url, payload, headers=None):
    """Post JSON payload to the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/scans/)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.post(url, json=payload, headers=headers, verify=ssl_verify)


def get(url, params=None, headers=None):
    """Get JSON data from the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.get(url, params=params, headers=headers, verify=ssl_verify)


def patch(url, payload, headers=None):
    """Patch JSON payload to the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.patch(url, json=payload, headers=headers,
                          verify=ssl_verify)


def delete(url, headers=None):
    """Delete the item with the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.delete(url, headers=headers, verify=ssl_verify)


def put(url, payload, headers=None):
    """Put JSON payload to the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.put(url, json=payload, headers=headers, verify=ssl_verify)


# pylint: disable=too-many-arguments, too-many-branches
def request(method, path, params=None, payload=None,
            parser=None, headers=None):
    """Create a generic handler for passing to specific request methods.

    :param method: the request method to execute
    :param path: path after server and port (i.e. /api/v1/credentials)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :param payload: dictionary of payload to be posted
    :param parser: parser for printing usage on failure
    :param headers: headers to include
    :returns: reponse object
    :raises: AssertionError error if method is not supported
    """
    # grab the cli command for the log if the parser is provided
    log_command = None
    if parser is not None:
        log_command = parser.prog
    req_headers = {}
    token = read_client_token()
    # create the url by adding the path to the configured server location
    url = get_server_location() + path
    if headers:
        req_headers.update(headers)
    if token:
        req_headers['Authorization'] = 'Token {}'.format(token)

    try:
        if method == POST:
            result = handle_general_errors(post(url, payload, req_headers))
        elif method == GET:
            result = handle_general_errors(get(url, params, req_headers))
        elif method == PATCH:
            result = handle_general_errors(patch(url, payload, req_headers))
        elif method == DELETE:
            result = handle_general_errors(delete(url, req_headers))
        elif method == PUT:
            result = handle_general_errors(put(url, payload, req_headers))
        else:
            log.error('Unsupported request method %s', method)
            parser.print_help()
            sys.exit(1)
        try:
            log_request_info(method, log_command,
                             url, result.json(), result.status_code)
        except ValueError:
            log_request_info(method, log_command,
                             url, result.text, result.status_code)
        return result
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
