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

        assert (
            system_purpose.ProcessSystemPurpose.process(ansible_result(input_data))
            == expected
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

        assert (
            system_purpose.ProcessSystemPurpose.process(ansible_result(input_data))
            == expected
        )
