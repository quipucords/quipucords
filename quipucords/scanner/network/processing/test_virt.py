# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of virt facts."""


import unittest

from scanner.network.processing import process, virt
from scanner.network.processing.util_for_test import ansible_result


class TestProcessVirtXenPrivcmdFound(unittest.TestCase):
    """Test ProcessVirtXenPrivcmdFound."""

    def test_success_case(self):
        """Found internal_xen_privcmd_found fact."""
        self.assertEqual(
            virt.ProcessVirtXenPrivcmdFound.process(ansible_result("Y\r\n"), {}), True
        )
        self.assertEqual(
            virt.ProcessVirtXenPrivcmdFound.process(ansible_result("N\r\n"), {}), False
        )

    def test_sudo_case(self):
        """Sudo found internal_xen_privcmd_found fact."""
        self.assertEqual(
            virt.ProcessVirtXenPrivcmdFound.process(ansible_result("\r\nY\r\n"), {}),
            True,
        )
        self.assertEqual(
            virt.ProcessVirtXenPrivcmdFound.process(ansible_result("\r\nN\r\n"), {}),
            False,
        )

    def test_not_found(self):
        """Did not find internal_xen_privcmd_found fact."""
        self.assertEqual(
            virt.ProcessVirtXenPrivcmdFound.process(ansible_result(""), {}), False
        )


class TestProcessVirtKvmFound(unittest.TestCase):
    """Test ProcessVirtKvmFound."""

    def test_success_case(self):
        """Found internal_kvm_found fact."""
        self.assertEqual(
            virt.ProcessVirtKvmFound.process(ansible_result("Y\r\n"), {}), True
        )
        self.assertEqual(
            virt.ProcessVirtKvmFound.process(ansible_result("N\r\n"), {}), False
        )

    def test_sudo_case(self):
        """Sudo found internal_kvm_found fact."""
        self.assertEqual(
            virt.ProcessVirtKvmFound.process(ansible_result("\r\nY\r\n"), {}), True
        )
        self.assertEqual(
            virt.ProcessVirtKvmFound.process(ansible_result("\r\nN\r\n"), {}), False
        )

    def test_not_found(self):
        """Did not find internal_kvm_found fact."""
        self.assertEqual(
            virt.ProcessVirtKvmFound.process(ansible_result(""), {}), False
        )


class TestProcessVirtXenGuest(unittest.TestCase):
    """Test ProcessVirtXenGuest."""

    def test_success_case(self):
        """Found internal_xen_guest fact."""
        self.assertEqual(
            virt.ProcessVirtXenGuest.process(ansible_result("1\r\n"), {}), True
        )
        self.assertEqual(
            virt.ProcessVirtXenGuest.process(ansible_result("0\r\n"), {}), False
        )

    def test_sudo_case(self):
        """Sudo found internal_xen_guest fact."""
        self.assertEqual(
            virt.ProcessVirtXenGuest.process(ansible_result("\r\n1\r\n"), {}), True
        )
        self.assertEqual(
            virt.ProcessVirtXenGuest.process(ansible_result("\r\n0\r\n"), {}), False
        )

    def test_not_found(self):
        """Did not find internal_xen_guest fact."""
        self.assertEqual(
            virt.ProcessVirtXenGuest.process(ansible_result(""), {}), False
        )


class TestProcessSystemManufacturer(unittest.TestCase):
    """Test ProcessSystemManufacturer."""

    def test_success_case(self):
        """Found internal_sys_manufacturer fact."""
        self.assertEqual(
            virt.ProcessSystemManufacturer.process(
                ansible_result("FooVmWareBar\r\n"), {}
            ),
            "FooVmWareBar",
        )

    def test_sudo_case(self):
        """Sudo found internal_sys_manufacturer fact."""
        self.assertEqual(
            virt.ProcessSystemManufacturer.process(
                ansible_result("\r\nFooVmWareBar\r\n"), {}
            ),
            "FooVmWareBar",
        )

    def test_not_found(self):
        """Did not find internal_sys_manufacturer fact."""
        self.assertEqual(
            virt.ProcessSystemManufacturer.process(ansible_result(""), {}), None
        )


