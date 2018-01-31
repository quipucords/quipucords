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
"""Quipucords Command Line utilities."""

from __future__ import print_function
import logging
import os
import json
from qpc.translation import _ as t
import qpc.messages as messages

QPC_PATH = 'qpc'
CONFIG_HOME_PATH = '~/.config/'
DATA_HOME_PATH = '~/.local/share/'
CONFIG_HOME = os.path.expanduser(CONFIG_HOME_PATH)
DATA_HOME = os.path.expanduser(DATA_HOME_PATH)
CONFIG_DIR = os.path.join(CONFIG_HOME, QPC_PATH)
DATA_DIR = os.path.join(DATA_HOME, QPC_PATH)
QPC_LOG = os.path.join(DATA_DIR, 'qpc.log')
QPC_SERVER_CONFIG = os.path.join(CONFIG_DIR, 'server.config')
QPC_CLIENT_TOKEN = os.path.join(CONFIG_DIR, 'client_token')

CONFIG_HOST_KEY = 'host'
CONFIG_PORT_KEY = 'port'
CONFIG_USE_HTTP = 'use_http'
CONFIG_SSL_VERIFY = 'ssl_verify'


# 'log' is a convenience for getting the appropriate logger from the
# logging module. Use it like this:
#
#   from rho.utilities import log
#   ...
#   log.error('Too many Tribbles!')

# pylint: disable=invalid-name
logging.captureWarnings(True)
log = logging.getLogger('qpc')


def ensure_config_dir_exists():
    """Ensure the qpc configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)


def get_ssl_verify():
    """Obtain configuration for using ssl cert verification."""
    config = read_server_config()
    if config is None:
        # No configuration written to server.config
        return None
    ssl_verify = config.get(CONFIG_SSL_VERIFY, False)
    if not ssl_verify:
        ssl_verify = False
    return ssl_verify


def get_server_location():
    """Build URI from server configuration.

    :returns: The URI to the sonar server.
    """
    config = read_server_config()
    if config is None:
        # No configuration written to server.config
        return None

    use_http = config.get(CONFIG_USE_HTTP, False)
    protocol = 'https'
    if use_http:
        protocol = 'http'

    server_location = '{}://{}:{}'.format(
        protocol, config[CONFIG_HOST_KEY], config[CONFIG_PORT_KEY])
    return server_location


try:
    exception_class = json.decoder.JSONDecodeError
except AttributeError:
    exception_class = ValueError


def read_client_token():
    """Retrieve client token for sonar server.

    :returns: The client token or None
    """
    if not os.path.exists(QPC_CLIENT_TOKEN):
        return None

    token = None
    with open(QPC_CLIENT_TOKEN) as client_token_file:
        try:
            token_json = json.load(client_token_file)
            token = token_json.get('token')
        except exception_class:
            pass

        return token


def read_server_config():
    """Retrieve configuration for sonar server.

    :returns: The validate dictionary with configuration
    """
    # pylint: disable=too-many-return-statements
    if not os.path.exists(QPC_SERVER_CONFIG):
        log.error('Server config %s was not found.',
                  QPC_SERVER_CONFIG)
        return None

    with open(QPC_SERVER_CONFIG) as server_config_file:
        try:
            config = json.load(server_config_file)
        except exception_class:
            return None

        host = config.get(CONFIG_HOST_KEY)
        port = config.get(CONFIG_PORT_KEY)
        use_http = config.get(CONFIG_USE_HTTP)
        ssl_verify = config.get(CONFIG_SSL_VERIFY, False)

        host_empty = host is None or host == ''
        port_empty = port is None or port == ''

        if host_empty or port_empty:
            return None

        if not isinstance(host, str):
            log.error('Server config %s has invalid value for host %s',
                      QPC_SERVER_CONFIG, host)
            return None

        if not isinstance(port, int):
            log.error('Server config %s has invalid value for port %s',
                      QPC_SERVER_CONFIG, port)
            return None

        if use_http is None:
            use_http = True

        if not isinstance(use_http, bool):
            log.error('Server config %s has invalid value for use_http %s',
                      QPC_SERVER_CONFIG, use_http)
            return None

        if (ssl_verify is not None and
                not isinstance(ssl_verify, bool) and
                not isinstance(ssl_verify, str)):
            log.error('Server config %s has invalid value for ssl_verify %s',
                      QPC_SERVER_CONFIG, ssl_verify)
            return None

        if (ssl_verify is not None and
                isinstance(ssl_verify, str) and
                not os.path.exists(ssl_verify)):
            log.error('Server config %s has invalid path for ssl_verify %s',
                      QPC_SERVER_CONFIG, ssl_verify)
            return None

        return {CONFIG_HOST_KEY: host,
                CONFIG_PORT_KEY: port,
                CONFIG_USE_HTTP: use_http,
                CONFIG_SSL_VERIFY: ssl_verify}


def write_server_config(server_config):
    """Write server configuration to server.config.

    :param server_config: dict containing server configuration
    """
    ensure_config_dir_exists()

    with open(QPC_SERVER_CONFIG, 'w') as configFile:
        json.dump(server_config, configFile)


def write_client_token(client_token):
    """Write client token to file client_token.

    :param client_token: dict containing client_token
    """
    ensure_config_dir_exists()

    with open(QPC_CLIENT_TOKEN, 'w') as configFile:
        json.dump(client_token, configFile)


def delete_client_token():
    """Remove file client_token."""
    ensure_config_dir_exists()
    os.remove(QPC_CLIENT_TOKEN)


def ensure_data_dir_exists():
    """Ensure the qpc data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def setup_logging(verbosity):
    """Set up Python logging for qpc.

    Must be run after ensure_data_dir_exists().

    :param verbosity: verbosity level, as measured in -v's on the command line.
        Can be None for default.
    """
    if verbosity is None:
        log_level = logging.WARNING
    elif verbosity == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    # Using basicConfig here means that all log messages, even
    # those not coming from rho, will go to the log file
    logging.basicConfig(filename=QPC_LOG)
    # but we only adjust the log level for the 'rho' logger.
    log.setLevel(log_level)
    # the StreamHandler sends warnings and above to stdout, but
    # only for messages going to the 'rho' logger, i.e. Rho
    # output.
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.ERROR)
    log.addHandler(stderr_handler)


