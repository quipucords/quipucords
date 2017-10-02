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
""" Quipucords Command Line utilities """

from __future__ import print_function
import logging
import os
import json
from xdg.BaseDirectory import xdg_data_home, xdg_config_home

QPC_PATH = 'qpc'
CONFIG_DIR = os.path.join(xdg_config_home, QPC_PATH)
DATA_DIR = os.path.join(xdg_data_home, QPC_PATH)
QPC_LOG = os.path.join(DATA_DIR, 'qpc.log')


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
    """Print errors from response data

    :param response: The response object with a dictionary of keys and
        lists of errors
    """
    try:
        response_data = response.json()
        for _, err_cases in response_data.items():
            for err_msg in err_cases:
                log.error(err_msg)
    except json.decoder.JSONDecodeError:
        pass


def pretty_print(json_data):
    """Provide pretty printing of output json data

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
    """
    result = None
    input_path = os.path.expanduser(os.path.expandvars(filename))
    try:
        with open(input_path, 'r') as in_file:
            result = in_file.read().splitlines()
    except EnvironmentError as err:
        log.error('Error reading from %s: %s', input_path, err)
    return result
