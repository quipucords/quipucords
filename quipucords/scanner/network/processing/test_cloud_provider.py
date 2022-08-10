# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of cloud provider facts."""


import unittest

from scanner.network.processing import cloud_provider
from scanner.network.processing.util_for_test import ansible_result


class TestProcessDmiChassisAssetTag(unittest.TestCase):
    """Test ProcessDmiChassisAssetTag."""

    def test_success_case(self):
        """Found dmi chassis asset tag."""
        dependencies = {"internal_dmi_chassis_asset_tag": ansible_result("a\nb\nc")}
        self.assertEqual(
            cloud_provider.ProcessDmiChassisAssetTag.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "a",
        )
        # stdout_lines looks like ['', 'b']
        dependencies["internal_dmi_chassis_asset_tag"] = ansible_result("\nb\n")
        self.assertEqual(
            cloud_provider.ProcessDmiChassisAssetTag.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "b",
        )
        dependencies["internal_dmi_chassis_asset_tag"] = ansible_result("Failed", 1)
        self.assertEqual(
            cloud_provider.ProcessDmiChassisAssetTag.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )

    def test_not_found(self):
        """Did not find dmi chassis asset tag."""
        dependencies = {}
        self.assertEqual(
            cloud_provider.ProcessDmiChassisAssetTag.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )


class TestProcessDmiSystemProductName(unittest.TestCase):
    """Test ProcessDmiSystemProductName."""

    def test_success_case(self):
        """Found dmi system product name."""
        dependencies = {"internal_dmi_system_product_name": ansible_result("a\nb\nc")}
        self.assertEqual(
            cloud_provider.ProcessDmiSystemProductName.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "a",
        )
        # stdout_lines looks like ['', 'b']
        dependencies["internal_dmi_system_product_name"] = ansible_result("\nb\n")
        self.assertEqual(
            cloud_provider.ProcessDmiSystemProductName.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "b",
        )
        dependencies["internal_dmi_system_product_name"] = ansible_result("Failed", 1)
        self.assertEqual(
            cloud_provider.ProcessDmiSystemProductName.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )

    def test_not_found(self):
        """Did not find dmi system product name."""
        dependencies = {}
        self.assertEqual(
            cloud_provider.ProcessDmiSystemProductName.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )


class TestProcessCloudProvider(unittest.TestCase):
    """Test ProcessCloudProvider."""

    def test_success_case(self):
        """Found cpu model ver."""
        dependencies = {"dmi_bios_version": "3.4.3.amazon"}
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            cloud_provider.AMAZON,
        )
        dependencies["dmi_bios_version"] = "6.0"
        dependencies[
            "dmi_chassis_asset_tag"
        ] = "Asset Tag: 7783-7084-3265-9085-8269-3286-77"
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            cloud_provider.AZURE,
        )
        dependencies["dmi_bios_version"] = "Google, 1.2.6"
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            cloud_provider.GOOGLE,
        )
        dependencies["dmi_bios_version"] = "6.0"
        dependencies["dmi_system_manufacturer"] = "Alibaba Cloud"
        dependencies["dmi_chassis_asset_tag"] = "Asset Tag: No Asset Tag"
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            cloud_provider.ALIBABA,
        )
        dependencies["dmi_system_manufacturer"] = "empty"
        dependencies["dmi_system_product_name"] = "	Alibaba Cloud ECS"
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            cloud_provider.ALIBABA,
        )

    def test_not_found(self):
        """Did not find any dmi facts to compute the cloud provider."""
        # no deps
        dependencies = {}
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )
        # deps indicate no cloud provider
        dependencies["dmi_bios_version"] = "6.0"
        dependencies["dmi_chassis_asset_tag"] = "Asset Tag: No Asset Tag"
        dependencies[
            "dmi_system_product_name"
        ] = "Product Name: VMware Virtual Platform"
        dependencies["dmi_system_manufacturer"] = "VMWare, Inc."
        self.assertEqual(
            cloud_provider.ProcessCloudProvider.process(
                "QPC_FORCE_POST_PROCESS", dependencies
            ),
            "",
        )
