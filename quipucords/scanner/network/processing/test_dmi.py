# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of dmi facts."""


import unittest

from scanner.network.processing import dmi
from scanner.network.processing.util_for_test import ansible_result


class TestProcessDmiSystemUuidr(unittest.TestCase):
    """Test ProcessDmiSystemUuid."""

    def test_success_case(self):
        """Test multiple dmi_system_uuid values."""
        # stdout_lines looks like ['a', 'b', 'c']
        dependencies = {"internal_dmi_system_uuid": ansible_result("a\nb\nc")}
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies),
            "a",
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
        # stdout_lines looks like ['a', 'b', 'c']
        dependencies = {"internal_dmi_system_uuid": ansible_result(f"{'a' * 37}\nb\nc")}
        self.assertEqual(
            dmi.ProcessDmiSystemUuid.process("QPC_FORCE_POST_PROCESS", dependencies), ""
        )
        # stdout_lines looks like ['', 'b']
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
