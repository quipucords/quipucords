# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of cpu facts."""


import unittest

from scanner.network.processing import cpu, process
from scanner.network.processing.util_for_test import ansible_result


class TestProcessCpuModelVer(unittest.TestCase):
    """Test ProcessCpuModelVer."""

    def test_success_case(self):
        """Found cpu model ver."""
        self.assertEqual(
            cpu.ProcessCpuModelVer.process(
                ansible_result('a\nb\nc')),
            'a')

    def test_not_found(self):
        """Did not find cpu model ver."""
        self.assertEqual(
            cpu.ProcessCpuModelVer.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuCpuFamily(unittest.TestCase):
    """Test ProcessCpuCpuFamily."""

    def test_success_case(self):
        """Found cpu family."""
        self.assertEqual(
            cpu.ProcessCpuCpuFamily.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu family."""
        self.assertEqual(
            cpu.ProcessCpuCpuFamily.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuVendorId(unittest.TestCase):
    """Test ProcessCpuVendorId."""

    def test_success_case(self):
        """Found cpu vendor id."""
        self.assertEqual(
            cpu.ProcessCpuVendorId.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu vendor id."""
        self.assertEqual(
            cpu.ProcessCpuVendorId.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuModelName(unittest.TestCase):
    """Test ProcessCpuModelName."""

    def test_success_case(self):
        """Found cpu model name."""
        self.assertEqual(
            cpu.ProcessCpuModelName.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu model name."""
        self.assertEqual(
            cpu.ProcessCpuModelName.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuBogomips(unittest.TestCase):
    """Test ProcessCpuBogomips."""

    def test_success_case(self):
        """Found cpu bogomips."""
        self.assertEqual(
            cpu.ProcessCpuBogomips.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu bogomips."""
        self.assertEqual(
            cpu.ProcessCpuBogomips.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuSocketCount(unittest.TestCase):
    """Test ProcessCpuSocketCount."""

    def test_success_case_dmiresult(self):
        """Test socket count when internal dmi cmd returns valid result."""
        dependencies = {'internal_cpu_socket_count_dmi_cmd':
                        ansible_result('5')}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '5')

    def test_dmiresult_contains_nonint_characters(self):
        """Test that we use cpuinfo cmd if dmi cmd can't be changed to int."""
        dependencies = {'internal_cpu_socket_count_dmi_cmd':
                        ansible_result('Permission Denied.'),
                        'internal_cpu_socket_count_cpuinfo_cmd':
                        ansible_result('2')}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '2')

    def test_dmiresult_cpuinfo_fails(self):
        """Test that we use cpu count when dmi and cpuinfo cmds fail."""
        dependencies = {'internal_cpu_socket_count_dmi_cmd':
                        ansible_result('Permission Denied.'),
                        'internal_cpu_socket_count_cpuinfo_cmd':
                        ansible_result(''),
                        'cpu_count': '4'}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '4')

    def test_dmiresult_cpuinfo_not_in_dependencies(self):
        """Test that we use cpu count when the dependencies are None."""
        dependencies = {'cpu_count': '4'}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '4')

    def test_dmiresult_cpuinfo_failed_tasks(self):
        """Test the sc is the same as cpu count when the deps raise errors."""
        dependencies = {'internal_cpu_socket_count_dmi_cmd':
                        ansible_result('Failed', 1),
                        'internal_cpu_socket_count_cpuinfo_cmd':
                        ansible_result('Failed', 1),
                        'cpu_count': '4'}
        self.assertEqual(
            cpu.ProcessCpuSocketCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '4')


class TestProcessCpuCoreCount(unittest.TestCase):
    """Test ProcessCpuCoreCount."""

    def test_core_count_success(self):
        """Test the cc when virt_type is None and cpu per socket is defined."""
        dependencies = {'cpu_core_per_socket': 2,
                        'cpu_socket_count': 2}
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            4)

    def test_core_count_success_with_virt_type(self):
        """Test the core count when virt_type is vmware."""
        dependencies = {'cpu_core_per_socket': 2,
                        'cpu_socket_count': 2,
                        'cpu_count': 3,
                        'virt_type': 'vmware'}
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            3)

    def test_core_count_success_with_hyperthreading(self):
        """Test the core count when there is hyperthreading."""
        dependencies = {'cpu_socket_count': 2,
                        'cpu_count': 3,
                        'cpu_hyperthreading': True}
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            1.5)

    def test_core_count_success_without_hyperthreading(self):
        """Test the core count when there is not hyperthreading."""
        dependencies = {'cpu_socket_count': 2,
                        'cpu_count': 3,
                        'cpu_hyperthreading': False}
        self.assertEqual(
            cpu.ProcessCpuCoreCount.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            3)
