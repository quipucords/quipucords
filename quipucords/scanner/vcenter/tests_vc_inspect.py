#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the vcenter inspect capabilities."""

from unittest.mock import Mock, patch, ANY
from django.test import TestCase
from pyVmomi import vim  # pylint: disable=no-name-in-module
from api.models import (Credential, Source, HostRange, ScanTask,
                        ScanJob, InspectionResults, InspectionResult)
from scanner.vcenter.inspect import (InspectTaskRunner, get_nics, vmsummary)


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


# pylint: disable=too-many-instance-attributes
class InspectTaskRunnerTest(TestCase):
    """Tests against the InspectTaskRunner class and functions."""

    runner = None

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_INSPECT,
                                  source=self.source, sequence_number=2)
        self.scan_task.save()

        self.conn_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=1)
        self.conn_task.systems_count = 5
        self.conn_task.status = ScanTask.COMPLETED
        self.conn_task.save()
        self.scan_task.prerequisites.add(self.conn_task)
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.inspect_results = InspectionResults(scan_job=self.scan_job)
        self.inspect_results.save()
        self.runner = InspectTaskRunner(scan_job=self.scan_job,
                                        scan_task=self.scan_task,
                                        inspect_results=self.inspect_results)

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

    def test_vmsummary(self):
        """Test the vmsummary method."""
        summary = Mock()
        guest = Mock()
        config = Mock()
        runtime = Mock()
        sum_guest = Mock()
        config.uuid = '1111'
        config.memorySizeMB = 1024
        config.numCpu = 2
        config.guestFullName = 'Red Hat 7'
        runtime.powerState = 'powerOn'
        sum_guest.hostName = 'hostname'
        summary.config = config
        summary.runtime = runtime
        summary.guest = sum_guest
        with patch('scanner.vcenter.inspect.get_nics',
                   return_value=(['mac1'], ['ip1'])) as mock_get_nics:
            expected = {'cpu': '2',
                        'hostname': 'hostname',
                        'ip_address': 'ip1',
                        'mac': 'mac1',
                        'mem': '1.0',
                        'ostype': 'Red Hat 7',
                        'state': 'powerOn',
                        'uuid': '1111'}
            vm_summary = vmsummary(summary, guest)
            mock_get_nics.assert_called_once_with(ANY)
            self.assertEqual(vm_summary, expected)

    def test_get_results_none(self):
        """Test get results method when no results exist."""
        results = self.runner.get_results()
        self.assertEqual(results, None)

    def test_get_results(self):
        """Test get results method when results exist."""
        inspect_result = InspectionResult(source=self.source,
                                          scan_task=self.scan_task)
        inspect_result.save()
        self.inspect_results.results.add(inspect_result)
        self.inspect_results.save()
        results = self.runner.get_results()
        self.assertEqual(results, inspect_result)

    def test_get_vm_info(self):
        """Test the get vm info method."""
        data_center = 'dc1'
        cluster = 'cluster1'
        host = 'host1'
        virtual_machine = Mock()
        summary = Mock()
        config = Mock()
        config.name = 'vm1'
        summary.config = config
        virtual_machine.summary = summary
        vm_summary = {'cpu': '2',
                      'hostname': 'hostname',
                      'ip_address': 'ip1',
                      'mac': 'mac1',
                      'mem': '1.0',
                      'ostype': 'Red Hat 7',
                      'state': 'powerOn',
                      'uuid': '1111'}
        with patch('scanner.vcenter.inspect.vmsummary',
                   return_value=vm_summary):
            self.scan_task.systems_count = 5
            self.scan_task.systems_failed = 0
            self.scan_task.systems_scanned = 0
            self.scan_task.save()
            self.runner.get_vm_info(data_center, cluster,
                                    host, virtual_machine)

    # pylint: disable=too-many-locals
    def test_recurse_datacenter(self):
        """Test the recurse_datacenter method."""
        vcenter = Mock()
        content = Mock()
        root_folder = Mock()
        child_entity = []
        for k in range(0, 2):
            child = Mock()
            child.name = 'dc' + str(k)
            host_folder = Mock()
            clusters = []
            for j in range(0, 1):
                cluster = Mock()
                cluster.name = 'cluster' + str(j)
                host = Mock()
                h_summary = Mock()
                h_config = Mock()
                h_config.name = 'host1'
                h_summary.config = h_config
                host.summary = h_summary
                host.vm = [Mock()]
                hosts = [host]
                cluster.host = hosts
                clusters.append(cluster)
            host_folder.childEntity = clusters
            child.hostFolder = host_folder
            child_entity.append(child)
        root_folder.childEntity = child_entity
        content.rootFolder = root_folder
        vcenter.RetrieveContent = Mock(return_value=content)
        with patch.object(InspectTaskRunner,
                          'get_vm_info') as mock_get_vm_info:
            self.runner.recurse_datacenter(vcenter)
            mock_get_vm_info.assert_called()

    def test_inspect(self):
        """Test the inspect method."""
        with patch('scanner.vcenter.inspect.vcenter_connect',
                   return_value=Mock()) as mock_vcenter_connect:
            with patch.object(InspectTaskRunner,
                              'recurse_datacenter') as mock_recurse:
                self.runner.connect_scan_task = self.conn_task
                self.runner.inspect()
                mock_vcenter_connect.assert_called_once_with(ANY)
                mock_recurse.assert_called_once_with(ANY)

    def test_failed_run(self):
        """Test the run method."""
        with patch.object(InspectTaskRunner, 'inspect',
                          side_effect=invalid_login) as mock_connect:
            status = self.runner.run()
            self.assertEqual(ScanTask.FAILED, status)
            mock_connect.assert_called_once_with()

    def test_prereq_failed(self):
        """Test the run method."""
        self.conn_task.status = ScanTask.FAILED
        self.conn_task.save()
        status = self.runner.run()
        self.assertEqual(ScanTask.FAILED, status)

    def test_run(self):
        """Test the run method."""
        with patch.object(InspectTaskRunner, 'inspect') as mock_connect:
            status = self.runner.run()
            self.assertEqual(ScanTask.COMPLETED, status)
            mock_connect.assert_called_once_with()
