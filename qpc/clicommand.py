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
"""Base CLI Command Class."""

from __future__ import print_function

import sys

from qpc.request import request
from qpc.utils import handle_error_response, log_args


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class CliCommand():
    """Base class for all sub-commands."""

    # pylint: disable=too-many-arguments
    def __init__(self, subcommand, action, parser, req_method, req_path,
                 success_codes):
        """Create cli command base object."""
        self.subcommand = subcommand
        self.action = action
        self.parser = parser
        self.req_method = req_method
        self.req_path = req_path
        self.success_codes = success_codes
        self.args = None
        self.req_payload = None
        self.req_params = None
        self.req_headers = None
        self.response = None

    def _validate_args(self):
        """Sub-commands can override."""
        pass

    def _build_req_params(self):
        """Sub-commands can override to construct request parameters."""
        pass

    def _build_data(self):
        """Sub-commands can define to construct request payload."""
        pass

    def _handle_response_error(self):
        """Sub-commands can override this method to perform error handling."""
        handle_error_response(self.response)
        sys.exit(1)

    def _handle_response_success(self):
        """Sub-commands can override to perform success handling."""
        pass

    def _do_command(self):
        """Execute command flow.

        Sub-commands define this method to perform the
        required action once all options have been verified.
        """
        self._build_req_params()
        self._build_data()
        self.response = request(method=self.req_method,
                                path=self.req_path,
                                params=self.req_params,
                                payload=self.req_payload,
                                headers=self.req_headers,
                                parser=self.parser)
        # pylint: disable=no-member
        if self.response.status_code not in self.success_codes:
            # handle error cases
            self._handle_response_error()
        else:
            self._handle_response_success()

    def main(self, args):
        """Trigger main command flow.

        The method that does a basic check for command
        validity and set's the process in motion.
        """
        self.args = args
        self._validate_args()
        log_args(self.args)

        self._do_command()
