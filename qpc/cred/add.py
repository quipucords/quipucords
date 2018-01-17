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
"""CredAddCommand is used to add authentication credentials."""

from __future__ import print_function
from requests import codes
from qpc.request import POST
from qpc.clicommand import CliCommand
import qpc.cred as credential
from qpc.cred.utils import validate_sshkeyfile, build_credential_payload
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class CredAddCommand(CliCommand):
    """Defines the add command.

    This command is for creating new credentials which
    can be later associated with sources to gather facts.
    """

    SUBCOMMAND = credential.SUBCOMMAND
    ACTION = credential.ADD

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            credential.CREDENTIAL_URI, [codes.created])

        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.CRED_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--type', dest='type',
                                 choices=[credential.NETWORK_CRED_TYPE,
                                          credential.VCENTER_CRED_TYPE,
                                          credential.SATELLITE_CRED_TYPE],
                                 metavar='TYPE',
                                 help=_(messages.CRED_TYPE_HELP),
                                 required=True)
        self.parser.add_argument('--username', dest='username',
                                 metavar='USERNAME',
                                 help=_(messages.CRED_USER_HELP),
                                 required=True)
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--password', dest='password',
                           action='store_true',
                           help=_(messages.CRED_PWD_HELP))
        group.add_argument('--sshkeyfile', dest='filename',
                           metavar='FILENAME',
                           help=_(messages.CRED_SSH_HELP))
        self.parser.add_argument('--sshpassphrase', dest='ssh_passphrase',
                                 action='store_true',
                                 help=_(messages.CRED_SSH_PSPH_HELP))
        self.parser.add_argument('--sudo-password', dest='sudo_password',
                                 action='store_true',
                                 help=_(messages.CRED_SUDO_HELP))
        self.parser.add_argument('--become_method', dest='become_method',
                                 choices=['sudo', 'su', 'pbrun', 'pfexec',
                                          'doas', 'dzdo', 'ksu', 'runas'],
                                 metavar='BECOME_METHOD',
                                 help=_(messages.CRED_BECOME_METHOD_HELP))

    def _validate_args(self):
        CliCommand._validate_args(self)

        if 'filename' in self.args and self.args.filename:
            # check for file existence on system
            self.args.filename = validate_sshkeyfile(self.args.filename,
                                                     self.parser)

    def _build_data(self):
        """Construct the dictionary credential given our arguments.

        :returns: a dictionary representing the credential being added
        """
        self.req_payload = build_credential_payload(self.args, self.args.type)

    def _handle_response_success(self):
        print(_(messages.CRED_ADDED % self.args.name))
