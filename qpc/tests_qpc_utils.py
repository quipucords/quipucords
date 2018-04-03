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
"""Test the utils module."""

import os
import unittest

from qpc import utils


class UtilsTests(unittest.TestCase):
    """Class for testing the utils module qpc."""

    def test_read_client_token(self):
        """Testing the read client token function."""
        check_value = False
        if not os.path.exists(utils.QPC_CLIENT_TOKEN):
            check_value = True
            expected_token = '100'
            token_json = {'token': expected_token}
            utils.write_client_token(token_json)
        token = utils.read_client_token()
        self.assertTrue(isinstance(token, str))
        if check_value:
            self.assertEqual(token, expected_token)
