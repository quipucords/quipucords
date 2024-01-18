"""Test the API application."""

from datetime import datetime
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError

from api import messages
from api.models import Credential, Scan, ScanTask, Source
from api.serializers import SourceSerializer
from api.source.view import format_source
from constants import DataSources
from tests.scanner.test_util import create_scan_job

ACCEPT_JSON_HEADER = {"Accept": "application/json"}


@pytest.fixture
def net_cred():
    """Return network credential object."""
    return Credential.objects.create(
        name="net_cred1",
        cred_type=DataSources.NETWORK,
        username="username",
        password="password",
        become_password=None,
        ssh_keyfile=None,
    )


@pytest.fixture
def vc_cred():
    """Return vcenter credential object."""
    return Credential.objects.create(
        name="vc_cred1",
        cred_type=DataSources.VCENTER,
        username="username",
        password="password",
        become_password=None,
        ssh_keyfile=None,
    )


@pytest.fixture
def sat_cred():
    """Return satellite credential object."""
    return Credential.objects.create(
        name="sat_cred1",
        cred_type=DataSources.SATELLITE,
        username="username",
        password="password",
        become_password=None,
        ssh_keyfile=None,
    )


@pytest.fixture
def openshift_cred():
    """Return OCP credential object."""
    return Credential.objects.create(
        name="openshift_cred1",
        cred_type=DataSources.OPENSHIFT,
        auth_token="openshift_token",
    )


@pytest.fixture
def rhacs_cred():
    """Return RHACS credential object."""
    return Credential.objects.create(
        name="acs_cred1",
        cred_type=DataSources.RHACS,
        auth_token="acs_token",
    )


@pytest.fixture
def dummy_start():
    """Create a dummy method for testing."""