class TestProcessVirtCpuModelNameKvm(unittest.TestCase):
    """Test ProcessVirtCpuModelNameKvm."""

    def test_success_case(self):
        """Found internal_cpu_model_name_kvm fact."""
        self.assertEqual(
            virt.ProcessVirtCpuModelNameKvm.process(ansible_result("Y\r\n"), {}), True
        )
        self.assertEqual(
            virt.ProcessVirtCpuModelNameKvm.process(ansible_result("N\r\n"), {}), False
        )

    def test_sudo_case(self):
        """Sudo found internal_cpu_model_name_kvm fact."""
        self.assertEqual(
            virt.ProcessVirtCpuModelNameKvm.process(ansible_result("\r\nY\r\n"), {}),
            True,
        )
        self.assertEqual(
            virt.ProcessVirtCpuModelNameKvm.process(ansible_result("\r\nN\r\n"), {}),
            False,
        )

    def test_not_found(self):
        """Did not find internal_cpu_model_name_kvm fact."""
        self.assertEqual(
            virt.ProcessVirtCpuModelNameKvm.process(ansible_result(""), {}), False
        )


class TestProcessVirtType(unittest.TestCase):
    """Test ProcessVirtType."""

    def test_dmidecode_vmware_case(self):
        """Found virt_type dmidecode vmware fact."""
        dependencies = {
            "internal_have_dmidecode": True,
            "internal_sys_manufacturer": "FooVmWaReBar",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": False,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_VMWARE,
        )

    def test_dmidecode_virtualbox_case(self):
        """Found virt_type dmidecode virtualbox fact."""
        dependencies = {
            "internal_have_dmidecode": True,
            "internal_sys_manufacturer": "hi innotek gMBh there",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": False,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_VIRTUALBOX,
        )

    def test_dmidecode_virtualpc_case(self):
        """Found virt_type dmidecode virtualpc fact."""
        dependencies = {
            "internal_have_dmidecode": True,
            "internal_sys_manufacturer": "hi microSOFT there",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": False,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_VIRTUALPC,
        )

    def test_dmidecode_kvm_case(self):
        """Found virt_type dmidecode kvm fact."""
        dependencies = {
            "internal_have_dmidecode": True,
            "internal_sys_manufacturer": "hi QeMU there",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": False,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_KVM,
        )

    def test_dmidecode_no_manu_case(self):
        """Found virt_type dmidecode no manufacturer fact."""
        dependencies = {
            "internal_have_dmidecode": True,
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": False,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            None,
        )

    def test_kvm_command_kvm_case(self):
        """Found virt_type kvm_command kvm fact."""
        dependencies = {
            "internal_have_dmidecode": False,
            "internal_sys_manufacturer": "hi there",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": False,
            "internal_kvm_found": True,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_KVM,
        )

    def test_cpu_model_name_kvm_case(self):
        """Found virt_type cpu_model_name kvm fact."""
        dependencies = {
            "internal_have_dmidecode": False,
            "internal_sys_manufacturer": "hi there",
            "internal_cpu_model_name_kvm": True,
            "internal_xen_guest": False,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_KVM,
        )

    def test_xen_guest_case(self):
        """Found virt_type xen guest fact."""
        dependencies = {
            "internal_have_dmidecode": False,
            "internal_sys_manufacturer": "hi there",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": True,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_XEN,
        )

    def test_xen_command_case(self):
        """Found virt_type xen command fact."""
        dependencies = {
            "internal_have_dmidecode": False,
            "internal_sys_manufacturer": "hi there",
            "internal_cpu_model_name_kvm": False,
            "internal_xen_guest": True,
            "internal_kvm_found": False,
            "internal_xen_privcmd_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtType.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            virt.VIRT_TYPE_XEN,
        )

    def test_not_found(self):
        """Did not find virt_type fact."""
        self.assertEqual(virt.ProcessVirtType.process(ansible_result(""), {}), None)


class TestProcessVirtVirt(unittest.TestCase):
    """Test ProcessVirtVirt."""

    # pylint: disable=invalid-name
    def test_virt_virt_with_virt_type_case(self):
        """Found virt_virt using virt_type fact."""
        dependencies = {
            "virt_type": virt.VIRT_TYPE_VIRTUALBOX,
            "internal_kvm_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtVirt.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            "virt-guest",
        )

    def test_virt_virt_with_kvm_case(self):
        """Found virt_virt using virt_type fact."""
        dependencies = {
            "virt_type": virt.VIRT_TYPE_VIRTUALBOX,
            "internal_kvm_found": True,
        }
        self.assertEqual(
            virt.ProcessVirtVirt.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            "virt-host",
        )

    def test_virt_virt_with_deps_case(self):
        """Found virt_virt using virt_type fact."""
        dependencies = {
            "virt_type": None,
            "internal_kvm_found": False,
        }
        self.assertEqual(
            virt.ProcessVirtVirt.process(
                ansible_result(process.QPC_FORCE_POST_PROCESS), dependencies
            ),
            None,
        )
