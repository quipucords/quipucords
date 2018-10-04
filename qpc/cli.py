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
"""Quipucords Command Line Interface."""

from __future__ import print_function

import sys
from argparse import ArgumentParser


from qpc import (cred, messages,
                 report, scan,
                 server, source)
from qpc.cred.commands import (CredAddCommand,
                               CredClearCommand,
                               CredEditCommand,
                               CredListCommand,
                               CredShowCommand,)
from qpc.report.commands import (ReportDetailCommand,
                                 ReportJobCommand,
                                 ReportMergeCommand,
                                 ReportSummaryCommand)
from qpc.scan.commands import (ScanAddCommand,
                               ScanCancelCommand,
                               ScanClearCommand,
                               ScanEditCommand,
                               ScanJobCommand,
                               ScanListCommand,
                               ScanPauseCommand,
                               ScanRestartCommand,
                               ScanShowCommand,
                               ScanStartCommand)
from qpc.server.commands import (ConfigureHostCommand,
                                 LoginHostCommand,
                                 LogoutHostCommand)
from qpc.source.commands import (SourceAddCommand,
                                 SourceClearCommand,
                                 SourceEditCommand,
                                 SourceListCommand,
                                 SourceShowCommand)
from qpc.translation import _
from qpc.utils import (ensure_config_dir_exists,
                       ensure_data_dir_exists,
                       get_server_location,
                       log,
                       read_client_token,
                       setup_logging)

from . import __version__


# pylint: disable=too-few-public-methods
class CLI():
    """Defines the CLI class.

    Class responsible for displaying usage or matching inputs
    to the valid set of commands supported by qpc.
    """

    def __init__(self, name='cli', usage=None, shortdesc=None,
                 description=None):
        """Create main command line handler."""
        self.shortdesc = shortdesc
        if shortdesc is not None and description is None:
            description = shortdesc
        self.parser = ArgumentParser(usage=usage, description=description)
        self.parser.add_argument('--version', action='version',
                                 version=__version__)
        self.parser.add_argument('-v', dest='verbosity', action='count',
                                 default=0, help=_(messages.VERBOSITY_HELP))
        self.subparsers = self.parser.add_subparsers(dest='subcommand')
        self.name = name
        self.args = None
        self.subcommands = {}
        self._add_subcommand(server.SUBCOMMAND,
                             [ConfigureHostCommand, LoginHostCommand,
                              LogoutHostCommand])
        self._add_subcommand(cred.SUBCOMMAND,
                             [CredAddCommand, CredListCommand,
                              CredEditCommand, CredShowCommand,
                              CredClearCommand])
        self._add_subcommand(source.SUBCOMMAND,
                             [SourceAddCommand, SourceListCommand,
                              SourceShowCommand, SourceClearCommand,
                              SourceEditCommand])

        self._add_subcommand(scan.SUBCOMMAND,
                             [ScanAddCommand, ScanStartCommand,
                              ScanListCommand, ScanShowCommand,
                              ScanPauseCommand, ScanCancelCommand,
                              ScanRestartCommand, ScanEditCommand,
                              ScanClearCommand, ScanJobCommand])
        self._add_subcommand(report.SUBCOMMAND,
                             [ReportSummaryCommand,
                              ReportDetailCommand,
                              ReportMergeCommand,
                              ReportJobCommand])
        ensure_data_dir_exists()
        ensure_config_dir_exists()

    def _add_subcommand(self, subcommand, actions):
        subcommand_parser = self.subparsers.add_parser(subcommand)
        action_subparsers = subcommand_parser.add_subparsers(dest='action')
        self.subcommands[subcommand] = {}
        for action in actions:
            action_inst = action(action_subparsers)
            action_dic = self.subcommands[action.SUBCOMMAND]
            action_dic[action.ACTION] = action_inst

    def main(self):
        """Execute of subcommand operation.

        Method determine whether to display usage or pass input
        to find the best command match. If no match is found the
        usage is displayed
        """
        self.args = self.parser.parse_args()
        setup_logging(self.args.verbosity)
        is_server_cmd = self.args.subcommand == server.SUBCOMMAND
        is_server_login = is_server_cmd and self.args.action == server.LOGIN
        is_server_logout = is_server_cmd and self.args.action == server.LOGOUT

        if not is_server_cmd or is_server_login or is_server_logout:
            # Before attempting to run command, check server location
            server_location = get_server_location()
            if server_location is None or server_location == '':
                log.error(_(messages.SERVER_CONFIG_REQUIRED))
                log.error('$ qpc server config --host HOST --port PORT')
                sys.exit(1)

        if ((not is_server_cmd or is_server_logout) and
                not read_client_token()):
            log.error(_(messages.SERVER_LOGIN_REQUIRED))
            log.error('$ qpc server login')
            sys.exit(1)

        if self.args.subcommand in self.subcommands:
            subcommand = self.subcommands[self.args.subcommand]
            if self.args.action in subcommand:
                action = subcommand[self.args.action]
                action.main(self.args)
            else:
                self.parser.print_help()
        else:
            self.parser.print_help()
