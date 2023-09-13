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

    def test_unexpected_stout_lines_before_actual_json(self):
        """Test handling unexpected lines in stdout before the actual JSON."""
        input_data = """
            Nobody expects the Spanish Inquisition.
            Have at thee!
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
