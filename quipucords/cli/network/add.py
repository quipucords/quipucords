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
""" NetworkAddCommand is used to add network profiles for system scans
"""

from __future__ import print_function
import os
import sys
from requests import codes
from cli.request import POST, GET, request
from cli.clicommand import CliCommand
from cli.utils import read_in_file
import cli.network as network
from cli.network.utils import validate_port, build_profile_payload
import cli.auth as auth


# pylint: disable=too-few-public-methods
class NetworkAddCommand(CliCommand):
    """
    This command is for creating new network profiles which can be later used
    with scans to gather facts.
    """
    SUBCOMMAND = network.SUBCOMMAND
    ACTION = network.ADD

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            network.NETWORK_URI, [codes.created])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help='profile name', required=True)
        self.parser.add_argument('--hosts', dest='hosts', nargs='+',
                                 metavar='HOSTS', default=[],
                                 help='IP range to scan.'
                                      ' See "man qpc" for supported formats.',
                                 required=True)
        self.parser.add_argument('--auth', dest='auth', metavar='AUTH',
                                 nargs='+', default=[], help='credentials to '
                                 'associate with profile', required=True)
        self.parser.add_argument('--sshport', dest='ssh_port',
                                 metavar='SSHPORT', type=validate_port,
                                 help='SSHPORT for connection; default=22',
                                 default=22)

    def _validate_args(self):
        CliCommand._validate_args(self)

        if self.args.hosts and len(self.args.hosts) == 1:
            # check if a file and read in values
            filename = self.args.hosts[0]
            input_path = os.path.expanduser(os.path.expandvars(filename))
            if os.path.isfile(input_path):
                self.args.hosts = read_in_file(input_path)

        # check for valid auth values
        auth_list = ','.join(self.args.auth)
        response = request(parser=self.parser, method=GET, path=auth.AUTH_URI,
                           params={'name': auth_list},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            if len(json_data) == len(self.args.auth):
                self.args.credentials = []
                for cred_entry in json_data:
                    self.args.credentials.append(cred_entry['id'])
            else:
                for cred_entry in json_data:
                    cred_name = cred_entry['name']
                    self.args.auth.remove(cred_name)
                not_found_str = ','.join(self.args.auth)
                print('An error occurred while processing the "--auth" input'
                      ' values. References for the following auth could not'
                      ' be found: %s. Failed to add profile "%s".'
                      % (not_found_str, self.args.name))
                sys.exit(1)
        else:
            print('An error occurred while processing the "--auth" input'
                  ' values. Failed to add profile "%s"' % self.args.name)
            sys.exit(1)

    def _build_data(self):
        """Construct the dictionary auth given our arguments.

        :returns: a dictionary representing the network profile being added
        """
        self.req_payload = build_profile_payload(self.args)

    def _handle_response_success(self):
        print('Profile "%s" was added' % self.args.name)
