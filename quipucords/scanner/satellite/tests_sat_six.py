"""Test the satellite six interface."""
from multiprocessing import Value
from unittest.mock import ANY, patch

import requests_mock
from django.test import TestCase

from api.models import (
    Credential,
    JobConnectionResult,
    ScanJob,
    ScanOptions,
    ScanTask,
    Source,
    SystemConnectionResult,
    SystemInspectionResult,
    TaskConnectionResult,
)
from constants import DataSources
from scanner.satellite.api import SatelliteException
from scanner.satellite.six import (
    SatelliteSixV1,
    SatelliteSixV2,
    host_fields,
    host_subscriptions,
    process_results,
    request_host_details,
)
from scanner.satellite.utils import construct_url
from scanner.test_util import create_scan_job

# pylint: disable=too-many-lines


# pylint: disable=unused-argument, too-many-arguments,
def mock_sat_exception(
    param1,
    param2,
    param3,
    param4,
    param5,
    param6=None,
    param7=None,
    param8=None,
    param9=None,
    param10=None,
):
    """Mock method to throw satellite error."""
    raise SatelliteException()


# pylint: disable=too-many-instance-attributes
class SatelliteSixV1Test(TestCase):
    """Tests Satellite 6 v1 functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            cred_type=DataSources.SATELLITE,
            username="username",
            password="password",
            become_password=None,
            become_method=None,
            become_user=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        self.source = Source(name="source1", port=443, hosts=["1.2.3.4"])

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT
        )

        self.api = SatelliteSixV1(self.scan_job, self.scan_task)
        job_conn_result = JobConnectionResult()
        job_conn_result.save()
        connection_results = TaskConnectionResult(job_connection_result=job_conn_result)
        connection_results.save()
        self.api.connect_scan_task.connection_result = connection_results
        self.api.connect_scan_task.connection_result.save()

        conn_result = self.api.connect_scan_task.connection_result
        sys_result = SystemConnectionResult(
            name="sys1_1",
            status=SystemInspectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        self.api.connect_scan_task.save()

    def tearDown(self):
        """Cleanup test case setup."""

    def test_get_orgs(self):
        """Test the method to get orgs."""
        orgs_url = "https://{sat_host}:{port}/katello/api/v2/organizations"
        with requests_mock.Mocker() as mocker:
            url = construct_url(orgs_url, "1.2.3.4")
            jsonresult = {"results": [{"id": 1}, {"id": 7}, {"id": 8}], "per_page": 100}
            mocker.get(url, status_code=200, json=jsonresult)
            orgs = self.api.get_orgs()
            orgs2 = self.api.get_orgs()
            self.assertEqual(orgs, [1, 7, 8])
            self.assertEqual(orgs, orgs2)

    def test_get_orgs_with_err(self):
        """Test the method to get orgs with err."""
        orgs_url = "https://{sat_host}:{port}/katello/api/v2/organizations"
        with requests_mock.Mocker() as mocker:
            url = construct_url(orgs_url, "1.2.3.4")
            jsonresult = {"results": [{"id": 1}, {"id": 7}, {"id": 8}], "per_page": 100}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.get_orgs()

    @patch("scanner.satellite.six.SatelliteSixV1.get_orgs")
    def test_host_count(self, mock_get_orgs):
        """Test the method host_count."""
        mock_get_orgs.return_value = [1]
        hosts_url = (
            "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
        )
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [{"name": "sys1"}, {"name": "sys2"}, {"name": "sys3"}],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            self.assertEqual(systems_count, 3)

    @patch("scanner.satellite.six.SatelliteSixV1.get_orgs")
    def test_host_count_with_err(self, mock_get_orgs):
        """Test the method host_count with err."""
        mock_get_orgs.return_value = [1]
        hosts_url = (
            "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
        )
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [{"name": "sys1"}, {"name": "sys2"}, {"name": "sys3"}],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.host_count()

    @patch("scanner.satellite.six.SatelliteSixV1.get_orgs")
    def test_hosts(self, mock_get_orgs):
        """Test the method hosts."""
        mock_get_orgs.return_value = [1]
        hosts_url = (
            "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
        )
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [
                    {"name": "sys1", "id": 1},
                    {"name": "sys2", "id": 2},
                    {"name": "sys3", "id": 3},
                ],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            hosts = self.api.hosts()
            self.assertEqual(systems_count, 3)
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ["sys1_1", "sys2_2", "sys3_3"])

    @patch("scanner.satellite.six.SatelliteSixV1.get_orgs")
    def test_hosts_with_err(self, mock_get_orgs):
        """Test the method hosts."""
        mock_get_orgs.return_value = [1]
        hosts_url = (
            "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
        )
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [{"name": "sys1"}, {"name": "sys2"}, {"name": "sys3"}],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.hosts()

    def test_host_fields(self):
        """Test the method host_fields."""
        host_field_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host="1.2.3.4", host_id=1)
            jsonresult = {
                "architecture_id": 1,
                "architecture_name": "x86_64",
                "operatingsystem_name": "RedHat 7.4",
                "uuid": None,
                "created_at": "2017-12-04 13:19:57 UTC",
                "updated_at": "2017-12-04 13:21:47 UTC",
                "organization_name": "ACME",
                "location_name": "Raleigh",
                "name": "mac52540071bafe.prov.lan",
                "virtual_host": {"uuid": "100", "name": "vhost1"},
                "virtual_guests": [{"name": "foo"}],
                "content_facet_attributes": {
                    "id": 11,
                    "katello_agent_installed": False,
                },
                "subscription_facet_attributes": {
                    "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
                    "last_checkin": "2018-01-04 17:36:07 UTC",
                    "registered_at": "2017-12-04 13:33:52 UTC",
                    "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
                    "virtual_host": {"uuid": "100", "name": "vhost1"},
                    "virtual_guests": [{"name": "foo"}],
                },
                "facts": {
                    "memorysize_mb": "992.45",
                    "memorysize": "992.45 MB",
                    "hostname": "fdi",
                    "type": "Other",
                    "architecture": "x86_64",
                    "is_virtual": "true",
                    "virtual": "kvm",
                    "net.interface.ipv4_address": "192.168.99.123",
                    "net.interface.mac_address": "fe80::5054:ff:fe24:946e",
                },
            }
            mocker.get(url, status_code=200, json=jsonresult)
            host_info = host_fields(1, jsonresult)
            expected = {
                "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
                "hostname": "mac52540071bafe.prov.lan",
                "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
                "registration_time": "2017-12-04 13:33:52 UTC",
                "last_checkin_time": "2018-01-04 17:36:07 UTC",
                "katello_agent_installed": False,
                "os_release": "RedHat 7.4",
                "organization": "ACME",
                "virtual_host_uuid": "100",
                "virtual_host_name": "vhost1",
                "virt_type": None,
                "kernel_version": None,
                "architecture": None,
                "is_virtualized": None,
                "cores": None,
                "num_sockets": None,
                "num_virtual_guests": 1,
                "virtual": "hypervisor",
                "location": "Raleigh",
                "ip_addresses": ["192.168.99.123"],
                "mac_addresses": ["fe80::5054:ff:fe24:946e"],
                "os_name": "RedHat",
                "os_version": "7.4",
            }
            self.assertEqual(host_info, expected)

    def test_prepare_host_s61(self):
        """Test the prepare host method for satellite 6.1."""
        url1 = (
            "https://{sat_host}:{port}/katello/api"
            "/v2/organizations/{org_id}/systems/{host_id}"
        )
        url2 = (
            "https://{sat_host}:{port}/katello/api"
            "/v2/organizations/{org_id}/systems/{host_id}/subscriptions"
        )
        expected = [
            (
                self.scan_task,
                {
                    "job_id": self.scan_job.id,
                    "task_sequence_number": self.scan_task.sequence_number,
                    "scan_type": self.scan_task.scan_type,
                    "source_type": self.scan_task.source.source_type,
                    "source_name": self.scan_task.source.name,
                },
                1,
                "sys",
                url1,
                url2,
                {
                    "host": {"id": 1, "name": "sys"},
                    "port": "443",
                    "user": self.cred.username,
                    "password": self.cred.password,
                    "ssl_cert_verify": True,
                },
            )
        ]
        host = {"id": 1, "name": "sys"}
        chunk = [host]
        port = "443"
        user = self.cred.username
        password = self.cred.password
        connect_data_return_value = host, port, user, password
        with patch(
            "scanner.satellite.utils.get_connect_data",
            return_value=connect_data_return_value,
        ) as mock_connect:
            host_params = SatelliteSixV1.prepare_host(self.api, chunk)
            self.assertEqual(expected, host_params)
            mock_connect.assert_called_once_with(ANY)

    def test_request_host_details_err(self):
        """Test request_host_details for error mark a failed system."""
        host_field_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host="1.2.3.4", host_id=1)
            mocker.get(url, status_code=500)
            result = request_host_details(
                self.scan_task,
                {
                    "job_id": self.scan_job.id,
                    "task_sequence_number": self.scan_task.id,
                    "scan_type": self.scan_task.scan_type,
                    "source_type": self.scan_task.source.source_type,
                    "source_name": self.scan_task.source.name,
                },
                1,
                "sys",
                url,
                url,
                {},
            )

            expected = {
                "unique_name": "sys_1",
                "system_inspection_result": "failed",
                "host_fields_response": {},
                "host_subscriptions_response": {},
            }
            self.assertEqual(result, expected)
            inspect_result = self.scan_task.inspection_result
            self.assertEqual(len(inspect_result.systems.all()), 0)

    def test_post_processing(self):
        """Test process_results method with mock data."""
        fields_return_value = {
            "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
            "hostname": "mac52540071bafe.prov.lan",
            "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
            "registration_time": "2017-12-04 13:33:52 UTC",
            "last_checkin_time": "2018-01-04 17:36:07 UTC",
            "katello_agent_installed": False,
            "os_name": "RedHat 7.4",
            "organization": "ACME",
            "virtual_host_uuid": "100",
            "virtual_host_name": "vhost1",
            "virt_type": None,
            "kernel_version": None,
            "architecture": None,
            "is_virtualized": None,
            "cores": None,
            "num_sockets": None,
            "num_virtual_guests": 1,
            "virtual": "hypervisor",
            "location": "Raleigh",
            "ip_addresses": ["192.168.99.123"],
            "ipv6_addresses": ["fe80::5054:ff:fe24:946e"],
        }
        subs_return_value = {
            "entitlements": [
                {
                    "derived_entitlement": False,
                    "name": "Satellite Tools 6.3",
                    "amount": 1,
                    "account_number": None,
                    "contract_number": None,
                    "start_date": "2017-12-01 14:50:59 UTC",
                    "end_date": "2047-11-24 14:50:59 UTC",
                },
                {
                    "derived_entitlement": True,
                    "name": "Employee SKU",
                    "amount": 1,
                    "account_number": 1212729,
                    "contract_number": 10913844,
                    "start_date": "2016-03-24 04:00:00 UTC",
                    "end_date": "2022-01-01 04:59:59 UTC",
                },
            ]
        }
        expected = {
            "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
            "hostname": "mac52540071bafe.prov.lan",
            "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
            "registration_time": "2017-12-04 13:33:52 UTC",
            "last_checkin_time": "2018-01-04 17:36:07 UTC",
            "katello_agent_installed": False,
            "os_name": "RedHat 7.4",
            "organization": "ACME",
            "virtual_host_uuid": "100",
            "virtual_host_name": "vhost1",
            "num_virtual_guests": 1,
            "virtual": "hypervisor",
            "location": "Raleigh",
            "ip_addresses": ["192.168.99.123"],
            "ipv6_addresses": ["fe80::5054:ff:fe24:946e"],
            "entitlements": [
                {
                    "derived_entitlement": False,
                    "name": "Satellite Tools 6.3",
                    "amount": 1,
                    "account_number": None,
                    "contract_number": None,
                    "start_date": "2017-12-01 14:50:59 UTC",
                    "end_date": "2047-11-24 14:50:59 UTC",
                },
                {
                    "derived_entitlement": True,
                    "name": "Employee SKU",
                    "amount": 1,
                    "account_number": 1212729,
                    "contract_number": 10913844,
                    "start_date": "2016-03-24 04:00:00 UTC",
                    "end_date": "2022-01-01 04:59:59 UTC",
                },
            ],
        }

        self.scan_task.save()
        self.scan_task.update_stats("TEST_SAT.", sys_scanned=0)
        with patch(
            "scanner.satellite.six.host_fields", return_value=fields_return_value
        ) as mock_fields:
            with patch(
                "scanner.satellite.six.host_subscriptions",
                return_value=subs_return_value,
            ) as mock_subs:
                result = {
                    "unique_name": "sys_1",
                    "system_inspection_result": SystemInspectionResult.SUCCESS,
                    "host_fields_response": fields_return_value,
                    "host_subscriptions_response": subs_return_value,
                }
                process_results(self.api, [result], 1)
                inspect_results = self.scan_task.inspection_result.systems.all()
                sys_1_result = inspect_results.filter(name="sys_1").first()
                self.assertEqual(sys_1_result.name, "sys_1")
                self.assertEqual(sys_1_result.status, "success")
                result = {}
                for fact in sys_1_result.facts.all():
                    result[fact.name] = fact.value
                self.assertEqual(result, expected)
                mock_fields.assert_called_once_with(ANY, ANY)
                mock_subs.assert_called_once_with(ANY)

    @patch("scanner.satellite.six.SatelliteSixV1.get_orgs")
    def test_hosts_facts_with_err(self, mock_get_orgs):
        """Test the hosts_facts method."""
        mock_get_orgs.return_value = [1]
        hosts_url = (
            "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
        )
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            mocker.get(url, status_code=500)
            with self.assertRaises(SatelliteException):
                self.api.hosts_facts(Value("i", ScanJob.JOB_RUN))

    @patch(
        "multiprocessing.pool.Pool.starmap",
        return_value=[
            {
                "unique_name": "sys_1",
                "system_inspection_result": "failed",
                "host_fields_response": {},
                "host_subscriptions_response": {},
            }
        ],
    )
    def test_hosts_facts(self, mock_pool):
        """Test the method hosts."""
        hosts_url = (
            "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
        )
        with patch.object(SatelliteSixV1, "get_orgs", return_value=[1]):
            with patch("scanner.satellite.six.request_host_details", return_value={}):
                with requests_mock.Mocker() as mocker:
                    url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
                    jsonresult = {
                        "results": [
                            {"uuid": "1", "name": "sys1"},
                            {"uuid": "2", "name": "sys2"},
                            {"uuid": "3", "name": "sys3"},
                        ],
                        "per_page": 100,
                        "total": 3,
                    }
                    mocker.get(url, status_code=200, json=jsonresult)
                    self.api.hosts_facts(Value("i", ScanJob.JOB_RUN))
                    inspect_result = self.scan_task.inspection_result
                    self.assertEqual(len(inspect_result.systems.all()), 1)


# pylint: disable=too-many-instance-attributes
class SatelliteSixV2Test(TestCase):
    """Tests Satellite 6 v2 functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            cred_type=DataSources.SATELLITE,
            username="username",
            password="password",
            become_password=None,
            become_method=None,
            become_user=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        self.source = Source(name="source1", port=443, hosts=["1.2.3.4"])

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT
        )
        self.scan_task.update_stats("TEST_SAT.", sys_scanned=0)
        self.api = SatelliteSixV2(self.scan_job, self.scan_task)
        job_conn_result = JobConnectionResult()
        job_conn_result.save()
        connection_results = TaskConnectionResult(job_connection_result=job_conn_result)
        connection_results.save()
        self.api.connect_scan_task.connection_result = connection_results
        self.api.connect_scan_task.connection_result.save()

        conn_result = self.api.connect_scan_task.connection_result
        sys_result = SystemConnectionResult(
            name="sys1_1",
            status=SystemInspectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        self.api.connect_scan_task.save()

    def tearDown(self):
        """Cleanup test case setup."""

    def test_host_count(self):
        """Test the method host_count."""
        hosts_url = "https://{sat_host}:{port}/api/v2/hosts"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [{"name": "sys1"}, {"name": "sys2"}, {"name": "sys3"}],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            self.assertEqual(systems_count, 3)

    def test_host_count_with_err(self):
        """Test the method host_count with error."""
        hosts_url = "https://{sat_host}:{port}/api/v2/hosts"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [{"name": "sys1"}, {"name": "sys2"}, {"name": "sys3"}],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.host_count()

    def test_hosts(self):
        """Test the method hosts."""
        hosts_url = "https://{sat_host}:{port}/api/v2/hosts"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [
                    {"name": "sys1", "id": 1},
                    {"name": "sys2", "id": 2},
                    {"name": "sys3", "id": 3},
                ],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            hosts = self.api.hosts()
            self.assertEqual(systems_count, 3)
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ["sys1_1", "sys2_2", "sys3_3"])

    def test_hosts_with_err(self):
        """Test the method hosts with error."""
        hosts_url = "https://{sat_host}:{port}/api/v2/hosts"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4", org_id=1)
            jsonresult = {
                "results": [{"name": "sys1"}, {"name": "sys2"}, {"name": "sys3"}],
                "per_page": 100,
                "total": 3,
            }
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.hosts()

    def test_processing_fields_with_err(self):
        """Test the post_processing with error."""
        host_field_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host="1.2.3.4", host_id=1)
            mocker.get(url, status_code=500)
            result = request_host_details(
                self.scan_task,
                {
                    "job_id": self.scan_job.id,
                    "task_sequence_number": self.scan_task.id,
                    "scan_type": self.scan_task.scan_type,
                    "source_type": self.scan_task.source.source_type,
                    "source_name": self.scan_task.source.name,
                },
                1,
                "sys",
                url,
                url,
                {},
            )
            expected = {
                "unique_name": "sys_1",
                "system_inspection_result": "failed",
                "host_fields_response": {},
                "host_subscriptions_response": {},
            }
            self.assertEqual(result, expected)
            process_results(self.api, [result], 1)
            inspect_results = self.scan_task.inspection_result.systems.all()
            sys_1_result = inspect_results.filter(name="sys_1").first()
            self.assertEqual(sys_1_result.name, "sys_1")
            self.assertEqual(sys_1_result.status, "failed")

    def test_host_fields(self):
        """Test the method host_fields."""
        host_field_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=host_field_url, sat_host="1.2.3.4", host_id=1)
            jsonresult = {
                "architecture_id": 1,
                "architecture_name": "x86_64",
                "operatingsystem_name": "RedHat 7.4",
                "uuid": None,
                "created_at": "2017-12-04 13:19:57 UTC",
                "updated_at": "2017-12-04 13:21:47 UTC",
                "organization_name": "ACME",
                "location_name": "Raleigh",
                "name": "mac52540071bafe.prov.lan",
                "virtual_host": {"uuid": "100", "name": "vhost1"},
                "virtual_guests": [{"name": "foo"}],
                "content_facet_attributes": {
                    "id": 11,
                    "katello_agent_installed": False,
                },
                "subscription_facet_attributes": {
                    "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
                    "last_checkin": "2018-01-04 17:36:07 UTC",
                    "registered_at": "2017-12-04 13:33:52 UTC",
                    "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
                    "virtual_host": {"uuid": "100", "name": "vhost1"},
                    "virtual_guests": [{"name": "foo"}],
                },
                "facts": {
                    "memorysize_mb": "992.45",
                    "memorysize": "992.45 MB",
                    "hostname": "fdi",
                    "type": "Other",
                    "architecture": "x86_64",
                    "is_virtual": "true",
                    "virtual": "kvm",
                    "net::interface::ipv4_address": "192.168.99.123",
                    "net::interface::mac_address": "fe80::5054:ff:fe24:946e",
                },
            }
            mocker.get(url, status_code=200, json=jsonresult)
            host_info = host_fields(2, jsonresult)
            expected = {
                "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
                "hostname": "mac52540071bafe.prov.lan",
                "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
                "registration_time": "2017-12-04 13:33:52 UTC",
                "last_checkin_time": "2018-01-04 17:36:07 UTC",
                "katello_agent_installed": False,
                "os_release": "RedHat 7.4",
                "organization": "ACME",
                "virtual_host_uuid": "100",
                "virtual_host_name": "vhost1",
                "virt_type": None,
                "kernel_version": None,
                "architecture": None,
                "is_virtualized": None,
                "cores": None,
                "num_sockets": None,
                "num_virtual_guests": 1,
                "virtual": "hypervisor",
                "location": "Raleigh",
                "ip_addresses": ["192.168.99.123"],
                "mac_addresses": ["fe80::5054:ff:fe24:946e"],
                "os_name": "RedHat",
                "os_version": "7.4",
            }
            self.assertEqual(host_info, expected)

    def test_get_https_with_err(self):
        """Test the host subscriptons method with bad status code."""
        sub_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}/subscriptions"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host="1.2.3.4", host_id=1)
            mocker.get(url, status_code=500)
            result = request_host_details(
                self.scan_task,
                {
                    "job_id": self.scan_job.id,
                    "task_sequence_number": self.scan_task.id,
                    "scan_type": self.scan_task.scan_type,
                    "source_type": self.scan_task.source.source_type,
                    "source_name": self.scan_task.source.name,
                },
                1,
                "sys",
                url,
                url,
                {},
            )

            expected = {
                "unique_name": "sys_1",
                "system_inspection_result": "failed",
                "host_fields_response": {},
                "host_subscriptions_response": {},
            }
            self.assertEqual(result, expected)

    def test_processing_subs_err_nojson(self):
        """Test the flow of post processing with bad code and not json."""
        sub_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}/subscriptions"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host="1.2.3.4", host_id=1)
            mocker.get(url, status_code=404, text="error message")
            result = request_host_details(
                self.scan_task,
                {
                    "job_id": self.scan_job.id,
                    "task_sequence_number": self.scan_task.id,
                    "scan_type": self.scan_task.scan_type,
                    "source_type": self.scan_task.source.source_type,
                    "source_name": self.scan_task.source.name,
                },
                1,
                "sys",
                url,
                url,
                {},
            )

            process_results(self.api, [result], 1)
            inspect_results = self.scan_task.inspection_result.systems.all()
            sys_1_result = inspect_results.filter(name="sys_1").first()
            self.assertEqual(sys_1_result.name, "sys_1")
            self.assertEqual(sys_1_result.status, "failed")

    def test_host_not_subscribed(self):
        """Test the host subscriptons method for not subscribed error."""
        sub_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}/subscriptions"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host="1.2.3.4", host_id=1)
            err_msg = {
                "displayMessage": "Host has not been registered "
                "with subscription-manager",
                "errors": ["Host has not been registered with subscription-manager"],
            }
            mocker.get(url, status_code=400, json=err_msg)
            result = request_host_details(
                self.scan_task,
                {
                    "job_id": self.scan_job.id,
                    "task_sequence_number": self.scan_task.id,
                    "scan_type": self.scan_task.scan_type,
                    "source_type": self.scan_task.source.source_type,
                    "source_name": self.scan_task.source.name,
                },
                1,
                "sys",
                url,
                url,
                {},
            )

        process_results(self.api, [result], 1)
        inspect_results = self.scan_task.inspection_result.systems.all()
        sys_1_result = inspect_results.filter(name="sys_1").first()
        self.assertEqual(sys_1_result.name, "sys_1")
        self.assertEqual(sys_1_result.status, "failed")

    def test_host_subscriptons(self):
        """Test the host subscriptons method."""
        sub_url = "https://{sat_host}:{port}/api/v2/hosts/{host_id}/subscriptions"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=sub_url, sat_host="1.2.3.4", host_id=1)
            jsonresult = {
                "results": [
                    {
                        "amount": 1,
                        "name": "Satellite Tools 6.3",
                        "start_date": "2017-12-01 14:50:59 UTC",
                        "end_date": "2047-11-24 14:50:59 UTC",
                        "product_name": "Satellite Tools 6.3",
                    },
                    {
                        "quantity_consumed": 1,
                        "name": "Employee SKU",
                        "start_date": "2016-03-24 04:00:00 UTC",
                        "end_date": "2022-01-01 04:59:59 UTC",
                        "account_number": 1212729,
                        "contract_number": 10913844,
                        "type": "ENTITLEMENT_DERIVED",
                        "product_name": "Employee SKU",
                    },
                ]
            }
            mocker.get(url, status_code=200, json=jsonresult)
            subs = host_subscriptions(jsonresult)
            expected = {
                "entitlements": [
                    {
                        "derived_entitlement": False,
                        "name": "Satellite Tools 6.3",
                        "amount": 1,
                        "account_number": None,
                        "contract_number": None,
                        "start_date": "2017-12-01 14:50:59 UTC",
                        "end_date": "2047-11-24 14:50:59 UTC",
                    },
                    {
                        "derived_entitlement": True,
                        "name": "Employee SKU",
                        "amount": 1,
                        "account_number": 1212729,
                        "contract_number": 10913844,
                        "start_date": "2016-03-24 04:00:00 UTC",
                        "end_date": "2022-01-01 04:59:59 UTC",
                    },
                ]
            }
            self.assertEqual(subs, expected)

    def test_post_processing_err(self):
        """Test error flow & check that a failed system is marked."""
        response = {
            "unique_name": "sys_1",
            "system_inspection_result": SystemInspectionResult.FAILED,
            "host_fields_response": {},
            "host_subscriptions_response": {},
        }
        process_results(self.api, [response], 1)
        inspect_results = self.scan_task.inspection_result.systems.all()
        sys_1_result = inspect_results.filter(name="sys_1").first()
        self.assertEqual(sys_1_result.name, "sys_1")
        self.assertEqual(sys_1_result.status, "failed")

    def test_post_processing(self):
        """Test process_results method with mock data."""
        fields_return_value = {
            "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
            "hostname": "mac52540071bafe.prov.lan",
            "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
            "registration_time": "2017-12-04 13:33:52 UTC",
            "last_checkin_time": "2018-01-04 17:36:07 UTC",
            "katello_agent_installed": False,
            "os_name": "RedHat 7.4",
            "organization": "ACME",
            "virtual_host_uuid": "100",
            "virtual_host_name": "vhost1",
            "virt_type": None,
            "kernel_version": None,
            "architecture": None,
            "is_virtualized": None,
            "cores": None,
            "num_sockets": None,
            "num_virtual_guests": 1,
            "virtual": "hypervisor",
            "location": "Raleigh",
            "ip_addresses": ["192.168.99.123"],
            "ipv6_addresses": ["fe80::5054:ff:fe24:946e"],
        }
        subs_return_value = {
            "entitlements": [
                {
                    "derived_entitlement": False,
                    "name": "Satellite Tools 6.3",
                    "amount": 1,
                    "account_number": None,
                    "contract_number": None,
                    "start_date": "2017-12-01 14:50:59 UTC",
                    "end_date": "2047-11-24 14:50:59 UTC",
                },
                {
                    "derived_entitlement": True,
                    "name": "Employee SKU",
                    "amount": 1,
                    "account_number": 1212729,
                    "contract_number": 10913844,
                    "start_date": "2016-03-24 04:00:00 UTC",
                    "end_date": "2022-01-01 04:59:59 UTC",
                },
            ]
        }
        expected = {
            "uuid": "00c7a108-48ec-4a97-835c-aa3369777f64",
            "hostname": "mac52540071bafe.prov.lan",
            "registered_by": "sat-r220-07.lab.eng.rdu2.redhat.com",
            "registration_time": "2017-12-04 13:33:52 UTC",
            "last_checkin_time": "2018-01-04 17:36:07 UTC",
            "katello_agent_installed": False,
            "os_name": "RedHat 7.4",
            "organization": "ACME",
            "virtual_host_uuid": "100",
            "virtual_host_name": "vhost1",
            "num_virtual_guests": 1,
            "virtual": "hypervisor",
            "location": "Raleigh",
            "ip_addresses": ["192.168.99.123"],
            "ipv6_addresses": ["fe80::5054:ff:fe24:946e"],
            "entitlements": [
                {
                    "derived_entitlement": False,
                    "name": "Satellite Tools 6.3",
                    "amount": 1,
                    "account_number": None,
                    "contract_number": None,
                    "start_date": "2017-12-01 14:50:59 UTC",
                    "end_date": "2047-11-24 14:50:59 UTC",
                },
                {
                    "derived_entitlement": True,
                    "name": "Employee SKU",
                    "amount": 1,
                    "account_number": 1212729,
                    "contract_number": 10913844,
                    "start_date": "2016-03-24 04:00:00 UTC",
                    "end_date": "2022-01-01 04:59:59 UTC",
                },
            ],
        }
        with patch(
            "scanner.satellite.six.host_fields", return_value=fields_return_value
        ) as mock_fields:
            with patch(
                "scanner.satellite.six.host_subscriptions",
                return_value=subs_return_value,
            ) as mock_subs:
                result = {
                    "unique_name": "sys_1",
                    "system_inspection_result": SystemInspectionResult.SUCCESS,
                    "host_fields_response": fields_return_value,
                    "host_subscriptions_response": subs_return_value,
                }
                process_results(self.api, [result], 1)
                inspect_results = self.scan_task.inspection_result.systems.all()
                sys_1_result = inspect_results.filter(name="sys_1").first()
                self.assertEqual(sys_1_result.name, "sys_1")
                self.assertEqual(sys_1_result.status, "success")
                result = {}
                for fact in sys_1_result.facts.all():
                    result[fact.name] = fact.value
                self.assertEqual(result, expected)
                mock_fields.assert_called_once_with(ANY, ANY)
                mock_subs.assert_called_once_with(ANY)
                mock_fields.assert_called_once_with(ANY, ANY)
                mock_subs.assert_called_once_with(ANY)

    def test_hosts_facts_with_err(self):
        """Test the hosts_facts method."""
        hosts_url = "https://{sat_host}:{port}/api/v2/hosts"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4")
            mocker.get(url, status_code=500)
            with self.assertRaises(SatelliteException):
                self.api.hosts_facts(Value("i", ScanJob.JOB_RUN))

    @patch(
        "multiprocessing.pool.Pool.starmap",
        return_value=[
            {
                "unique_name": "sys_1",
                "system_inspection_result": "success",
                "host_fields_response": {},
                "host_subscriptions_response": {},
            }
        ],
    )
    def test_hosts_facts(self, mock_pool):
        """Test the hosts_facts method."""
        scan_options = ScanOptions(max_concurrency=10)
        scan_options.save()
        scan_job, scan_task = create_scan_job(
            self.source,
            ScanTask.SCAN_TYPE_INSPECT,
            scan_name="test_62",
            scan_options=scan_options,
        )
        scan_task.update_stats("TEST_SAT.", sys_scanned=0)
        api = SatelliteSixV2(scan_job, scan_task)
        job_conn_result = JobConnectionResult()
        job_conn_result.save()
        connection_results = TaskConnectionResult(job_connection_result=job_conn_result)
        connection_results.save()
        api.connect_scan_task.connection_result = connection_results
        api.connect_scan_task.connection_result.save()

        sys_result = SystemConnectionResult(
            name="sys1_1",
            status=SystemInspectionResult.SUCCESS,
            task_connection_result=api.connect_scan_task.connection_result,
        )
        sys_result.save()
        api.connect_scan_task.save()
        hosts_url = "https://{sat_host}:{port}/api/v2/hosts"
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host="1.2.3.4")
            jsonresult = {
                "total": 1,
                "subtotal": 1,
                "page": 1,
                "per_page": 100,
                "results": [{"id": 10, "name": "sys10"}],
            }
            mocker.get(url, status_code=200, json=jsonresult)
            api.hosts_facts(Value("i", ScanJob.JOB_RUN))
            inspect_result = scan_task.inspection_result
            self.assertEqual(len(inspect_result.systems.all()), 1)
