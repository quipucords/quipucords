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
"""ServerStatusCommand is used to show the server status."""

from __future__ import print_function

import sys

from qpc import messages, server
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import (pretty_print,
                       validate_write_file,
                       write_file)

from requests import codes


# pylint: disable=too-few-public-methods
class ServerStatusCommand(CliCommand):
    """Defines the server status command.

    This command is viewing the server version.
    """

    SUBCOMMAND = server.SUBCOMMAND
    ACTION = server.STATUS

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            server.STATUS_URI, [codes.ok])
        self.parser.add_argument('--output-file', dest='path', metavar='PATH',
                                 help=_(messages.STATUS_PATH_HELP),
                                 required=False)

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.path:
            try:
                validate_write_file(self.args.path, 'output-file')
            except ValueError as error:
                print(error)
                sys.exit(1)

    def _build_req_params(self):
        self.req_path = server.STATUS_URI

    def _handle_response_success(self):
        json_data = self.response.json()
        status = pretty_print(json_data)
        if self.args.path:
            try:
                write_file(self.args.path, status)
                print(_(messages.STATUS_SUCCESSFULLY_WRITTEN))
            except EnvironmentError as err:
                err_msg = _(messages.WRITE_FILE_ERROR % (self.args.path, err))
                print(err_msg)
        else:
            print(status)

    def _handle_response_error(self):
        print(_(messages.SERVER_STATUS_FAILURE))
        sys.exit(1)
