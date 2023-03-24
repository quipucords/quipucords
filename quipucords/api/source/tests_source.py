"""Test the API application."""

import json
from datetime import datetime
from unittest.mock import patch

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.serializers import ValidationError

from api import messages
from api.models import Credential, Scan, ScanTask, Source
from api.serializers import SourceSerializer
from api.source.view import format_source
from constants import DataSources
from scanner.test_util import create_scan_job


def dummy_start():
    """Create a dummy method for testing."""


# pylint: disable=too-many-instance-attributes,invalid-name,R0904,C0302
class SourceTest(TestCase):
    """Test the basic Source infrastructure."""

    def setUp(self):
        """Create test case setup."""
        management.call_command("flush", "--no-input")
        self.net_cred = Credential.objects.create(
            name="net_cred1",
            cred_type=DataSources.NETWORK,
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.net_cred_for_upload = self.net_cred.id
        self.net_cred_for_response = {
            "id": self.net_cred.id,
            "name": self.net_cred.name,
        }

        self.vc_cred = Credential.objects.create(
            name="vc_cred1",
            cred_type=DataSources.VCENTER,
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.vc_cred_for_upload = self.vc_cred.id
        self.vc_cred_for_response = {"id": self.vc_cred.id, "name": self.vc_cred.name}

        self.sat_cred = Credential.objects.create(
            name="sat_cred1",
            cred_type=DataSources.SATELLITE,
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.sat_cred_for_upload = self.sat_cred.id
        self.sat_cred_for_response = {
            "id": self.sat_cred.id,
            "name": self.sat_cred.name,
        }

        self.openshift_cred = Credential.objects.create(
            name="openshift_cred1",
            cred_type=DataSources.OPENSHIFT,
            auth_token="openshift_token",
        )
        self.openshift_cred_for_upload = self.openshift_cred.id

    def create(self, data):
        """Call the create endpoint."""
        url = reverse("source-list")
        return self.client.post(url, json.dumps(data), "application/json")

    def create_expect_400(self, data, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        if response.status_code != status.HTTP_201_CREATED:
            print("#" * 1200)
            print("Status code not 201.  See JSON response.")
            print(response.json())
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    # pylint: disable=unused-argument
    @patch("api.source.view.start_scan", side_effect=dummy_start)
    def create_with_query(self, query, data, start_scan):
        """Create a source with query param.

        :param query: The value of scan
        :param data: The payload of the source
        :return a dict containing the response
        """
        url = reverse("source-list")
        url += query
        return self.client.post(url, json.dumps(data), "application/json")

    # pylint: disable=no-value-for-parameter
    def create_expect_201_with_query(self, query, data):
        """Create a valid source with a scan parameter."""
        response = self.create_with_query(query, data)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    # pylint: disable=no-value-for-parameter
    def create_expect_400_with_query(self, query, data, expected_response=None):
        """Create an expect HTTP 400."""
        response = self.create_with_query(query, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    #################################################
    # Function Tests
    #################################################
    def test_validate_opts(self):
        """Test the validate_opts function."""
        source_type = DataSources.SATELLITE
        options = {"use_paramiko": True}
        with self.assertRaises(ValidationError):
            SourceSerializer.validate_opts(options, source_type)

        options = {}
        SourceSerializer.validate_opts(options, source_type)
        assert options["ssl_cert_verify"] is True

        source_type = DataSources.VCENTER
        options = {"use_paramiko": True}
        with self.assertRaises(ValidationError):
            SourceSerializer.validate_opts(options, source_type)

        options = {}
        SourceSerializer.validate_opts(options, source_type)
        assert options["ssl_cert_verify"] is True

        source_type = DataSources.NETWORK
        options = {"disable_ssl": True}
        with self.assertRaises(ValidationError):
            SourceSerializer.validate_opts(options, source_type)

    def test_format_source(self):
        """Test the format source method."""
        start = datetime.now()
        source = Source(
            name="source1",
            hosts=["1.2.3.4"],
            source_type="network",
            port=22,
        )
        source.save()
        end = datetime.now()
        scan_job, scan_task = create_scan_job(source)
        scan_task.update_stats(
            "", sys_count=10, sys_scanned=9, sys_failed=1, sys_unreachable=0
        )
        scan_job.start_time = start
        scan_job.end_time = end
        scan_job.status = ScanTask.COMPLETED
        scan_job.save()
        source.most_recent_connect_scan = scan_job
        source.save()

        serializer = SourceSerializer(source)
        json_source = serializer.data
        out = format_source(json_source)

        # pylint: disable=line-too-long
        expected = {
            "id": 1,
            "name": "source1",
            "source_type": "network",
            "port": 22,
            "hosts": ["1.2.3.4"],
            "connection": {
                "id": 1,
                "start_time": start,
                "end_time": end,
                "systems_count": 10,
                "systems_scanned": 9,
                "systems_failed": 1,
                "systems_unreachable": 0,
                "system_fingerprint_count": 0,
                "status_details": {"job_status_message": "Job is pending."},
                "status": "completed",
                "source_systems_count": 10,
                "source_systems_scanned": 9,
                "source_systems_failed": 1,
                "source_systems_unreachable": 0,
            },
        }
        assert out == expected

    #################################################
    # Network Tests
    #################################################

    # Note: hosts and exclude hosts lists use the same method to validate, so
    # invalid exclude host testing has not been included.

    def test_source_create_with_false_scan(self):
        """Test creating a source with a valid scan query param of False."""
        query = "?scan=False"
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        response = self.create_expect_201_with_query(query, data)
        assert "id" in response

    def test_source_create_with_true_scan(self):
        """Test creating source with valid scan query param of True."""
        query = "?scan=True"
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        self.create_expect_201_with_query(query, data)

    def test_source_create_with_invalid_scan(self):
        """Test the source create method with invalid query param."""
        query = "?scan=Foo"
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        self.create_expect_400_with_query(query, data)

    def test_successful_net_create(self):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        response = self.create_expect_201(data)
        assert "id" in response

    def test_successful_net_create_no_port(self):
        """A valid create request should succeed without port."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "credentials": [self.net_cred_for_upload],
        }
        response = self.create_expect_201(data)
        assert "id" in response

    def test_double_create(self):
        """A duplicate create should fail."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        response = self.create_expect_201(data)
        assert "id" in response
        self.create_expect_400(data)

    def test_create_multiple_hosts(self):
        """A valid create request with two hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        self.create_expect_201(data)

    def test_create_no_name(self):
        """A create request must have a name."""
        self.create_expect_400(
            {
                "hosts": "1.2.3.4",
                "source_type": DataSources.NETWORK,
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_invalid_name(self):
        """A create request must have a string name."""
        self.create_expect_400(
            {
                "name": 1,
                "hosts": "1.2.3.4",
                "source_type": DataSources.NETWORK,
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_unprintable_name(self):
        """The Source name must be printable."""
        self.create_expect_400(
            {
                "name": "\r\n",
                "source_type": DataSources.NETWORK,
                "hosts": "1.2.3.4",
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_no_host(self):
        """A Source needs a host."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_empty_host(self):
        """An empty string is not a host identifier."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": [],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_hosts_not_array(self):
        """Test error when hosts is not an array."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": {"1.2.3.4": "1.2.3.4"},
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_hosts_not_array_of_strings(self):
        """Test error when hosts is not an array of strings."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": [1, 2, 3, 4],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_long_name(self):
        """An long source name."""
        self.create_expect_400(
            {
                "name": "A" * 100,
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_negative_port(self):
        """An long source name."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": -1,
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_empty_ip(self):
        """An empty string passed with valid ips."""
        self.create_expect_201(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["10.10.181.9", ""],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_valid_hosts(self):
        """Test valid host patterns."""
        self.create_expect_201(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": [
                    "10.10.181.9",
                    "10.10.181.9/16",
                    "10.10.128.[1:25]",
                    "10.10.[1:20].25",
                    "10.10.[1:20].[1:25]",
                    "localhost",
                    "my_cool_underscore.com",
                    "mycentos.com",
                    "my_rhel[a:d].company.com",
                    "my_rhel[120:400].company.com",
                    "my-rhel[a:d].company.com",
                    "my-rhel[120:400].company.com",
                    "my-rh_el[120:400].comp_a-ny.com",
                ],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_valid_exclude_hosts(self):
        """Test valid exclude host patterns."""
        self.create_expect_201(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": [
                    "10.10.181.8",
                    "10.10.181.9",
                    "10.10.181.9/16",
                    "10.10.128.[1:25]",
                    "10.10.[1:20].25",
                    "10.10.[1:20].[1:25]",
                ],
                "exclude_hosts": [
                    "10.10.191.9",
                    "10.10.181.9/16",
                    "10.10.128.[1:25]",
                    "10.10.[1:20].25",
                    "10.10.[1:20].[1:25]",
                ],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_invalid_hosts(self):
        """Test invalid host patterns."""
        hosts = [
            "192.1..2",
            "192.01.5.10",
            "192.1.5.1/",
            "192.01.5.[1:10]/10",
            "192.3-32.56.100-254",
            "192.3.6-56.254",
            "192.3.56.0-254",
            "192.3.4.455",
            "192.3.4.455/16",
            "10.10.[181.9",
            "10.10.128.[a:25]",
            "10.10.[1-20].25",
            "1.1.1.1/33",
            "myrhel[a:400].company.com",
        ]

        response = self.create(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": hosts,
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )
        assert response.status_code == 400
        assert len(response.data["hosts"]) == len(hosts)

    def test_create_bad_host_pattern(self):
        """Test a invalid host pattern."""
        hosts = ["10.1.1.1-10.1.1.254"]

        response = self.create(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": hosts,
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )
        assert response.status_code == 400
        assert len(response.data["hosts"]) == len(hosts)

    def test_create_bad_port(self):
        """-1 is not a valid ssh port."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "-1",
                "credentials": [self.net_cred_for_upload],
            }
        )

    def test_create_no_credentials(self):
        """A Source needs credentials."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
            }
        )

    def test_create_empty_credentials(self):
        """The empty string is not a valid credential list."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [],
            }
        )

    def test_create_credential_does_not_exist(self):
        """A random int is not a valid credential id."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [42],
            }
        )

    def test_create_credential_not_valid_id(self):
        """A random int is not a valid credential id."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": ["hi"],
            }
        )

    def test_create_invalid_cred_type(self):
        """A source type and credential type must be the same."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.vc_cred_for_upload],
            }
        )

    def test_create_with_options_not_allowed_network_type(self):
        """Test network type doesn't allow ssl options."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.vc_cred_for_upload],
            "options": {"ssl_cert_verify": False},
        }
        self.create_expect_400(data)

    def test_list(self):
        """List all Source objects."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "hosts": ["1.2.3.4"],
            "credentials": [self.net_cred_for_upload],
        }
        for i in range(3):
            this_data = data.copy()
            this_data["name"] = "source" + str(i)
            self.create_expect_201(this_data)

        url = reverse("source-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        content = response.json()
        results1 = [
            {
                "id": 1,
                "name": "source0",
                "source_type": DataSources.NETWORK,
                "port": 22,
                "hosts": ["1.2.3.4"],
                "credentials": [self.net_cred_for_response],
            },
            {
                "id": 2,
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "port": 22,
                "hosts": ["1.2.3.4"],
                "credentials": [self.net_cred_for_response],
            },
            {
                "id": 3,
                "name": "source2",
                "source_type": DataSources.NETWORK,
                "port": 22,
                "hosts": ["1.2.3.4"],
                "credentials": [self.net_cred_for_response],
            },
        ]
        expected = {"count": 3, "next": None, "previous": None, "results": results1}
        assert content == expected

    def test_filter_by_type_list(self):
        """List all Source objects filtered by type."""
        data = {
            "name": "nsource",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [self.net_cred_for_upload],
            "hosts": ["1.2.3.4"],
        }
        for i in range(1, 3):
            this_data = data.copy()
            this_data["name"] = "nsource" + str(i)
            self.create_expect_201(this_data)

        data = {
            "name": "vsource",
            "source_type": DataSources.VCENTER,
            "credentials": [self.vc_cred_for_upload],
            "hosts": ["1.2.3.4"],
        }

        for i in range(3, 5):
            this_data = data.copy()
            this_data["name"] = "vsource" + str(i)
            self.create_expect_201(this_data)

        url = reverse("source-list")
        response = self.client.get(url, {"source_type": DataSources.VCENTER})
        assert response.status_code == status.HTTP_200_OK

        content = response.json()
        results1 = [
            {
                "id": 3,
                "name": "vsource3",
                "source_type": "vcenter",
                "port": 443,
                "hosts": ["1.2.3.4"],
                "options": {
                    "ssl_cert_verify": True,
                },
                "credentials": [{"id": 2, "name": "vc_cred1"}],
            },
            {
                "id": 4,
                "name": "vsource4",
                "source_type": "vcenter",
                "port": 443,
                "hosts": ["1.2.3.4"],
                "options": {
                    "ssl_cert_verify": True,
                },
                "credentials": [{"id": 2, "name": "vc_cred1"}],
            },
        ]
        expected = {"count": 2, "next": None, "previous": None, "results": results1}
        assert content == expected

    def test_retrieve(self):
        """Get details on a specific Source by primary key."""
        initial = self.create_expect_201(
            {
                "name": "source1",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "exclude_hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert "credentials" in response_json
        creds = response_json["credentials"]

        assert creds == [self.net_cred_for_response]
        assert "hosts" in response_json
        assert response_json["hosts"][0] == "1.2.3.4"
        assert response_json["exclude_hosts"][0] == "1.2.3.4"

    def test_retrieve_bad_id(self):
        """Get details on a specific Source by bad primary key."""
        url = reverse("source-detail", args=("string",))
        response = self.client.get(url, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # We don't have to test that update validates fields correctly
    # because the validation code is shared between create and update.
    def test_update(self):
        """Completely update a Source."""
        initial = self.create_expect_201(
            {
                "name": "source2",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source2",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [self.net_cred.id],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        expected = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [self.net_cred_for_response],
        }
        # data should be a strict subset of the response, because the
        # response adds an id field.
        for key, value in expected.items():
            assert value == response.json()[key]

    def test_update_collide(self):
        """Fail update due to name conflict."""
        self.create_expect_201(
            {
                "name": "source2-double",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        initial = self.create_expect_201(
            {
                "name": "source2",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source2-double",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [self.net_cred.id],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_missing_hosts(self):
        """Partial update should succeed with missing hosts."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {"name": "source", "port": 22, "credentials": [self.net_cred_for_upload]}
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.patch(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_partial_update_network_ssl_options_not_allowed(self):
        """Partial update should succeed with missing hosts."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "port": 22,
            "credentials": [self.net_cred_for_upload],
            "options": {"ssl_cert_verify": False},
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.patch(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_no_hosts_retains_initial_host(self):
        """Partial update should keep initial host if no host provided."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {"name": "source", "port": 22, "credentials": [self.net_cred_for_upload]}
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.patch(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        expected = ["1.2.3.4"]
        assert response.data["hosts"] == expected

    def test_partial_update_empty_hosts(self):
        """Partial update should succeed with missing hosts."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "port": 22,
            "hosts": [],
            "credentials": [self.net_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.patch(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_missing_hosts(self):
        """Fail update due to missing host array."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {"name": "source", "port": 22, "credentials": [self.net_cred_for_upload]}
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_empty_hosts(self):
        """Fail update due to empty host array."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": [],
            "port": 22,
            "credentials": [self.net_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json_rsp = response.json()
        assert json_rsp["hosts"][0] == messages.SOURCE_HOSTS_CANNOT_BE_EMPTY

    def test_update_type_passed(self):
        """Fail update due to type passed."""
        initial = self.create_expect_201(
            {
                "name": "source2",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [self.net_cred.id],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_bad_cred_type(self):
        """Fail update due to bad cred type."""
        initial = self.create_expect_201(
            {
                "name": "source2",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [self.vc_cred.id],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update(self):
        """Partially update a Source."""
        initial = self.create_expect_201(
            {
                "name": "source3",
                "source_type": DataSources.NETWORK,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.net_cred_for_upload],
            }
        )

        data = {"name": "source3-new", "hosts": ["1.2.3.5"]}
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.patch(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "source3-new"
        assert response.json()["hosts"] == ["1.2.3.5"]

    def test_delete(self):
        """Delete a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [self.net_cred_for_upload],
        }
        response = self.create_expect_201(data)

        url = reverse("source-detail", args=(response["id"],))
        response = self.client.delete(url, format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_with_scans(self):
        """Delete a Source used by a scan."""
        cred = Credential(name="cred2", username="user2", password="pass2")
        cred.save()
        source = Source(
            name="cred_source",
            source_type=DataSources.NETWORK,
            hosts=["1.2.3.4"],
        )
        source.save()
        source.credentials.add(cred)
        source.save()

        scan = Scan(name="test_scan", scan_type=ScanTask.SCAN_TYPE_CONNECT)
        scan.save()
        scan.sources.add(source)

        url = reverse("source-detail", args=(source.id,))
        response = self.client.delete(url, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["detail"] == messages.SOURCE_DELETE_NOT_VALID_W_SCANS
        assert response_json["scans"][0]["name"] == "test_scan"

    #################################################
    # VCenter Tests
    #################################################
    def test_successful_vc_create(self):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [self.vc_cred_for_upload],
        }
        response = self.create_expect_201(data)
        assert "id" in response

    def test_create_too_many_creds(self):
        """A vcenter source and have one credential."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "credentials": [self.vc_cred_for_upload, self.net_cred_for_upload],
            }
        )

    def test_create_req_host(self):
        """A vcenter source must have a host."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.VCENTER,
                "credentials": [self.vc_cred_for_upload],
            }
        )

    def test_create_empty_hosts(self):
        """A vcenter source not have empty hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.VCENTER,
                "hosts": [],
                "credentials": [self.vc_cred_for_upload],
            }
        )

    def test_create_vc_with_hosts(self):
        """A vcenter source must not have multiple hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4", "1.2.3.5"],
                "credentials": [self.vc_cred_for_upload],
            }
        )

    def test_create_vc_with_excluded_hosts(self):
        """A vcenter source must not have any excluded hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "exclude_hosts": ["1.2.3.4"],
                "credentials": [self.vc_cred_for_upload],
            }
        )

    def test_create_vc_with_host_range(self):
        """A vcenter source must not have multiple hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4/5"],
                "credentials": [self.vc_cred_for_upload],
            }
        )

    def test_update_vc_greenpath(self):
        """VC - Success full update."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.vc_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.vc_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_vc_more_than_one_host(self):
        """VC - Fail more than one host."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.vc_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [self.vc_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_with_exclude_host(self):
        """VC - Fail when excluded hosts are provided."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.vc_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.vc_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_more_than_one_cred(self):
        """VC - Fail more than one cred."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.vc_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.vc_cred_for_upload, self.vc_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_range_hosts(self):
        """Fail update due to empty host array."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.VCENTER,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.vc_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [self.vc_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json_rsp = response.json()
        assert json_rsp["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_create_req_type(self):
        """A vcenter source must have an type."""
        self.create_expect_400(
            {
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [self.vc_cred_for_upload],
            }
        )

    #################################################
    # Satellite Tests
    #################################################
    def test_successful_sat_create(self):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [self.sat_cred_for_upload],
        }
        response = self.create_expect_201(data)
        assert "id" in response

    def test_successful_sat_create_with_options(self):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [self.sat_cred_for_upload],
            "options": {"ssl_cert_verify": False},
        }
        response = self.create_expect_201(data)
        assert "id" in response

    def test_sat_too_many_creds(self):
        """A sat source and have one credential."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "credentials": [self.sat_cred_for_upload, self.net_cred_for_upload],
            }
        )

    def test_sat_req_host(self):
        """A satellite source must have a host."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.SATELLITE,
                "credentials": [self.sat_cred_for_upload],
            }
        )

    def test_sat_req_empty_hosts(self):
        """A satellite source must not have empty hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.SATELLITE,
                "hosts": [],
                "credentials": [self.sat_cred_for_upload],
            }
        )

    def test_create_sat_with_hosts(self):
        """A satellite source must not have multiple hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4", "1.2.3.5"],
                "credentials": [self.sat_cred_for_upload],
            }
        )

    def test_create_sat_with_exclude_hosts(self):
        """A satellite source does not accept excluded hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "exclude_hosts": ["1.2.3.4"],
                "credentials": [self.sat_cred_for_upload],
            }
        )

    def test_create_sat_with_host_range(self):
        """A satellite source must not have multiple hosts."""
        self.create_expect_400(
            {
                "name": "source1",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4/5"],
                "credentials": [self.sat_cred_for_upload],
            }
        )

    def test_update_sat_greenpath(self):
        """Sat - Valid full update."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.sat_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.sat_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_sat_with_options(self):
        """Sat - Valid full update with options."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.sat_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.sat_cred_for_upload],
            "options": {"ssl_cert_verify": False},
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        expected = {
            "id": 1,
            "name": "source",
            "source_type": "satellite",
            "port": 22,
            "hosts": ["1.2.3.4"],
            "options": {"ssl_cert_verify": False},
            "credentials": [{"id": 3, "name": "sat_cred1"}],
        }
        assert response.json() == expected

    def test_update_sat_more_than_one_hosts(self):
        """Sat- Fail update due to multiple hosts."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.sat_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [self.sat_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_exclude_hosts(self):
        """Sat- Fail update due to including excluded hosts."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.sat_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.sat_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_than_one_cred(self):
        """Sat- Fail update due to multiple hosts."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.sat_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [self.sat_cred_for_upload, self.sat_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_range_hosts(self):
        """Fail update due to invalid host array."""
        initial = self.create_expect_201(
            {
                "name": "source",
                "source_type": DataSources.SATELLITE,
                "hosts": ["1.2.3.4"],
                "port": "22",
                "credentials": [self.sat_cred_for_upload],
            }
        )

        data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [self.sat_cred_for_upload],
        }
        url = reverse("source-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json_rsp = response.json()
        assert json_rsp["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_openshift_source_create(self):
        """Ensure we can create a new openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [self.openshift_cred_for_upload],
        }
        self.create_expect_201(data)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "openshift_source_1"

    def test_openshift_missing_host(self):
        """Ensure hosts field is required when creating openshift credential."""
        url = reverse("source-list")
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "credentials": [self.openshift_cred_for_upload],
        }
        response = self.client.post(url, json.dumps(data), "application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["hosts"]

    def test_openshift_extra_unallowed_fields(self):
        """Ensure unallowed fields are not accepted when creating openshift source."""
        url = reverse("source-list")
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [self.openshift_cred_for_upload],
            "options": {"use_paramiko": True},
        }
        response = self.client.post(url, json.dumps(data), "application/json")
        assert response.status_code, status.HTTP_400_BAD_REQUEST
        assert response.data["options"]

    def test_update_openshift_green_path(self):
        """Fail update due to invalid host array."""
        source_to_be_updated = self.create_expect_201(
            {
                "name": "openshift_source_1",
                "source_type": DataSources.OPENSHIFT,
                "hosts": ["1.2.3.4"],
                "credentials": [self.openshift_cred_for_upload],
            }
        )
        data = {
            "name": "openshift_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [self.openshift_cred_for_upload],
        }

        url = reverse("source-detail", args=(source_to_be_updated["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_openshift_range_hosts(self):
        """Fail update due to invalid host array."""
        source_to_be_updated = self.create_expect_201(
            {
                "name": "openshift_source_1",
                "source_type": DataSources.OPENSHIFT,
                "hosts": ["1.2.3.4"],
                "credentials": [self.openshift_cred_for_upload],
            }
        )

        data = {
            "name": "openshift_source_1",
            "hosts": ["1.2.3.4/5"],
            "credentials": [self.openshift_cred_for_upload],
        }
        url = reverse("source-detail", args=(source_to_be_updated["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = response.json()
        assert response["hosts"][0] == messages.SOURCE_ONE_HOST
