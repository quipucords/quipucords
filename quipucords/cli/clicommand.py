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
""" Base CLI Command Class """

from __future__ import print_function


# pylint: disable=too-few-public-methods
class CliCommand(object):

    """ Base class for all sub-commands. """
    def __init__(self, subcommand, action):
        self.subcommand = subcommand
        self.action = action
        self.args = None

    def _validate_args(self):
        """
        Sub-commands can override to do any argument validation they
        require.
        """
        pass

    def _do_command(self):
        """
        Sub-commands define this method to perform the
        required action once all options have been verified.
        """
        pass

    def main(self, args):
        """
        The method that does a basic check for command
        validity and set's the process in motion.
        """
        self.args = args
        self._validate_args()

        self._do_command()
