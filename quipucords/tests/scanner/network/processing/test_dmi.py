"""Unit tests for initial processing of dmi facts."""

import unittest

from scanner.network.processing import dmi
from scanner.network.processing.util_for_test import ansible_result


class TestProcessDmiSystemUuidr(unittest.TestCase):
    """Test ProcessDmiSystemUuid."""

    def test_success_case(self):
        """
        Test multiple dmi_system_uuid values.

        Please note that the way we handle multiple results may be unintuitive. If
        Ansible's output includes multiple lines which may mean multiple UUIDs,
        we always return only one of them: the content from the last line.
        """
        # stdout_lines looks like ['a', 'b', 'c']
        dependencies = {"internal_dmi_system_uuid": ansible_result("a\nb\nc")}
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies),
            "c",
        )
        # stdout_lines looks like ['', 'b']
        dependencies["internal_dmi_system_uuid"] = ansible_result("\nb\n")
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies),
            "b",
        )
        dependencies["internal_dmi_system_uuid"] = ansible_result("Failed", 1)
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies), ""
        )

    def test_invalid_uuid_case(self):
        """Test dmi_system_uuid too long."""
        # stdout_lines looks like ['a', 'b', 'ccccccccccccccccccccccccccccccccccccc']
        dependencies = {"internal_dmi_system_uuid": ansible_result(f"a\nb\n{'c' * 37}")}
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies),
            "b",
        )
        # stdout_lines looks like ['', 'b', '']
        dependencies["internal_dmi_system_uuid"] = ansible_result(f"\n{'b' * 37}\n")
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies), ""
        )

    def test_not_found(self):
        """Did not find dmi system uuid."""
        dependencies = {}
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies), ""
        )
