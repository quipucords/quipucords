"""Unit tests for processing the user_data role."""

import unittest

from scanner.network.processing import user_data
from tests.scanner.network.processing.util_for_test import ansible_result


class TestProcessSystemUserCount(unittest.TestCase):
    """Test ProcessSystemUserCount."""

    def test_success_case(self):
        """Processed result of system_user_count."""
        dependencies = {
            "internal_system_user_count": ansible_result(
                "root:x:0:0:root:/root:/bin/bash\nb\nc"
            )
        }
        self.assertEqual(
            user_data.ProcessSystemUserCount.process(
                "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
            ),
            1,
        )
        # stdout_lines looks like ['', 'b']
        dependencies["internal_system_user_count"] = ansible_result(
            "\ntestuser:x:502:502::/home/testuser:/bin/bash\n"
            "sysuser:x:32:32:system user:/:/sbin/nologin"
        )
        self.assertEqual(
            user_data.ProcessSystemUserCount.process(
                "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
            ),
            1,
        )
        dependencies["internal_system_user_count"] = ansible_result("Failed", 1)
        self.assertEqual(
            user_data.ProcessSystemUserCount.process(
                "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )

    def test_not_found(self):
        """No result for the system_user_count fact."""
        dependencies = {}
        self.assertEqual(
            user_data.ProcessSystemUserCount.process(
                "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )
