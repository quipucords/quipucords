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
""" AuthAddCommand is used to add authentication credentials
for system access
"""

from __future__ import print_function
import sys
import os
from getpass import getpass
import requests
from cli.utils import log, handle_error_response
from cli.clicommand import CliCommand
import cli.auth as auth
from cli.request import post, CONNECTION_ERROR_MSG, SSL_ERROR_MSG


# pylint: disable=too-few-public-methods
class AuthAddCommand(CliCommand):
    """
    This command is for creating new auths which can be later associated with
    profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.ADD

    def __init__(self, subparsers):
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION)
        self.parser = subparsers.add_parser(self.ACTION)
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help='auth credential name', required=True)
        self.parser.add_argument('--username', dest='username',
                                 metavar='USERNAME',
                                 help='user name for authenticating'
                                      ' against target system', required=True)
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--password', dest='password',
                           action='store_true',
                           help='password for authenticating against'
                                ' target system')
        group.add_argument('--sshkeyfile', dest='filename',
                           metavar='FILENAME',
                           help='file containing SSH key')
        self.parser.add_argument('--sudo-password', dest='sudo_password',
                                 action='store_true',
                                 help='password for running sudo')

    def _validate_args(self):
        CliCommand._validate_args(self)

        if self.args.filename:
            # check for file existence on system
            keyfile = self.args.filename
            keyfile_path = os.path.abspath(os.path.normpath(keyfile))
            if not os.path.isfile(keyfile_path):
                print('The file path provided, %s, could not be found on the '
                      'system. Please provide a valid location for the '
                      '"--sshkeyfile" argument.' % (keyfile))
                self.parser.print_help()
                sys.exit(1)
            else:
                # set filename to the resolved keyfile_path
                self.args.filename = keyfile_path

    def _get_password(self, data):
        """Collect the password value and place in auth dictionary.

        :param data: a dictionary representing the auth being added
        """
        if self.args.password:
            print('Provide connection password.')
            pass_prompt = getpass()
            data['password'] = pass_prompt or None
        else:
            data['password'] = None
        if self.args.sudo_password:
            print('Provide password for sudo.')
            pass_prompt = getpass()
            data['sudo_password'] = pass_prompt or None
        else:
            data['sudo_password'] = None

    def _make_auth(self):
        """Construct the dictionary auth given our arguments.

        :returns: a dictionsary representing the auth being added
        """
        data = {'name': self.args.name,
                'username': self.args.username}
        data['ssh_keyfile'] = self.args.filename or None
        self._get_password(data)

        return data

    def _do_command(self):
        data = self._make_auth()

        try:
            response = post(auth.AUTH_URI_POST, data)
            # pylint: disable=no-member
            if response.status_code != requests.codes.created:
                # handle error cases
                r_data = response.json()
                handle_error_response(r_data)
                self.parser.print_help()
                sys.exit(1)
            else:
                print('Auth "%s" was added' % self.args.name)
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
