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
from xdg.BaseDirectory import xdg_data_home, xdg_config_home
from qpc.translation import _ as t
import qpc.messages as messages

QPC_PATH = 'qpc'
CONFIG_DIR = os.path.join(xdg_config_home, QPC_PATH)
DATA_DIR = os.path.join(xdg_data_home, QPC_PATH)
QPC_LOG = os.path.join(DATA_DIR, 'qpc.log')
QPC_SERVER_CONFIG = os.path.join(CONFIG_DIR, 'server.config')

CONFIG_HOST_KEY = 'host'
CONFIG_PORT_KEY = 'port'


# 'log' is a convenience for getting the appropriate logger from the
# logging module. Use it like this:
#
#   from rho.utilities import log
#   ...
#   log.error('Too many Tribbles!')

# pylint: disable=invalid-name
log = logging.getLogger('qpc')


def ensure_config_dir_exists():
    """Ensure the qpc configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)


def get_server_location():
    """Build URI from server configuration.

    :returns: The URI to the sonar server.
    """
    config = read_server_config()
    if config is None:
        # No configuration written to server.config
        return None

    server_locataion = 'http://{}:{}'.format(
        config[CONFIG_HOST_KEY], config[CONFIG_PORT_KEY])
    return server_locataion


def read_server_config():
    """Retrieve configuration for sonar server.

    :returns: The validate dictionary with configuration
    """
    # pylint: disable=too-many-return-statements
    if not os.path.exists(QPC_SERVER_CONFIG):
        return None

    with open(QPC_SERVER_CONFIG) as server_config_file:
        try:
            config = json.load(server_config_file)
        except json.decoder.JSONDecodeError:
            return None

        if CONFIG_HOST_KEY not in config or CONFIG_PORT_KEY not in config:
            return None

        host = config[CONFIG_HOST_KEY]
        port = config[CONFIG_PORT_KEY]

        if host is None or host == '':
            return None

        if port is None or port == '':
            return None

        if not isinstance(host, str):
            return None

        if not isinstance(port, int):
            return None

        return {CONFIG_HOST_KEY: host, CONFIG_PORT_KEY: port}


def write_server_config(server_config):
    """Write server configuration to server.config.

    :param server_config: dict containing server configuration
    """
    ensure_config_dir_exists()

    with open(QPC_SERVER_CONFIG, 'w') as configFile:
        json.dump(server_config, configFile)


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
    stderr_handler.setLevel(logging.WARNING)
    log.addHandler(stderr_handler)


def handle_error_response(response):
    """Print errors from response data.

    :param response: The response object with a dictionary of keys and
        lists of errors
    """
    try:
        response_data = response.json()
        for err_key, err_cases in response_data.items():
            error_context = 'Error'
            if err_key != 'non_field_errors':
                error_context = err_key
            for err_msg in err_cases:
                log.error('%s: %s', error_context, err_msg)
    except json.decoder.JSONDecodeError:
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
