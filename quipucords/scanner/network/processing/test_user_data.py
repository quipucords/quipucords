"""Unit tests for processing the user_data role."""

import unittest

from scanner.network.processing import user_data
from scanner.network.processing.util_for_test import ansible_result


class TestProcessSystemUserCount(unittest.TestCase):
    """Test ProcessSystemUserCount."""

    def test_success_case(self):
        """Processed result of system_user_count."""
        dependencies = {
            "internal_system_user_count": ansible_result(
                "root:x:0:0:root:/root:/bin/bash\nb\nc"
            )
        }
        assert (
            user_data.ProcessSystemUserCount.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            )
            == 1
        )
        # stdout_lines looks like ['', 'b']
        dependencies["internal_system_user_count"] = ansible_result(
            "\ntestuser:x:502:502::/home/testuser:/bin/bash\n"
            "sysuser:x:32:32:system user:/:/sbin/nologin"
        )
        assert (
            user_data.ProcessSystemUserCount.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            )
            == 1
        )
        dependencies["internal_system_user_count"] = ansible_result("Failed", 1)
        assert (
            user_data.ProcessSystemUserCount.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            )
            == ""
        )

    def test_not_found(self):
        """No result for the system_user_count fact."""
        dependencies = {}
        assert (
            user_data.ProcessSystemUserCount.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            )
            == ""
        )


class TestProcessUserLoginHistory(unittest.TestCase):
    """Test ProcessUserLoginHistory."""

    def test_success_case(self):
        """Found user login history fact."""
        dependencies = {"internal_user_login_history": ansible_result("a\nb\nc")}
        assert user_data.ProcessUserLoginHistory.process(
            "QPC_FORCE_POST_PROCESS", dependencies
        ) == ["a", "b", "c"]
        # stdout_lines looks like ['', 'b']
        dependencies["internal_user_login_history"] = ansible_result("\nb\n")
        assert user_data.ProcessUserLoginHistory.process(
            "QPC_FORCE_POST_PROCESS", dependencies
        ) == ["b"]
        dependencies["internal_user_login_history"] = ansible_result("Failed", 1)
        assert (
            user_data.ProcessUserLoginHistory.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            )
            == ""
        )

    def test_not_found(self):
        """Did not find user login history."""
        dependencies = {}
        assert (
            user_data.ProcessUserLoginHistory.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            )
            == ""
        )
