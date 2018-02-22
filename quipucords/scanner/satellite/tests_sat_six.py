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
"""Test the satellite six interface."""

from datetime import datetime
from unittest.mock import patch, ANY
import requests_mock
from django.test import TestCase
from api.models import (Credential, Source, ScanTask,
                        ScanJob, ConnectionResults, ConnectionResult,
                        InspectionResult, SystemInspectionResult)
from scanner.satellite.utils import construct_url
from scanner.satellite.api import SatelliteException
from scanner.satellite.six import (SatelliteSixV1, SatelliteSixV2,
                                   host_fields, host_subscriptions)


# pylint: disable=unused-argument
def mock_sat_exception(param1, param2, param3, param4, param5):
    """Mock method to throw satellite error."""
    raise SatelliteException()


# pylint: disable=too-many-instance-attributes
class SatelliteSixV1Test(TestCase):
    """Tests Satellite 6 v1 functions."""

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

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=1,
                                  start_time=datetime.utcnow())
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = ConnectionResults(scan_job=self.scan_job)
        self.conn_results.save()
        self.conn_result = ConnectionResult(
            scan_task=self.scan_task, source=self.source)
        self.conn_result.save()

        self.inspect_result = InspectionResult(scan_task=self.scan_task,
                                               source=self.source)
        self.inspect_result.save()

        self.api = SatelliteSixV1(self.scan_task, self.conn_result,
                                  self.inspect_result)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_get_orgs(self):
        """Test the method to get orgs."""
        orgs_url = 'https://{sat_host}:{port}/katello/api/v2/organizations'
        with requests_mock.Mocker() as mocker:
            url = construct_url(orgs_url, '1.2.3.4')
            jsonresult = {'results': [{'id': 1}, {'id': 7}, {'id': 8}],
                          'per_page': 100}
            mocker.get(url, status_code=200, json=jsonresult)
            orgs = self.api.get_orgs()
            orgs2 = self.api.get_orgs()
            self.assertEqual(orgs, [1, 7, 8])
            self.assertEqual(orgs, orgs2)

    def test_get_orgs_with_err(self):
        """Test the method to get orgs with err."""
        orgs_url = 'https://{sat_host}:{port}/katello/api/v2/organizations'
        with requests_mock.Mocker() as mocker:
            url = construct_url(orgs_url, '1.2.3.4')
            jsonresult = {'results': [{'id': 1}, {'id': 7}, {'id': 8}],
                          'per_page': 100}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.get_orgs()

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_host_count(self, mock_get_orgs):
        """Test the method host_count."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            self.assertEqual(systems_count, 3)

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_host_count_with_err(self, mock_get_orgs):
        """Test the method host_count with err."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.host_count()

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_hosts(self, mock_get_orgs):
        """Test the method hosts."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            hosts = self.api.hosts()
            self.assertEqual(systems_count, 3)
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ['sys1', 'sys2', 'sys3'])

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_hosts_with_err(self, mock_get_orgs):
        """Test the method hosts."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.hosts()

    def test_host_fields(self):
        """Test the method host_fields."""
        host_field_url = 'https://{sat_host}:{port}/api/v2/hosts/{host_id}'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host='1.2.3.4',
                                host_id=1)
            jsonresult = {
                'architecture_id': 1,
                'architecture_name': 'x86_64',
                'operatingsystem_name': 'RedHat 7.4',
                'uuid': None,
                'created_at': '2017-12-04 13:19:57 UTC',
                'updated_at': '2017-12-04 13:21:47 UTC',
                'organization_name': 'ACME',
                'location_name': 'Raleigh',
                'name': 'mac52540071bafe.prov.lan',
                'virtual_host': {'uuid': '100', 'name': 'vhost1'},
                'virtual_guests': [{'name': 'foo'}],
                'content_facet_attributes': {
                    'id': 11,
                    'katello_agent_installed': False
                },
                'subscription_facet_attributes': {
                    'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
                    'last_checkin': '2018-01-04 17:36:07 UTC',
                    'registered_at': '2017-12-04 13:33:52 UTC',
                    'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
                    'virtual_host': {'uuid': '100', 'name': 'vhost1'},
                    'virtual_guests': [{'name': 'foo'}],
                },
                'facts': {
                    'memorysize_mb': '992.45',
                    'memorysize': '992.45 MB',
                    'hostname': 'fdi',
                    'type': 'Other',
                    'architecture': 'x86_64',
                    'is_virtual': 'true',
                    'virtual': 'kvm',
                    'net.interface.ipv4_address': '192.168.99.123',
                    'net.interface.mac_address': 'fe80::5054:ff:fe24:946e',
                },
            }
            mocker.get(url, status_code=200, json=jsonresult)
            host_info = host_fields(self.scan_task, 1,
                                    host_field_url, None, 1)
            expected = {
                'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
                'hostname': 'mac52540071bafe.prov.lan',
                'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
                'registration_time': '2017-12-04 13:33:52 UTC',
                'last_checkin_time': '2018-01-04 17:36:07 UTC',
                'katello_agent_installed': False,
                'os_release': 'RedHat 7.4',
                'organization': 'ACME',
                'virtual_host': '100',
                'virtual_host_name': 'vhost1',
                'virt_type': None,
                'kernel_version': None,
                'architecture': None, 'is_virtualized': None,
                'cores': None, 'num_sockets': None, 'num_virtual_guests': 1,
                'virtual': 'hypervisor', 'location': 'Raleigh',
                'ip_addresses': ['192.168.99.123'],
                'mac_addresses': ['fe80::5054:ff:fe24:946e'],
                'os_name': 'RedHat', 'os_version': '7.4'}
            self.assertEqual(host_info, expected)

    def test_host_details_skip(self):
        """Test host_details method for already captured data."""
        sys_result = SystemInspectionResult(
            name='sys1',
            status=SystemInspectionResult.SUCCESS)
        sys_result.save()
        self.inspect_result.systems.add(sys_result)
        self.inspect_result.save()
        detail = self.api.host_details(1, 1, 'sys1')
        self.assertEqual(len(self.inspect_result.systems.all()), 1)
        self.assertEqual(detail, {})

    def test_host_details_err(self):
        """Test host_details method for error mark a failed system."""
        with patch('scanner.satellite.six.host_fields',
                   side_effect=mock_sat_exception) as mock_fields:
            detail = self.api.host_details(1, 1, 'sys1')
            self.assertEqual(len(self.inspect_result.systems.all()), 1)
            sys_result = self.inspect_result.systems.all().first()
            self.assertEqual(sys_result.status, SystemInspectionResult.FAILED)
            self.assertEqual(detail, {})
            mock_fields.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)

    def test_host_details(self):
        """Test host_details method with mock data."""
        fields_return_value = {
            'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
            'hostname': 'mac52540071bafe.prov.lan',
            'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
            'registration_time': '2017-12-04 13:33:52 UTC',
            'last_checkin_time': '2018-01-04 17:36:07 UTC',
            'katello_agent_installed': False,
            'os_name': 'RedHat 7.4',
            'organization': 'ACME',
            'virtual_host': '100',
            'virtual_host_name':
            'vhost1', 'virt_type': None,
            'kernel_version': None,
            'architecture': None,
            'is_virtualized': None,
            'cores': None,
            'num_sockets': None,
            'num_virtual_guests': 1,
            'virtual': 'hypervisor',
            'location': 'Raleigh',
            'ip_addresses': ['192.168.99.123'],
            'ipv6_addresses': ['fe80::5054:ff:fe24:946e']}
        subs_return_value = {
            'entitlements':
                [{'derived_entitlement': False,
                  'name': 'Satellite Tools 6.3',
                  'amount': 1,
                  'account_number': None,
                  'contract_number': None,
                  'start_date': '2017-12-01 14:50:59 UTC',
                  'end_date': '2047-11-24 14:50:59 UTC'},
                 {'derived_entitlement': True,
                  'name': 'Employee SKU',
                  'amount': 1,
                  'account_number': 1212729,
                  'contract_number': 10913844,
                  'start_date': '2016-03-24 04:00:00 UTC',
                  'end_date': '2022-01-01 04:59:59 UTC'}]}
        expected = {
            'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
            'hostname': 'mac52540071bafe.prov.lan',
            'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
            'registration_time': '2017-12-04 13:33:52 UTC',
            'last_checkin_time': '2018-01-04 17:36:07 UTC',
            'katello_agent_installed': False,
            'os_name': 'RedHat 7.4',
            'organization': 'ACME',
            'virtual_host': '100',
            'virtual_host_name': 'vhost1',
            'virt_type': None,
            'kernel_version': None,
            'architecture': None,
            'is_virtualized': None,
            'cores': None,
            'num_sockets': None,
            'num_virtual_guests': 1,
            'virtual': 'hypervisor',
            'location': 'Raleigh',
            'ip_addresses': ['192.168.99.123'],
            'ipv6_addresses': ['fe80::5054:ff:fe24:946e'],
            'entitlements': [
                {'derived_entitlement': False,
                 'name': 'Satellite Tools 6.3',
                 'amount': 1,
                 'account_number': None,
                 'contract_number': None,
                 'start_date': '2017-12-01 14:50:59 UTC',
                 'end_date': '2047-11-24 14:50:59 UTC'},
                {'derived_entitlement': True,
                 'name': 'Employee SKU',
                 'amount': 1,
                 'account_number': 1212729,
                 'contract_number': 10913844,
                 'start_date': '2016-03-24 04:00:00 UTC',
                 'end_date': '2022-01-01 04:59:59 UTC'}]}

        self.scan_task.save()
        self.scan_task.update_stats('TEST_SAT.', sys_scanned=0)
        with patch('scanner.satellite.six.host_fields',
                   return_value=fields_return_value) as mock_fields:
            with patch('scanner.satellite.six.host_subscriptions',
                       return_value=subs_return_value) as mock_subs:
                details = self.api.host_details(org_id=1,
                                                host_id=1,
                                                host_name='sys1')
                self.assertEqual(details, expected)
                mock_fields.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)
                mock_subs.assert_called_once_with(ANY, ANY, ANY, ANY)

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_hosts_facts_with_err(self, mock_get_orgs):
        """Test the hosts_facts method."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            mocker.get(url, status_code=500)
            with self.assertRaises(SatelliteException):
                self.api.hosts_facts()

    def test_hosts_facts(self):
        """Test the method hosts."""
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with patch.object(SatelliteSixV1, 'get_orgs',
                          return_value=[1]) as mock_get_orgs:
            with patch.object(SatelliteSixV1, 'host_details',
                              return_value={}) as mock_host_details:
                with requests_mock.Mocker() as mocker:
                    url = construct_url(url=hosts_url,
                                        sat_host='1.2.3.4',
                                        org_id=1)
                    jsonresult = {'results': [{'uuid': '1', 'name': 'sys1'},
                                              {'uuid': '2', 'name': 'sys2'},
                                              {'uuid': '3', 'name': 'sys3'}],
                                  'per_page': 100,
                                  'total': 3}
                    mocker.get(url, status_code=200, json=jsonresult)
                    self.api.hosts_facts()
                    mock_get_orgs.assert_called_once_with()
                    mock_host_details.assert_called_with(ANY, ANY, ANY)


# pylint: disable=too-many-instance-attributes
class SatelliteSixV2Test(TestCase):
    """Tests Satellite 6 v2 functions."""

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

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=1,
                                  start_time=datetime.utcnow())
        self.scan_task.save()
        self.scan_task.update_stats('TEST_SAT.', sys_scanned=0)

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = ConnectionResults(scan_job=self.scan_job)
        self.conn_results.save()
        self.conn_result = ConnectionResult(
            scan_task=self.scan_task, source=self.source)
        self.conn_result.save()
        self.inspect_result = InspectionResult(scan_task=self.scan_task,
                                               source=self.source)
        self.inspect_result.save()
        self.api = SatelliteSixV2(self.scan_task,
                                  self.conn_result,
                                  self.inspect_result)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_host_count(self):
        """Test the method host_count."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            self.assertEqual(systems_count, 3)

    def test_host_count_with_err(self):
        """Test the method host_count with error."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.host_count()

    def test_hosts(self):
        """Test the method hosts."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            hosts = self.api.hosts()
            self.assertEqual(systems_count, 3)
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ['sys1', 'sys2', 'sys3'])

    def test_hosts_with_err(self):
        """Test the method hosts with error."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.hosts()

    def test_host_fields_with_err(self):
        """Test the method host_fields with error."""
        host_field_url = 'https://{sat_host}:{port}/api/v2/hosts/{host_id}'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host='1.2.3.4',
                                host_id=1)
            mocker.get(url, status_code=500)
            with self.assertRaises(SatelliteException):
                host_fields(self.scan_task, 2, host_field_url, None, 1)

    def test_host_fields(self):
        """Test the method host_fields."""
        host_field_url = 'https://{sat_host}:{port}/api/v2/hosts/{host_id}'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host='1.2.3.4',
                                host_id=1)
            jsonresult = {
                'architecture_id': 1,
                'architecture_name': 'x86_64',
                'operatingsystem_name': 'RedHat 7.4',
                'uuid': None,
                'created_at': '2017-12-04 13:19:57 UTC',
                'updated_at': '2017-12-04 13:21:47 UTC',
                'organization_name': 'ACME',
                'location_name': 'Raleigh',
                'name': 'mac52540071bafe.prov.lan',
                'virtual_host': {'uuid': '100', 'name': 'vhost1'},
                'virtual_guests': [{'name': 'foo'}],
                'content_facet_attributes': {
                    'id': 11,
                    'katello_agent_installed': False
                },
                'subscription_facet_attributes': {
                    'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
                    'last_checkin': '2018-01-04 17:36:07 UTC',
                    'registered_at': '2017-12-04 13:33:52 UTC',
                    'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
                    'virtual_host': {'uuid': '100', 'name': 'vhost1'},
                    'virtual_guests': [{'name': 'foo'}],
                },
                'facts': {
                    'memorysize_mb': '992.45',
                    'memorysize': '992.45 MB',
                    'hostname': 'fdi',
                    'type': 'Other',
                    'architecture': 'x86_64',
                    'is_virtual': 'true',
                    'virtual': 'kvm',
                    'net::interface::ipv4_address': '192.168.99.123',
                    'net::interface::mac_address': 'fe80::5054:ff:fe24:946e',
                },
            }
            mocker.get(url, status_code=200, json=jsonresult)
            host_info = host_fields(self.scan_task, 2,
                                    host_field_url, None, 1)
            expected = {
                'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
                'hostname': 'mac52540071bafe.prov.lan',
                'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
                'registration_time': '2017-12-04 13:33:52 UTC',
                'last_checkin_time': '2018-01-04 17:36:07 UTC',
                'katello_agent_installed': False,
                'os_release': 'RedHat 7.4',
                'organization': 'ACME',
                'virtual_host': '100',
                'virtual_host_name': 'vhost1',
                'virt_type': None,
                'kernel_version': None,
                'architecture': None, 'is_virtualized': None,
                'cores': None, 'num_sockets': None, 'num_virtual_guests': 1,
                'virtual': 'hypervisor', 'location': 'Raleigh',
                'ip_addresses': ['192.168.99.123'],
                'mac_addresses': ['fe80::5054:ff:fe24:946e'],
                'os_name': 'RedHat', 'os_version': '7.4'}
            self.assertEqual(host_info, expected)

    def test_host_subs_with_err(self):
        """Test the host subscriptons method with bad status code."""
        sub_url = 'https://{sat_host}:{port}/' \
            'api/v2/hosts/{host_id}/subscriptions'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host='1.2.3.4',
                                host_id=1)
            mocker.get(url, status_code=500)
            with self.assertRaises(SatelliteException):
                host_subscriptions(self.scan_task, sub_url, None, 1)

    def test_host_subs_err_nojson(self):
        """Test the host subscriptons method with bad code and not json."""
        sub_url = 'https://{sat_host}:{port}/' \
            'api/v2/hosts/{host_id}/subscriptions'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host='1.2.3.4',
                                host_id=1)
            mocker.get(url, status_code=404, text='error message')
            subs = host_subscriptions(self.scan_task, sub_url, None, 1)
            self.assertEqual(subs, {'entitlements': []})

    def test_host_not_subscribed(self):
        """Test the host subscriptons method for not subscribed error."""
        sub_url = 'https://{sat_host}:{port}/' \
            'api/v2/hosts/{host_id}/subscriptions'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host='1.2.3.4',
                                host_id=1)
            err_msg = {
                'displayMessage': 'Host has not been registered '
                                  'with subscription-manager',
                'errors': ['Host has not been registered'
                           ' with subscription-manager']
                }  # noqa
            mocker.get(url, status_code=400, json=err_msg)
            subs = host_subscriptions(self.scan_task, sub_url, None, 1)
            self.assertEqual(subs, {'entitlements': []})

    def test_host_subscriptons(self):
        """Test the host subscriptons method."""
        sub_url = 'https://{sat_host}:{port}/' \
            'api/v2/hosts/{host_id}/subscriptions'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host='1.2.3.4',
                                host_id=1)
            jsonresult = {
                'results': [
                    {
                        'amount': 1,
                        'name': 'Satellite Tools 6.3',
                        'start_date': '2017-12-01 14:50:59 UTC',
                        'end_date': '2047-11-24 14:50:59 UTC',
                        'product_name': 'Satellite Tools 6.3',
                    },
                    {
                        'quantity_consumed': 1,
                        'name': 'Employee SKU',
                        'start_date': '2016-03-24 04:00:00 UTC',
                        'end_date': '2022-01-01 04:59:59 UTC',
                        'account_number': 1212729,
                        'contract_number': 10913844,
                        'type': 'ENTITLEMENT_DERIVED',
                        'product_name': 'Employee SKU',
                    }
                ]
            }
            mocker.get(url, status_code=200, json=jsonresult)
            subs = host_subscriptions(self.scan_task, sub_url, None, 1)
            expected = {'entitlements':
                        [{'derived_entitlement': False,
                          'name': 'Satellite Tools 6.3',
                          'amount': 1,
                          'account_number': None,
                          'contract_number': None,
                          'start_date': '2017-12-01 14:50:59 UTC',
                          'end_date': '2047-11-24 14:50:59 UTC'},
                         {'derived_entitlement': True,
                          'name': 'Employee SKU',
                          'amount': 1,
                          'account_number': 1212729,
                          'contract_number': 10913844,
                          'start_date': '2016-03-24 04:00:00 UTC',
                          'end_date': '2022-01-01 04:59:59 UTC'}]}
            self.assertEqual(subs, expected)

    def test_host_details_err(self):
        """Test host_details method for error mark a failed system."""
        with patch('scanner.satellite.six.host_fields',
                   side_effect=mock_sat_exception) as mock_fields:
            detail = self.api.host_details(1, 'sys1')
            self.assertEqual(len(self.inspect_result.systems.all()), 1)
            sys_result = self.inspect_result.systems.all().first()
            self.assertEqual(sys_result.status, SystemInspectionResult.FAILED)
            self.assertEqual(detail, {})
            mock_fields.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)

    def test_host_details(self):
        """Test host_details method with mock data."""
        fields_return_value = {
            'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
            'hostname': 'mac52540071bafe.prov.lan',
            'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
            'registration_time': '2017-12-04 13:33:52 UTC',
            'last_checkin_time': '2018-01-04 17:36:07 UTC',
            'katello_agent_installed': False,
            'os_name': 'RedHat 7.4',
            'organization': 'ACME',
            'virtual_host': '100',
            'virtual_host_name':
            'vhost1', 'virt_type': None,
            'kernel_version': None,
            'architecture': None,
            'is_virtualized': None,
            'cores': None,
            'num_sockets': None,
            'num_virtual_guests': 1,
            'virtual': 'hypervisor',
            'location': 'Raleigh',
            'ip_addresses': ['192.168.99.123'],
            'ipv6_addresses': ['fe80::5054:ff:fe24:946e']}
        subs_return_value = {
            'entitlements':
                [{'derived_entitlement': False,
                  'name': 'Satellite Tools 6.3',
                  'amount': 1,
                  'account_number': None,
                  'contract_number': None,
                  'start_date': '2017-12-01 14:50:59 UTC',
                  'end_date': '2047-11-24 14:50:59 UTC'},
                 {'derived_entitlement': True,
                  'name': 'Employee SKU',
                  'amount': 1,
                  'account_number': 1212729,
                  'contract_number': 10913844,
                  'start_date': '2016-03-24 04:00:00 UTC',
                  'end_date': '2022-01-01 04:59:59 UTC'}]}
        expected = {
            'uuid': '00c7a108-48ec-4a97-835c-aa3369777f64',
            'hostname': 'mac52540071bafe.prov.lan',
            'registered_by': 'sat-r220-07.lab.eng.rdu2.redhat.com',
            'registration_time': '2017-12-04 13:33:52 UTC',
            'last_checkin_time': '2018-01-04 17:36:07 UTC',
            'katello_agent_installed': False,
            'os_name': 'RedHat 7.4',
            'organization': 'ACME',
            'virtual_host': '100',
            'virtual_host_name': 'vhost1',
            'virt_type': None,
            'kernel_version': None,
            'architecture': None,
            'is_virtualized': None,
            'cores': None,
            'num_sockets': None,
            'num_virtual_guests': 1,
            'virtual': 'hypervisor',
            'location': 'Raleigh',
            'ip_addresses': ['192.168.99.123'],
            'ipv6_addresses': ['fe80::5054:ff:fe24:946e'],
            'entitlements': [
                {'derived_entitlement': False,
                 'name': 'Satellite Tools 6.3',
                 'amount': 1,
                 'account_number': None,
                 'contract_number': None,
                 'start_date': '2017-12-01 14:50:59 UTC',
                 'end_date': '2047-11-24 14:50:59 UTC'},
                {'derived_entitlement': True,
                 'name': 'Employee SKU',
                 'amount': 1,
                 'account_number': 1212729,
                 'contract_number': 10913844,
                 'start_date': '2016-03-24 04:00:00 UTC',
                 'end_date': '2022-01-01 04:59:59 UTC'}]}
        with patch('scanner.satellite.six.host_fields',
                   return_value=fields_return_value) as mock_fields:
            with patch('scanner.satellite.six.host_subscriptions',
                       return_value=subs_return_value) as mock_subs:
                details = self.api.host_details(host_id=1, host_name='sys1')
                self.assertEqual(details, expected)
                mock_fields.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)
                mock_subs.assert_called_once_with(ANY, ANY, ANY, ANY)

    def test_host_details_skip(self):
        """Test host_details method for already captured data."""
        sys_result = SystemInspectionResult(
            name='sys1',
            status=SystemInspectionResult.SUCCESS)
        sys_result.save()
        self.inspect_result.systems.add(sys_result)
        self.inspect_result.save()
        detail = self.api.host_details(1, 'sys1')
        self.assertEqual(len(self.inspect_result.systems.all()), 1)
        self.assertEqual(detail, {})

    def test_hosts_facts_with_err(self):
        """Test the hosts_facts method."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4')
            mocker.get(url, status_code=500)
            with self.assertRaises(SatelliteException):
                self.api.hosts_facts()

    def test_hosts_facts(self):
        """Test the hosts_facts method."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4')
            jsonresult = {
                'total': 1,
                'subtotal': 1,
                'page': 1,
                'per_page': 100,
                'results': [{'id': 10, 'name': 'sys10'}]
                }  # noqa
            mocker.get(url, status_code=200, json=jsonresult)
            detail_return_value = {}
            with patch.object(SatelliteSixV2, 'host_details',
                              return_value=detail_return_value) as mock_detail:
                self.api.hosts_facts()
                mock_detail.assert_called_once_with(ANY, ANY)
