"""Unit tests for initial processing of cpu facts."""

import unittest

from scanner.network.processing import cpu, process
from tests.scanner.network.processing.util_for_test import ansible_result


class TestProcessCpuModelVer(unittest.TestCase):
    """Test ProcessCpuModelVer."""

    def test_success_case(self):
        """Found cpu model ver."""
        self.assertEqual(cpu.ProcessCpuModelVer.process(ansible_result("a\nb\nc")), "c")

    def test_not_found(self):
        """Did not find cpu model ver."""
        self.assertEqual(
            cpu.ProcessCpuModelVer.process(ansible_result("")), process.NO_DATA
        )


class TestProcessCpuCpuFamily(unittest.TestCase):
    """Test ProcessCpuCpuFamily."""

    def test_success_case(self):
        """Found cpu family."""
        self.assertEqual(
            cpu.ProcessCpuCpuFamily.process(ansible_result("a\nb\nc")), "c"
        )

    def test__not_found(self):
        """Did not find cpu family."""
        self.assertEqual(
            cpu.ProcessCpuCpuFamily.process(ansible_result("")), process.NO_DATA
        )


class TestProcessCpuVendorId(unittest.TestCase):
    """Test ProcessCpuVendorId."""

    def test_success_case(self):
        """Found cpu vendor id."""
        self.assertEqual(cpu.ProcessCpuVendorId.process(ansible_result("a\nb\nc")), "c")

    def test__not_found(self):
        """Did not find cpu vendor id."""
        self.assertEqual(
            cpu.ProcessCpuVendorId.process(ansible_result("")), process.NO_DATA
        )


class TestProcessCpuModelName(unittest.TestCase):
    """Test ProcessCpuModelName."""

    def test_success_case(self):
        """Found cpu model name."""
        self.assertEqual(
            cpu.ProcessCpuModelName.process(ansible_result("a\nb\nc")), "c"
        )

    def test__not_found(self):
        """Did not find cpu model name."""
        self.assertEqual(
            cpu.ProcessCpuModelName.process(ansible_result("")), process.NO_DATA
        )


class TestProcessCpuBogomips(unittest.TestCase):
    """Test ProcessCpuBogomips."""

    def test_success_case(self):
        """Found cpu bogomips."""
        self.assertEqual(cpu.ProcessCpuBogomips.process(ansible_result("a\nb\nc")), "c")

    def test__not_found(self):
        """Did not find cpu bogomips."""
        self.assertEqual(
            cpu.ProcessCpuBogomips.process(ansible_result("")), process.NO_DATA
        )


