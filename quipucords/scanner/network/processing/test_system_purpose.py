# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of system purpose fact."""


import unittest

from scanner.network.processing import system_purpose
from scanner.network.processing.util_for_test import ansible_result


class TestProcessSystemPurpose(unittest.TestCase):
    """Test ProcessSystemPurpose."""

    def test_success_case(self):
        """Valid system purpose json."""
        input_data = """
            {
                "_version": "1",
                "role": "server",
                "addons": [
                    "ibm"
                ],
                "service_level_agreement": "self-support",
                "usage_type": "dev"
            }
            """

        expected = {
            "_version": "1",
            "role": "server",
            "addons": ["ibm"],
            "service_level_agreement": "self-support",
            "usage_type": "dev",
        }

        self.assertEqual(
            system_purpose.ProcessSystemPurpose.process(ansible_result(input_data)),
            expected,
        )

    def test_invalid_json_case(self):
        """Invalid system purpose json."""
        input_data = """
                "_version": "1",
                "role": "server",
                "addons": [
                    "ibm"
                ],
                "service_level_agreement": "self-support",
                "usage_type": "dev"
            }
            """

        expected = None

        self.assertEqual(
            system_purpose.ProcessSystemPurpose.process(ansible_result(input_data)),
            expected,
        )