@pytest.mark.django_db
class TestSource:
    """Test the basic Source infrastructure."""

    def create(self, data, django_client):
        """Call the create endpoint."""
        url = reverse("v1:source-list")
        return django_client.post(url, json=data, headers=ACCEPT_JSON_HEADER)

    def create_expect_400(self, data, django_client, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data, django_client)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def create_expect_201(self, data, django_client):
        """Create a source, return the response as a dict."""
        response = self.create(data, django_client)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    @patch("api.source.view.start_scan", side_effect=dummy_start)
    def create_with_query(self, query, data, django_client, start_scan):
        """Create a source with query param, return the response as a dict."""
        url = reverse("v1:source-list")
        url += query
        return django_client.post(url, json=data, headers=ACCEPT_JSON_HEADER)

    def create_expect_201_with_query(self, query, data, django_client):
        """Create a valid source with a query parameter."""
        response = self.create_with_query(query, data, django_client)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def create_expect_400_with_query(
        self, query, data, django_client, expected_response=None
    ):
        """Create an expect HTTP 400 with a query param."""
        response = self.create_with_query(query, data, django_client)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def get_source(self, django_client, params=None, url=None):
        """Call the retrieve endpoint."""
        if not url:
            url = reverse("v1:source-list")
        if params is not None:
            return django_client.get(url, params=params)
        else:
            return django_client.get(url)

    def update_source(self, django_client, data, source_id):
        """Call the update endpoint."""
        url = reverse("v1:source-detail", args=(source_id,))
        return django_client.put(url=url, json=data)

    def partially_update_source(self, django_client, data, source_id):
        """Call the partialy update endpoint."""
        url = reverse("v1:source-detail", args=(source_id,))
        return django_client.patch(url=url, json=data)

    def source_object_factory(self, data, django_client, range_number):
        """Create source objects and return list with name and ids."""
        source_list = []
        for index in range(range_number):
            data["name"] = data["name"] + str(index)
            response = self.create_expect_201(data, django_client)

            source_info = {"name": data["name"], "id": response["id"]}
            source_list.append(source_info)
        return source_list

    def test_validate_opts(self):
        """Test the validate_opts function."""
        source_type = DataSources.SATELLITE
        options = {"use_paramiko": True}
        with pytest.raises(ValidationError):
            SourceSerializer.validate_opts(options, source_type)

        options = {}
        SourceSerializer.validate_opts(options, source_type)
        assert options["ssl_cert_verify"] is True

        source_type = DataSources.VCENTER
        options = {"use_paramiko": True}
        with pytest.raises(ValidationError):
            SourceSerializer.validate_opts(options, source_type)

        options = {}
        SourceSerializer.validate_opts(options, source_type)
        assert options["ssl_cert_verify"] is True

        source_type = DataSources.NETWORK
        options = {"disable_ssl": True}
        with pytest.raises(ValidationError):
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

        expected = {
            "id": source.id,
            "name": "source1",
            "source_type": "network",
            "port": 22,
            "hosts": ["1.2.3.4"],
            "connection": {
                "id": scan_job.id,
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

    def test_source_create_with_false_scan(self, django_client, net_cred):
        """Test creating a source with a valid scan query param of False."""
        query = "?scan=False"
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create_expect_201_with_query(query, data, django_client)
        assert "id" in response

    def test_source_create_with_true_scan(self, django_client, net_cred):
        """Test creating source with valid scan query param of True."""
        query = "?scan=True"
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201_with_query(query, data, django_client)

    def test_source_create_with_invalid_scan(self, django_client, net_cred):
        """Test the source create method with invalid query param."""
        query = "?scan=Foo"
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400_with_query(query, data, django_client)

    def test_successful_net_create(self, django_client, net_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create_expect_201(data, django_client)
        assert "id" in response

    def test_successful_net_create_no_port(self, django_client, net_cred):
        """A valid create request should succeed without port."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "credentials": [net_cred.id],
        }
        response = self.create_expect_201(data, django_client)
        assert "id" in response

    def test_double_create(self, django_client, net_cred):
        """A duplicate create should fail."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create_expect_201(data, django_client)
        assert "id" in response
        self.create_expect_400(data, django_client)

    def test_create_multiple_hosts(self, django_client, net_cred):
        """A valid create request with two hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201(data, django_client)

    def test_create_no_name(self, django_client, net_cred):
        """A create request must have a name."""
        data = {
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_invalid_name(self, django_client, net_cred):
        """A create request must have a string name."""
        data = {
            "name": 1,
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_unprintable_name(self, django_client, net_cred):
        """The Source name must be printable."""
        data = {
            "name": "\r\n",
            "source_type": DataSources.NETWORK,
            "hosts": "1.2.3.4",
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_no_host(self, django_client, net_cred):
        """A Source needs a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_empty_host(self, django_client, net_cred):
        """An empty string is not a host identifier."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_hosts_not_array(self, django_client, net_cred):
        """Test error when hosts is not an array."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": {"1.2.3.4": "1.2.3.4"},
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_hosts_not_array_of_strings(self, django_client, net_cred):
        """Test error when hosts is not an array of strings."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [1, 2, 3, 4],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_long_name(self, django_client, net_cred):
        """A long source name."""
        data = {
            "name": "A" * 100,
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_negative_port(self, django_client, net_cred):
        """negative port."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": -1,
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_empty_ip(self, django_client, net_cred):
        """An empty string passed with valid ips."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["10.10.181.9", ""],
            "port": "22",
            "credentials": [net_cred.id],
        }

        self.create_expect_201(data, django_client)

    def test_create_valid_hosts(self, django_client, net_cred):
        """Test valid host patterns."""
        data = {
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
            "credentials": [net_cred.id],
        }
        self.create_expect_201(data, django_client)

    def test_create_valid_exclude_hosts(self, django_client, net_cred):
        """Test valid exclude host patterns."""
        data = {
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
            "credentials": [net_cred.id],
        }

        self.create_expect_201(data, django_client)

    def test_create_invalid_hosts(self, django_client, net_cred):
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
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": hosts,
            "port": "22",
            "credentials": [net_cred.id],
        }

        response = self.create(data, django_client)
        assert response.status_code == 400
        assert len(response.json()["hosts"]) == len(hosts)

    def test_create_bad_host_pattern(self, django_client, net_cred):
        """Test a invalid host pattern."""
        hosts = ["10.1.1.1-10.1.1.254"]

        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": hosts,
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create(data, django_client)
        assert response.status_code == 400
        assert len(response.json()["hosts"]) == len(hosts)

    def test_create_bad_port(self, django_client, net_cred):
        """-1 is not a valid ssh port."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "-1",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_no_credentials(self, django_client):
        """A Source needs credentials."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
        }
        self.create_expect_400(data, django_client)

    def test_create_empty_credentials(self, django_client):
        """The empty string is not a valid credential list."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [],
        }

        self.create_expect_400(data, django_client)

    def test_create_credential_does_not_exist(self, django_client):
        """A random int is not a valid credential id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [42],
        }

        self.create_expect_400(data, django_client)

    def test_create_credential_not_valid_id(self, django_client):
        """A random int is not a valid credential id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": ["hi"],
        }
        self.create_expect_400(data, django_client)

    def test_create_invalid_cred_type(self, django_client, vc_cred):
        """A source type and credential type must be the same."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_with_options_not_allowed_network_type(
        self, django_client, net_cred
    ):
        """Test network type doesn't allow ssl options."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        self.create_expect_400(data, django_client)

    def test_list(self, django_client, net_cred):
        """List all Source objects."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "hosts": ["1.2.3.4"],
            "credentials": [net_cred.id],
        }

        source_list = self.source_object_factory(data, django_client, range_number=3)

        response = self.get_source(django_client)
        assert response.status_code == status.HTTP_200_OK

        content = response.json()
        cred_for_response = {"id": net_cred.id, "name": net_cred.name}

        results = []
        for source in source_list:
            result_dict = {
                "id": source["id"],
                "name": source["name"],
                "source_type": DataSources.NETWORK,
                "port": 22,
                "hosts": ["1.2.3.4"],
                "credentials": [cred_for_response],
            }
            results.append(result_dict)
        expected = {"count": 3, "next": None, "previous": None, "results": results}
        assert content == expected

    def test_filter_by_type_list(self, django_client, vc_cred, net_cred):
        """List all Source objects filtered by type."""
        net_data = {
            "name": "net_source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
            "hosts": ["1.2.3.4"],
        }
        self.source_object_factory(net_data, django_client, range_number=3)

        vcenter_data = {
            "name": "vc_source",
            "source_type": DataSources.VCENTER,
            "credentials": [vc_cred.id],
            "hosts": ["1.2.3.4"],
        }

        vcenter_source_list = self.source_object_factory(
            vcenter_data, django_client, range_number=2
        )

        response = self.get_source(django_client, {"source_type": DataSources.VCENTER})
        assert response.status_code == status.HTTP_200_OK

        content = response.json()
        cred_for_response = {"id": vc_cred.id, "name": vc_cred.name}
        results = []
        for source in vcenter_source_list:
            result_dict = {
                "id": source["id"],
                "name": source["name"],
                "source_type": DataSources.VCENTER,
                "port": 443,
                "hosts": ["1.2.3.4"],
                "options": {
                    "ssl_cert_verify": True,
                },
                "credentials": [cred_for_response],
            }
            results.append(result_dict)
        expected = {"count": 2, "next": None, "previous": None, "results": results}
        assert content == expected

    def test_retrieve(self, django_client, net_cred):
        """Get details on a specific Source by primary key."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        url = reverse("v1:source-detail", args=(initial["id"],))
        response = self.get_source(django_client, url=url)
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert "credentials" in response_json
        creds = response_json["credentials"]
        cred_for_response = {"id": net_cred.id, "name": net_cred.name}

        assert creds == [cred_for_response]
        assert "hosts" in response_json
        assert response_json["hosts"][0] == "1.2.3.4"
        assert response_json["exclude_hosts"][0] == "1.2.3.4"

    def test_retrieve_bad_id(self, django_client):
        """Get details on a specific Source by bad primary key."""
        url = reverse("v1:source-detail", args=("string",))
        response = self.get_source(django_client, url=url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update(self, django_client, net_cred):
        """Completely update a Source."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source2",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_200_OK

        net_cred_response = {"id": net_cred.id, "name": net_cred.name}
        expected = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred_response],
        }
        for key, value in expected.items():
            assert value == response.json()[key]

    def test_update_collide(self, django_client, net_cred):
        """Fail update due to name conflict."""
        first_net_source = {
            "name": "net_source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201(first_net_source, django_client)

        second_net_source = {
            "name": "net_source_2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(second_net_source, django_client)

        updated_data = {
            "name": "net_source",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_missing_hosts(self, django_client, net_cred):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.partially_update_source(
            django_client, updated_data, initial["id"]
        )

        assert response.status_code == status.HTTP_200_OK

    def test_partial_update_network_ssl_options_not_allowed(
        self, django_client, net_cred
    ):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "port": 22,
            "credentials": [net_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.partially_update_source(
            django_client, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_no_hosts_retains_initial_host(
        self, django_client, net_cred
    ):
        """Partial update should keep initial host if no host provided."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }

        initial = self.create_expect_201(data, django_client)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.partially_update_source(
            django_client, updated_data, initial["id"]
        )
        assert response.json()["hosts"] == ["1.2.3.4"]

    def test_partial_update_empty_hosts(self, django_client, net_cred):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "port": 22,
            "hosts": [],
            "credentials": [net_cred.id],
        }
        response = self.partially_update_source(
            django_client, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_missing_hosts(self, django_client, net_cred):
        """Fail update due to missing host array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_empty_hosts(self, django_client, net_cred):
        """Fail update due to empty host array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": [],
            "port": 22,
            "credentials": [net_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_HOSTS_CANNOT_BE_EMPTY

    def test_update_type_passed(self, django_client, net_cred):
        """Fail update due to type passed."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_bad_cred_type(self, django_client, net_cred, vc_cred):
        """Fail update due to bad cred type."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update(self, django_client, net_cred):
        """Partially update a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {"name": "source3-new", "hosts": ["1.2.3.5"]}
        response = self.partially_update_source(
            django_client, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "source3-new"
        assert response.json()["hosts"] == ["1.2.3.5"]

    def test_delete(self, django_client, net_cred):
        """Delete a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response_source_creation = self.create_expect_201(data, django_client)

        url = reverse("v1:source-detail", args=(response_source_creation["id"],))
        response = django_client.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_with_scans(self, django_client):
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

        scan = Scan.objects.create(
            name="test_scan", scan_type=ScanTask.SCAN_TYPE_CONNECT
        )
        scan.sources.add(source)

        url = reverse("v1:source-detail", args=(source.id,))
        response = django_client.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["detail"] == messages.SOURCE_DELETE_NOT_VALID_W_SCANS
        assert response_json["scans"][0]["name"] == "test_scan"

    def test_successful_vcenter_create(self, django_client, vc_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        response = self.create_expect_201(data, django_client)
        assert "id" in response

    def test_create_too_many_creds(self, django_client, vc_cred, net_cred):
        """A vcenter source and have one credential."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id, net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_req_host(self, django_client, vc_cred):
        """A vcenter source must have a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_empty_hosts(self, django_client, vc_cred):
        """A vcenter source not have empty hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": [],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_vc_with_hosts(self, django_client, vc_cred):
        """A vcenter source must not have multiple hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_vc_with_excluded_hosts(self, django_client, vc_cred):
        """A vcenter source must not have any excluded hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_vc_with_host_range(self, django_client, vc_cred):
        """A vcenter source must not have multiple hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4/5"],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_update_vc_greenpath(self, django_client, vc_cred):
        """VC - Success full update."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_200_OK

    def test_update_vc_more_than_one_host(self, django_client, vc_cred):
        """VC - Fail more than one host."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_with_exclude_host(self, django_client, vc_cred):
        """VC - Fail when excluded hosts are provided."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_more_than_one_cred(self, django_client, vc_cred):
        """VC - Fail more than one cred."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id, vc_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_range_hosts(self, django_client, vc_cred):
        """Fail update due to empty host array."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_create_req_type(self, django_client, vc_cred):
        """A vcenter source must have an type."""
        data = {
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_successful_sat_create(self, django_client, sat_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
        }
        response = self.create_expect_201(data, django_client)
        assert "id" in response

    def test_successful_sat_create_with_options(self, django_client, sat_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.create_expect_201(data, django_client)
        assert "id" in response

    def test_sat_too_many_creds(self, django_client, sat_cred, net_cred):
        """A sat source and have one credential."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id, net_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_sat_req_host(self, django_client, sat_cred):
        """A satellite source must have a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_sat_req_empty_hosts(self, django_client, sat_cred):
        """A satellite source must not have empty hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": [],
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_sat_with_hosts(self, django_client, sat_cred):
        """A satellite source must not have multiple hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_sat_with_exclude_hosts(self, django_client, sat_cred):
        """A satellite source does not accept excluded hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_create_sat_with_host_range(self, django_client, sat_cred):
        """A satellite source must not have multiple hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4/5"],
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_update_sat_greenpath(self, django_client, sat_cred):
        """Sat - Valid full update."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, django_client)
        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_200_OK

    def test_update_sat_with_options(self, django_client, sat_cred):
        """Sat - Valid full update with options."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_200_OK
        expected = {
            "id": initial["id"],
            "name": "source",
            "source_type": "satellite",
            "port": 22,
            "hosts": ["1.2.3.4"],
            "options": {"ssl_cert_verify": False},
            "credentials": [{"id": sat_cred.id, "name": "sat_cred1"}],
        }
        assert response.json() == expected

    def test_update_sat_more_than_one_hosts(self, django_client, sat_cred):
        """Sat- Fail update due to multiple hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_exclude_hosts(self, django_client, sat_cred):
        """Sat- Fail update due to including excluded hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_than_one_cred(self, django_client, sat_cred):
        """Sat- Fail update due to multiple hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id, sat_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_range_hosts(self, django_client, sat_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_openshift_source_create(self, django_client, openshift_cred):
        """Ensure we can create a new openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        self.create_expect_201(data, django_client)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "openshift_source_1"

    def test_openshift_missing_host(self, django_client, openshift_cred):
        """Ensure hosts field is required when creating openshift credential."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "credentials": [openshift_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_openshift_extra_unallowed_fields(self, django_client, openshift_cred):
        """Ensure unallowed fields are not accepted when creating openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
            "options": {"use_paramiko": True},
        }
        self.create_expect_400(data, django_client)

    def test_update_openshift_green_path(self, django_client, openshift_cred):
        """Openshift source successful update."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        initial = self.create_expect_201(data, django_client)
        updated_data = {
            "name": "openshift_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [openshift_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_200_OK

    def test_update_openshift_range_hosts(self, django_client, openshift_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "openshift_source_1",
            "hosts": ["1.2.3.4/5"],
            "credentials": [openshift_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = response.json()
        assert response["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_rhacs_source_create(self, django_client, rhacs_cred):
        """Ensure we can create a new RHACS source."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        self.create_expect_201(data, django_client)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "acs_source_1"

    def test_rhacs_missing_host(self, django_client, rhacs_cred):
        """Ensure hosts field is required when creating RHACS credential."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "credentials": [rhacs_cred.id],
        }
        self.create_expect_400(data, django_client)

    def test_rhacs_extra_unallowed_fields(self, django_client, rhacs_cred):
        """Ensure unallowed fields are not accepted when creating RHACS source."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
            "options": {"use_paramiko": True},
        }
        self.create_expect_400(data, django_client)

    def test_update_rhacs_green_path(self, django_client, rhacs_cred):
        """RHACS source successful update."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        initial = self.create_expect_201(data, django_client)
        updated_data = {
            "name": "acs_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [rhacs_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_200_OK

    def test_update_rhacs_range_hosts(self, django_client, rhacs_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        initial = self.create_expect_201(data, django_client)

        updated_data = {
            "name": "acs_source_1",
            "hosts": ["1.2.3.4/5"],
            "credentials": [rhacs_cred.id],
        }
        response = self.update_source(django_client, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = response.json()
        assert response["hosts"][0] == messages.SOURCE_ONE_HOST