class TestProcessCpuSocketCount(unittest.TestCase):
    """Test ProcessCpuSocketCount."""

    def test_success_case_dmiresult(self):
        """Test socket count when internal dmi cmd returns valid result."""
        one_dmi_result = (
            "\tSocket Designation: CPU #000\r\n\t"
            "Status: Populated, Enabled\r\n "
            "\tSocket Designation: CPU #001\r\n\t"
            "Status: Unpopulated\r\n"
        )
        dependencies = {"internal_cpu_socket_count_dmi": ansible_result(one_dmi_result)}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 1
        )

    def test_dmiresult_contains_no_enabled_sockets(self):
        """Test that we use cpuinfo cmd if dmi cmd finds 0 sockets."""
        no_dmi_result = (
            "\tSocket Designation: CPU #000\r\n\t"
            "Status: Unpopulated\r\n "
            "\tSocket Designation: CPU #001\r\n\t"
            "Status: Unpopulated\r\n"
        )
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result(no_dmi_result),
            "internal_cpu_socket_count_cpuinfo": ansible_result("2"),
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 2
        )

    def test_dmiresult_contains_nonint_characters(self):
        """Test that we use cpuinfo cmd if dmi cmd can't be changed to int."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("Permission Denied."),
            "internal_cpu_socket_count_cpuinfo": ansible_result("2"),
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 2
        )

    def test_dmiresult_cpuinfo_fails(self):
        """Test that we use cpu count when dmi and cpuinfo cmds fail."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("Permission Denied."),
            "internal_cpu_socket_count_cpuinfo": ansible_result(""),
            "cpu_count": "4",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 4
        )

    def test_dmiresult_cpuinfo_not_in_dependencies(self):
        """Test that we use cpu count when the dependencies are None."""
        dependencies = {"cpu_count": "4"}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 4
        )

    def test_dmiresult_cpuinfo_failed_tasks(self):
        """Test the sc is the same as cpu count when the deps raise errors."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("Failed", 1),
            "internal_cpu_socket_count_cpuinfo": ansible_result("Failed", 1),
            "cpu_count": "4",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 4
        )

    def test_cpuinfo_failed_value_error(self):
        """Test that cpu count is used when other deps rasie value errors."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("Permission Denied."),
            "internal_cpu_socket_count_cpuinfo": ansible_result("Failure"),
            "cpu_count": "1",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 1
        )

    def test_cpuinfo_failed_return_none(self):
        """Test that none is returned if everything else fails."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("Permission Denied."),
            "internal_cpu_socket_count_cpuinfo": ansible_result("Failure"),
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies),
            None,
        )

    def test_dmiresult_greater_than_8(self):
        """Test that cpu count is used when other deps greater than 8."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("9"),
            "internal_cpu_socket_count_cpuinfo": ansible_result("9"),
            "cpu_count": "3",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 3
        )

    def test_dmiresult_equal_to_8(self):
        """Test that socket count is set to dmicode dep when equal to 8."""
        eight_dmi_result = (
            "\tSocket Designation: CPU #000\r\n\t"
            "Status: Populated, Enabled\r\n "
            "\tSocket Designation: CPU #001\r\n\t"
            "Status: Populated, Enabled\r\n "
            "\tSocket Designation: CPU #002\r\n\t"
            "Status: Populated, Enabled\r\n"
            "\tSocket Designation: CPU #003\r\n\t"
            "Status: Populated, Disabled\r\n"
            "\tSocket Designation: CPU #004\r\n\t"
            "Status: Populated, Enabled\r\n"
            "\tSocket Designation: CPU #005\r\n\t"
            "Status: Populated, Disabled\r\n"
            "\tSocket Designation: CPU #006\r\n\t"
            "Status: Populated, Enabled\r\n"
            "\tSocket Designation: CPU #007\r\n\t"
            "Status: Populated, Enabled\r\n"
        )
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result(eight_dmi_result),
            "internal_cpu_socket_count_cpuinfo": ansible_result("9"),
            "cpu_count": "3",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 8
        )

    def test_cpuinfo_equal_to_8(self):
        """Test that socket count is set to cpuinfo dep when equal to 8."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("10"),
            "internal_cpu_socket_count_cpuinfo": ansible_result("8"),
            "cpu_count": "3",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies), 8
        )

    def test_cpu_count_greater_than_8(self):
        """Test that the sc is set to cpuinfo even if greater thatn 8."""
        dependencies = {
            "internal_cpu_socket_count_dmi": ansible_result("10"),
            "internal_cpu_socket_count_cpuinfo": ansible_result("9"),
            "cpu_count": "12",
        }
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process("QPC_FORCE_POST_PROCESS", dependencies),
            12,
        )


class TestProcessCpuCoreCount(unittest.TestCase):
    """Test ProcessCpuCoreCount."""

    def test_core_count_success(self):
        """Test the cc when virt_type is None and cpu per socket is defined."""
        dependencies = {"cpu_core_per_socket": 2, "cpu_socket_count": 2}
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process("QPC_FORCE_POST_PROCESS", dependencies), 4
        )

    def test_core_count_success_with_virt_type(self):
        """Test the core count when virt_type is vmware."""
        dependencies = {
            "cpu_core_per_socket": 2,
            "cpu_socket_count": 2,
            "cpu_count": 3,
            "virt_type": "vmware",
        }
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process("QPC_FORCE_POST_PROCESS", dependencies), 3
        )

    def test_core_count_success_with_hyperthreading(self):
        """Test the core count when there is hyperthreading."""
        dependencies = {
            "cpu_socket_count": 2,
            "cpu_count": 3,
            "cpu_hyperthreading": True,
        }
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process("QPC_FORCE_POST_PROCESS", dependencies), 1.5
        )

    def test_core_count_success_without_hyperthreading(self):
        """Test the core count when there is not hyperthreading."""
        dependencies = {
            "cpu_socket_count": 2,
            "cpu_count": 3,
            "cpu_hyperthreading": False,
        }
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process("QPC_FORCE_POST_PROCESS", dependencies), 3
        )

    def test_core_count_return_empty_string(self):
        """Test the core count is set to '' when deps not available."""
        dependencies = {}
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process("QPC_FORCE_POST_PROCESS", dependencies),
            None,
        )
