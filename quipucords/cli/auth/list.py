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
""" AuthListCommand is used to list authentication credentials
for system access
"""

from __future__ import print_function
import sys
import requests
from cli.utils import log, handle_error_response, pretty_print
from cli.clicommand import CliCommand
import cli.auth as auth
from cli.request import get, CONNECTION_ERROR_MSG, SSL_ERROR_MSG


# pylint: disable=too-few-public-methods
class AuthListCommand(CliCommand):
    """
    This command is for listing auths which can be later associated with
    profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.LIST

    def __init__(self, subparsers):
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION)
        self.parser = subparsers.add_parser(self.ACTION)

    def _do_command(self):
        try:
            response = get(auth.AUTH_URI_GET_LIST)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                # handle error cases
                r_data = response.json()
                handle_error_response(r_data)
                self.parser.print_help()
                sys.exit(1)
            else:
                json_data = response.json()
                if json_data == []:
                    print('No credentials exist yet.')
                else:
                    data = pretty_print(json_data)
                    print(data)
        except requests.exceptions.SSLError as ssl_error:
            print(SSL_ERROR_MSG)
            log.error(ssl_error)
            self.parser.print_help()
            sys.exit(1)
        except requests.exceptions.ConnectionError as conn_err:
            print(CONNECTION_ERROR_MSG)
            log.error(conn_err)
            self.parser.print_help()
            sys.exit(1)
