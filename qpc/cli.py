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
""" Quipucords Command Line Interface """

from __future__ import print_function
from argparse import ArgumentParser
import qpc.auth as auth
import qpc.network as network
import qpc.scan as scan
from qpc.utils import ensure_config_dir_exists, ensure_data_dir_exists, \
    setup_logging
from qpc.auth.add import AuthAddCommand
from qpc.auth.list import AuthListCommand
from qpc.auth.edit import AuthEditCommand
from qpc.auth.show import AuthShowCommand
from qpc.auth.clear import AuthClearCommand
from qpc.network.add import NetworkAddCommand
from qpc.network.list import NetworkListCommand
from qpc.network.show import NetworkShowCommand
from qpc.network.clear import NetworkClearCommand
from qpc.network.edit import NetworkEditCommand
from qpc.scan.start import ScanStartCommand
from qpc.scan.list import ScanListCommand
from qpc.scan.show import ScanShowCommand
from qpc.translation import _
import qpc.messages as messages
from . import __version__


# pylint: disable=too-few-public-methods
class CLI(object):
    """Class responsible for displaying ussage or matching inputs
    to the valid set of commands supported by qpc.
    """
    def __init__(self, name="cli", usage=None, shortdesc=None,
                 description=None):
        self.shortdesc = shortdesc
        if shortdesc is not None and description is None:
            description = shortdesc
        self.parser = ArgumentParser(usage=usage, description=description)
        self.parser.add_argument('--version', action='version',
                                 version=__version__)
        self.parser.add_argument('-v', dest='verbosity', action='count',
                                 help=_(messages.VERBOSITY_HELP))
        self.subparsers = self.parser.add_subparsers(dest='subcommand')
        self.name = name
        self.args = None
        self.subcommands = {}
        self._add_subcommand(auth.SUBCOMMAND,
                             [AuthAddCommand, AuthListCommand,
                              AuthEditCommand, AuthShowCommand,
                              AuthClearCommand])
        self._add_subcommand(network.SUBCOMMAND,
                             [NetworkAddCommand, NetworkListCommand,
                              NetworkShowCommand, NetworkClearCommand,
                              NetworkEditCommand])

        self._add_subcommand(scan.SUBCOMMAND,
                             [ScanStartCommand, ScanListCommand,
                              ScanShowCommand])
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
        """Method determine whether to display usage or pass input
        to find the best command match. If no match is found the
        usage is displayed
        """
        self.args = self.parser.parse_args()
        setup_logging(self.args.verbosity)

        if self.args.subcommand in self.subcommands:
            subcommand = self.subcommands[self.args.subcommand]
            if self.args.action in subcommand:
                action = subcommand[self.args.action]
                action.main(self.args)
            else:
                self.parser.print_help()
        else:
            self.parser.print_help()
