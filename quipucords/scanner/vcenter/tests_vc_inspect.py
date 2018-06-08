#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the vcenter inspect capabilities."""

import json
from multiprocessing import Value
from unittest.mock import ANY, Mock, patch

from api.models import (Credential,
                        ScanJob,
                        ScanTask,
                        Source,
                        SystemInspectionResult)

from django.test import TestCase

from pyVmomi import vim  # pylint: disable=no-name-in-module

from scanner.test_util import create_scan_job
from scanner.vcenter.inspect import (InspectTaskRunner, get_nics)


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


# pylint: disable=too-many-instance-attributes
class InspectTaskRunnerTest(TestCase):
    """Tests against the InspectTaskRunner class and functions."""

    runner = None

    def setUp(self):
        """Create test case setup."""
        cred = Credential(
            name='cred1',
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        cred.save()

        source = Source(
            name='source1',
            port=22,
            hosts='["1.2.3.4"]')

        source.save()
        source.credentials.add(cred)

        self.scan_job, self.scan_task = create_scan_job(
            source, ScanTask.SCAN_TYPE_INSPECT)

        self.connect_scan_task = self.scan_task.prerequisites.first()
        self.connect_scan_task.update_stats('TEST_VC.', sys_count=5)
        self.connect_scan_task.complete()

        # Create task runner
        self.runner = InspectTaskRunner(scan_job=self.scan_job,
                                        scan_task=self.scan_task)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_get_nics(self):
        """Test the get_nics method."""
        guest = Mock()
        nics = []
        for k in range(0, 2):
            nic = Mock()
            network = Mock()
            nic.network = network
            nic.macAddress = 'mac' + str(k)
            ip_config = Mock()
            ip_addr = Mock()
            ip_addr.ipAddress = 'ip' + str(k)
            addresses = [ip_addr]
            ip_config.ipAddress = addresses
            nic.ipConfig = ip_config
            nics.append(nic)
        guest.net = nics
        mac_addresses, ip_addresses = get_nics(guest)
        self.assertEqual(mac_addresses, ['mac0', 'mac1'])
        self.assertEqual(ip_addresses, ['ip0', 'ip1'])

    def test__none(self):
        """Test get result method when no results exist."""
        results = self.scan_task.get_result().systems.first()
        self.assertEqual(results, None)

    def test_get_result(self):
        """Test get results method when results exist."""
        results = self.scan_task.get_result()
        self.assertEqual(results, self.scan_task.inspection_result)

    # pylint: disable=too-many-locals
    def test_get_vm_info(self):
        """Test the get vm info method."""
        data_center = 'dc1'
        cluster = 'cluster1'
        host = Mock()
        host_sum = Mock()
        host_config = Mock()
        host_config.name = 'host1'
        host_sum.config = host_config
        host_hard = Mock()
        host_hard.numCpuCores = 12
        host_hard.numCpuThreads = 24
        host_sum.hardware = host_hard
        host.summary = host_sum
        virtual_machine = Mock()
        summary = Mock()
        config = Mock()
        runtime = Mock()
        sum_guest = Mock()
        config.name = 'vm1'
        config.uuid = '1111'
        config.memorySizeMB = 1024
        config.numCpu = 2
        config.guestFullName = 'Red Hat 7'
        runtime.powerState = 'powerOn'
        sum_guest.hostName = 'hostname'
        summary.config = config
        summary.runtime = runtime
        summary.guest = sum_guest

        virtual_machine.summary = summary
        self.scan_task.update_stats(
            'TEST_VC.',
            sys_count=5,
            sys_failed=0,
            sys_scanned=0,
            sys_unreachable=0)
        getnics = (['00:50:56:9e:09:8c'], ['1.2.3.4'])
        with patch('scanner.vcenter.inspect.get_nics',
                   return_value=getnics):
            self.runner.get_vm_info(data_center, cluster,
                                    host, virtual_machine)

            inspect_result = self.scan_task.inspection_result
            sys_results = inspect_result.systems.all()
            expected_facts = {'vm.cluster': 'cluster1',
                              'vm.cpu_count': 2,
                              'vm.datacenter': 'dc1',
                              'vm.dns_name': 'hostname',
                              'vm.host.cpu_cores': 12,
                              'vm.host.cpu_count': 2,
                              'vm.host.cpu_threads': 24,
                              'vm.host.name': 'host1',
                              'vm.ip_addresses': ['1.2.3.4'],
                              'vm.mac_addresses': ['00:50:56:9e:09:8c'],
                              'vm.memory_size': 1,
                              'vm.name': 'vm1',
                              'vm.os': 'Red Hat 7',
                              'vm.state': 'powerOn',
                              'vm.uuid': '1111'}
            sys_fact = {}
            for raw_fact in sys_results.first().facts.all():
                # Must read as JSON as this is what task.py does
                sys_fact[raw_fact.name] = json.loads(raw_fact.value)

            self.assertEqual(1, len(sys_results))
            self.assertEqual('vm1', sys_results.first().name)
            self.assertEqual(expected_facts, sys_fact)

    # pylint: disable=too-many-locals
    def test_recurse_folder(self):
        """Test the recurse_folder method."""
        sys_result = SystemInspectionResult(
            name='vm1', status=SystemInspectionResult.SUCCESS)
        sys_result.save()

        child_entity = []
        for k in range(0, 2):
            child = Mock()
            child.name = 'dc' + str(k)
            child.__class__.__name__ = 'vim.Datacenter'
            host_folder = Mock()
            clusters = []
            for j in range(0, 1):
                cluster = Mock()
                cluster.name = 'cluster' + str(j)
                host = Mock()
                h_summary = Mock(name='h_summary')
                h_config = Mock(name='h_config')
                h_config.name = 'host1'
                h_summary.config = h_config
                host.summary = h_summary
                virtual_machine = Mock(name='vm')
                virtual_machine.summary.config.name = 'host1'
                host.vm = [virtual_machine]
                hosts = [host]
                cluster.host = hosts
                clusters.append(cluster)
            host_folder.childEntity = clusters
            child.hostFolder = host_folder
            child_entity.append(child)

        vcenter = Mock()
        content = Mock()
        empty_folder = Mock()
        empty_folder.__class__.__name__ = 'vim.Folder'
        empty_folder.name = 'empty_folder'
        empty_folder.childEntity = []

        invalid_folder = Mock()
        invalid_folder.__class__.__name__ = 'vim.Folder'
        invalid_folder.childEntity = None
        invalid_folder.name = 'invalid_folder'

        regular_folder = Mock()
        regular_folder.__class__.__name__ = 'vim.Folder'
        regular_folder.childEntity = child_entity
        regular_folder.name = 'regular_folder'

        folder_entries = [empty_folder, invalid_folder, regular_folder]

        root_folder = Mock()
        root_folder.childEntity = folder_entries
        content.rootFolder = root_folder
        vcenter.RetrieveContent = Mock(return_value=content)
        with patch.object(InspectTaskRunner,
                          'get_vm_info') as mock_get_vm_info:
            self.runner.recurse_folder(root_folder)
            mock_get_vm_info.assert_called_with(ANY, ANY, ANY, ANY)

    def test_inspect(self):
        """Test the inspect method."""
        with patch('scanner.vcenter.inspect.vcenter_connect',
                   return_value=Mock()) as mock_vcenter_connect:
            with patch.object(InspectTaskRunner,
                              'recurse_folder') as mock_recurse:
                self.runner.connect_scan_task = self.connect_scan_task
                self.runner.inspect()
                mock_vcenter_connect.assert_called_once_with(ANY)
                mock_recurse.assert_called_once_with(ANY)

    def test_failed_run(self):
        """Test the run method."""
        with patch.object(InspectTaskRunner, 'inspect',
                          side_effect=invalid_login) as mock_connect:
            status = self.runner.run(Value('i', ScanJob.JOB_RUN))
            self.assertEqual(ScanTask.FAILED, status[1])
            mock_connect.assert_called_once_with()

    def test_prereq_failed(self):
        """Test the run method."""
        self.connect_scan_task.status = ScanTask.FAILED
        self.connect_scan_task.save()
        status = self.runner.run(Value('i', ScanJob.JOB_RUN))
        self.assertEqual(ScanTask.FAILED, status[1])

    def test_run(self):
        """Test the run method."""
        with patch.object(InspectTaskRunner, 'inspect') as mock_connect:
            status = self.runner.run(Value('i', ScanJob.JOB_RUN))
            self.assertEqual(ScanTask.COMPLETED, status[1])
            mock_connect.assert_called_once_with()

    def test_cancel(self):
        """Test the cancel method."""
        status = self.runner.run(Value('i', ScanJob.JOB_TERMINATE_CANCEL))
        self.assertEqual(ScanTask.CANCELED, status[1])

    def test_pause(self):
        """Test the pause method."""
        status = self.runner.run(Value('i', ScanJob.JOB_TERMINATE_PAUSE))
        self.assertEqual(ScanTask.PAUSED, status[1])
