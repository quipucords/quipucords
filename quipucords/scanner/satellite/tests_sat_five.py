#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the satellite five interface."""
import json
import xmlrpc.client
from multiprocessing import Value
from unittest.mock import ANY, patch


from api.models import (Credential,
                        JobConnectionResult,
                        ScanJob,
                        ScanTask,
                        Source,
                        SystemConnectionResult,
                        SystemInspectionResult,
                        TaskConnectionResult)

from django.test import TestCase

from scanner.satellite.api import SatelliteException
from scanner.satellite.five import (SatelliteFive,
                                    request_host_details)
from scanner.test_util import create_scan_job


def mock_xml_fault(param1, param2):  # pylint: disable=unused-argument
    """Mock method to throw connection error."""
    raise xmlrpc.client.Fault(faultCode=500, faultString='fault')


# pylint: disable=too-many-instance-attributes
class SatelliteFiveTest(TestCase):
    """Tests Satellite 5 functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            cred_type=Credential.SATELLITE_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            become_method=None,
            become_user=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            port=443,
            hosts='["1.2.3.4"]')

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT)

        self.api = SatelliteFive(self.scan_job, self.scan_task)
        job_conn_result = JobConnectionResult()
        job_conn_result.save()
        connection_results = TaskConnectionResult(
            job_connection_result=job_conn_result)
        connection_results.save()
        self.api.connect_scan_task.connection_result = connection_results
        self.api.connect_scan_task.connection_result.save()

        conn_result = self.api.connect_scan_task.connection_result
        sys_result = SystemConnectionResult(
            name='sys1_1',
            status=SystemInspectionResult.SUCCESS,
            task_connection_result=conn_result)
        sys_result.save()
        self.api.connect_scan_task.save()

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    @patch('xmlrpc.client.ServerProxy')
    def test_host_count(self, mock_serverproxy):
        """Test the method host_count."""
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        client.system.list_user_systems.return_value = ['sys1', 'sys2', 'sys3']
        systems_count = self.api.host_count()
        self.assertEqual(systems_count, 3)

    @patch('xmlrpc.client.ServerProxy')
    def test_host_count_with_err(self, mock_serverproxy):
        """Test the method host_count with error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with self.assertRaises(SatelliteException):
            self.api.host_count()

    @patch('xmlrpc.client.ServerProxy')
    def test_hosts(self, mock_serverproxy):
        """Test the method hosts."""
        systems = [{'name': 'sys1',
                    'id': 1},
                   {'name': 'sys2',
                    'id': 2},
                   {'name': 'sys3',
                    'id': 3}]
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        client.system.list_user_systems.return_value = systems
        systems_count = self.api.host_count()
        hosts = self.api.hosts()
        self.assertEqual(systems_count, 3)
        self.assertEqual(len(hosts), 3)
        self.assertEqual(hosts, ['sys1_1', 'sys2_2', 'sys3_3'])

    @patch('xmlrpc.client.ServerProxy')
    def test_hosts_with_err(self, mock_serverproxy):
        """Test the method hosts with error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with self.assertRaises(SatelliteException):
            self.api.hosts()

    @patch('xmlrpc.client.ServerProxy')
    def test_host_details_virt_host(self, mock_serverproxy):
        """Test host_details method with mock data for virt host."""
        expected = {'uuid': 1, 'name': 'sys1', 'hostname': 'sys1_hostname',
                    'last_checkin_time': '', 'registration_time': 'datetime',
                    'architecture': 'x86', 'kernel_version': 'kernel',
                    'cores': 2, 'num_sockets': 2, 'os_release': '7server',
                    'entitlements': [{'name': 'ent1'}],
                    'ip_addresses': ['1.2.3.4'],
                    'mac_addresses': ['1:a:2:b:3:c'], 'virtual': 'hypervisor',
                    'num_virtual_guests': 3, 'is_virtualized': False}
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        client.system.get_uuid.return_value = ''
        cpu = {'arch': 'x86', 'count': 2, 'socket_count': 2}
        client.system.get_cpu.return_value = cpu
        system_details = {'hostname': 'sys1_hostname', 'release': '7server'}
        client.system.get_details.return_value = system_details
        client.system.get_running_kernel.return_value = 'kernel'
        client.system.get_entitlements.return_value = ['ent1']
        net_devices = [{'interface': 'eth0', 'ip': '1.2.3.4',
                        'hardware_address': '1:a:2:b:3:c'}]
        client.system.get_network_devices.return_value = net_devices
        client.system.get_registration_date.return_value = 'datetime'
        virt = {1: {'id': 1, 'num_virtual_guests': 3}}

        logging_options = {
            'job_id': self.scan_job.id,
            'task_sequence_number': self.scan_task.sequence_number,
            'scan_type': self.scan_task.scan_type,
            'source_type': self.scan_task.source.source_type,
            'source_name': self.scan_task.source.name
        }
        raw_result = request_host_details(host_id=1, host_name='sys1',
                                          last_checkin='',
                                          scan_task=self.scan_task,
                                          request_options={},
                                          logging_options=logging_options)
        self.api.process_results([raw_result], virt, {1: 2}, [])
        inspect_results = \
            self.scan_task.inspection_result.systems.all()
        sys_1_result = inspect_results.filter(name='sys1_1').first()
        self.assertEqual(sys_1_result.name, 'sys1_1')
        self.assertEqual(sys_1_result.status, 'success')
        result = {}
        for fact in sys_1_result.facts.all():
            result[fact.name] = json.loads(fact.value)
        self.assertEqual(result, expected)

    @patch('xmlrpc.client.ServerProxy')
    def test_host_details_virt_guest(self, mock_serverproxy):
        """Test host_details method with mock data for virt guest."""
        expected = {'uuid': 1, 'name': 'sys1', 'hostname': 'sys1_hostname',
                    'last_checkin_time': '', 'registration_time': 'datetime',
                    'architecture': 'x86', 'kernel_version': 'kernel',
                    'cores': 2, 'num_sockets': 2, 'os_release': '7server',
                    'entitlements': [{'name': 'ent1'}],
                    'ip_addresses': ['1.2.3.4'],
                    'mac_addresses': ['1:a:2:b:3:c'],
                    'is_virtualized': True, 'virtual_host': 2,
                    'virtual_host_name': 'sys2'}
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        client.system.get_uuid.return_value = ''
        cpu = {'arch': 'x86', 'count': 2, 'socket_count': 2}
        client.system.get_cpu.return_value = cpu
        system_details = {'hostname': 'sys1_hostname', 'release': '7server'}
        client.system.get_details.return_value = system_details
        client.system.get_running_kernel.return_value = 'kernel'
        client.system.get_entitlements.return_value = ['ent1']
        net_devices = [{'interface': 'eth0', 'ip': '1.2.3.4',
                        'hardware_address': '1:a:2:b:3:c'}]
        client.system.get_network_devices.return_value = net_devices
        client.system.get_registration_date.return_value = 'datetime'
        virt = {2: {'uuid': 2, 'name': 'sys2', 'num_virtual_guests': 3}}
        raw_result = request_host_details(host_id=1, host_name='sys1',
                                          last_checkin='',
                                          scan_task=self.scan_task,
                                          request_options={},
                                          logging_options=None)
        self.api.process_results([raw_result], virt, {1: 2}, [])
        inspect_results = \
            self.scan_task.inspection_result.systems.all()
        sys_1_result = inspect_results.filter(name='sys1_1').first()
        self.assertEqual(sys_1_result.name, 'sys1_1')
        self.assertEqual(sys_1_result.status, 'success')
        result = {}
        for fact in sys_1_result.facts.all():
            result[fact.name] = json.loads(fact.value)
        self.assertEqual(result, expected)

    def test_prepare_host_s5(self):
        """Test the prepare host method for satellite 5."""
        expected = [(1, 'sys', '', self.scan_task,
                     {'host': {'id': 1, 'name': 'sys', 'last_checkin': ''},
                      'port': '443', 'user': self.cred.username,
                      'password': self.cred.password,
                      'ssl_cert_verify': True},
                     {'job_id': self.scan_job.id,
                      'task_sequence_number': self.scan_task.sequence_number,
                      'scan_type': self.scan_task.scan_type,
                      'source_type': self.scan_task.source.source_type,
                      'source_name': self.scan_task.source.name})]
        host = {'id': 1, 'name': 'sys', 'last_checkin': ''}
        chunk = [host]
        port = '443'
        user = self.cred.username
        password = self.cred.password
        connect_data_return_value = host, port, user, password
        with patch('scanner.satellite.utils.get_connect_data',
                   return_value=connect_data_return_value) as mock_connect:
            host_params = self.api.prepare_host(chunk)
            self.assertEqual(expected, host_params)
            mock_connect.assert_called_once_with(ANY)

    @patch('xmlrpc.client.ServerProxy')
    def test_host_details_with_err(self, mock_serverproxy):
        """Test the host details with an error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        virt = {2: {'uuid': 2, 'name': 'sys2', 'num_virtual_guests': 3}}
        raw_result = request_host_details(host_id=2, host_name='sys2',
                                          last_checkin='',
                                          scan_task=self.scan_task,
                                          request_options={},
                                          logging_options=None)

        self.api.process_results([raw_result], virt, {1: 2}, [])
        inspect_results = \
            self.scan_task.inspection_result.systems.all()
        sys_1_result = inspect_results.filter(name='sys2_2').first()
        self.assertEqual(sys_1_result.name, 'sys2_2')
        self.assertEqual(sys_1_result.status, 'failed')
        result = {}
        for fact in sys_1_result.facts.all():
            result[fact.name] = json.loads(fact.value)
        self.assertEqual(result, {})

    @patch('xmlrpc.client.ServerProxy')
    def test_virtual_guests_with_err(self, mock_serverproxy):
        """Test the virtual_guests method with an error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with self.assertRaises(SatelliteException):
            self.api.virtual_guests(1)

    @patch('xmlrpc.client.ServerProxy')
    def test_virtual_guests(self, mock_serverproxy):
        """Test the virtual_guests method with an error."""
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        guests = [{'id': 2}]
        client.system.list_virtual_guests.return_value = guests
        virt_guests = self.api.virtual_guests(1)
        self.assertEqual(virt_guests, ({2: 1}, 1))

    @patch('xmlrpc.client.ServerProxy')
    def test_virtual_hosts_with_err(self, mock_serverproxy):
        """Test the virtual_hosts method with an error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with self.assertRaises(SatelliteException):
            self.api.virtual_hosts()

    @patch('xmlrpc.client.ServerProxy')
    def test_virtual_hosts(self, mock_serverproxy):
        """Test the virtual_hosts method."""
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        guests = [{'id': 2}]
        client.system.list_virtual_guests.return_value = guests
        hosts = [{'id': 1, 'name': 'host1'}]
        client.system.list_virtual_hosts.return_value = hosts
        client.system.get_uuid.return_value = ''
        virtual_hosts, virtual_guests = self.api.virtual_hosts()
        virt_host = {1: {'id': 1, 'name': 'host1',
                         'uuid': 1, 'num_virtual_guests': 1}}
        virt_guest = {2: 1}
        self.assertEqual(virtual_hosts, virt_host)
        self.assertEqual(virtual_guests, virt_guest)

    @patch('xmlrpc.client.ServerProxy')
    def test_physical_hosts_with_err(self, mock_serverproxy):
        """Test the phyiscal_hosts method with an error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with self.assertRaises(SatelliteException):
            self.api.physical_hosts()

    @patch('xmlrpc.client.ServerProxy')
    def test_physical_hosts(self, mock_serverproxy):
        """Test the physical_hosts method."""
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        hosts = [{'id': 1, 'name': 'host1'}]
        client.system.list_physical_systems.return_value = hosts
        phyiscal_hosts = self.api.physical_hosts()
        self.assertEqual(phyiscal_hosts, [1])

    @patch('xmlrpc.client.ServerProxy')
    def test_hosts_facts_with_err(self, mock_serverproxy):
        """Test the hosts_facts method with an error."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with self.assertRaises(SatelliteException):
            self.api.hosts_facts(Value('i', ScanJob.JOB_RUN))

    @patch('multiprocessing.pool.Pool.starmap', return_value=[
        {'host_name': 'sys10',
         'last_checkin': '',
         'host_id': 1,
         'cpu': {},
         'uuid': 1,
         'system_details': {},
         'kernel': '',
         'subs': [],
         'network_devices': [],
         'registration_date': '',
         'system_inspection_result': SystemInspectionResult.SUCCESS}])
    @patch('xmlrpc.client.ServerProxy')
    def test_hosts_facts(self, mock_serverproxy, mock_pool):
        """Test the hosts_facts method."""
        # pylint: disable=unused-argument
        systems = [{'id': 1, 'name': 'sys1'}]
        client = mock_serverproxy.return_value
        client.auth.login.return_value = 'key'
        client.auth.logout.return_value = 'key'
        client.system.list_user_systems.return_value = systems
        hosts_return_value = ({}, {})
        with patch.object(SatelliteFive, 'virtual_hosts',
                          return_value=hosts_return_value) as mock_vhosts:
            with patch.object(SatelliteFive, 'physical_hosts',
                              return_value=[]) as mock_physical:
                self.api.hosts_facts(Value('i', ScanJob.JOB_RUN))
                inspect_result = self.scan_task.inspection_result
                self.assertEqual(len(inspect_result.systems.all()), 1)
                mock_vhosts.assert_called_once_with()
                mock_physical.assert_called_once_with()