def handle_error_response(response):
    """Print errors from response data.

    :param response: The response object with a dictionary of keys and
        lists of errors
    """
    try:
        response_data = response.json()
        if isinstance(response_data, str):
            log.error('Error: %s', str(response_data))
        if isinstance(response_data, dict):
            for err_key, err_cases in response_data.items():
                error_context = 'Error'
                if (err_key != 'non_field_errors' and
                        err_key != 'detail' and err_key != 'options'):
                    error_context = err_key
                if isinstance(err_cases, str):
                    log.error('%s: %s', error_context, err_cases)
                elif isinstance(err_cases, dict):
                    log.error('%s: %s', error_context, err_cases)
                else:
                    for err_msg in err_cases:
                        log.error('%s: %s', error_context, err_msg)
        elif isinstance(response_data, list):
            for err in response_data:
                log.error('Error: %s', err)
        else:
            log.error('Error: %s', str(response_data))
    except exception_class:
        pass


def pretty_print(json_data):
    """Provide pretty printing of output json data.

    :param json_data: the json data to pretty print
    :returns: the pretty print string of the json data
    """
    return json.dumps(json_data, sort_keys=True, indent=4,
                      separators=(',', ': '))


# Read in a file and make it a list
def read_in_file(filename):
    """Read values from file into a list object. Expecting newline delimited.

    :param filename: the filename to read
    :returns: the list of values found in the file
    :raises: ValueError if incoming value is not a file that could be found
    """
    result = None
    input_path = os.path.expanduser(os.path.expandvars(filename))
    if os.path.isfile(input_path):
        try:
            with open(input_path, 'r') as in_file:
                result = in_file.read().splitlines()
        except EnvironmentError as err:
            err_msg = t(messages.READ_FILE_ERROR % (input_path, err))
            log.error(err_msg)
        return result
    else:
        raise ValueError(t(messages.NOT_A_FILE % input_path))
