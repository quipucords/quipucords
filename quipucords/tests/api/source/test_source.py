"""Test the API application."""

import random
from datetime import UTC, datetime
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
from tests.factories import SourceFactory
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
def ansible_cred():
    """Return Ansible credential object."""
    return Credential.objects.create(
        name="ansible_cred1",
        cred_type=DataSources.ANSIBLE,
        username="username",
        password="password",
        become_password=None,
        ssh_keyfile=None,
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
def valid_cred(  # noqa: PLR0913
    net_cred, vc_cred, sat_cred, openshift_cred, ansible_cred, rhacs_cred
):
    """Return credential object based on source type."""

    def inner(source_type):
        match source_type:
            case DataSources.NETWORK:
                return net_cred
            case DataSources.VCENTER:
                return vc_cred
            case DataSources.SATELLITE:
                return sat_cred
            case DataSources.OPENSHIFT:
                return openshift_cred
            case DataSources.ANSIBLE:
                return ansible_cred
            case DataSources.RHACS:
                return rhacs_cred

    return inner


@pytest.fixture
def dummy_start():
    """Create a dummy method for testing."""


@pytest.mark.django_db
class TestSource:
    """Test the basic Source infrastructure."""

    def create(self, data, client_logged_in):
        """Call the create endpoint."""
        url = reverse("v1:source-list")
        return client_logged_in.post(url, data=data, headers=ACCEPT_JSON_HEADER)

    def create_expect_400(self, data, client_logged_in, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data, client_logged_in)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def create_expect_201(self, data, client_logged_in):
        """Create a source, return the response as a dict."""
        response = self.create(data, client_logged_in)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    @patch("api.source.view.start_scan", side_effect=dummy_start)
    def create_with_query(self, query, data, client_logged_in, start_scan):
        """Create a source with query param, return the response as a dict."""
        url = reverse("v1:source-list")
        url += query
        return client_logged_in.post(url, data=data, headers=ACCEPT_JSON_HEADER)

    def create_expect_201_with_query(self, query, data, client_logged_in):
        """Create a valid source with a query parameter."""
        response = self.create_with_query(query, data, client_logged_in)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def create_expect_400_with_query(
        self, query, data, client_logged_in, expected_response=None
    ):
        """Create an expect HTTP 400 with a query param."""
        response = self.create_with_query(query, data, client_logged_in)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def get_source(self, client_logged_in, params=None, url=None):
        """Call the retrieve endpoint."""
        if not url:
            url = reverse("v1:source-list")
        if params is not None:
            return client_logged_in.get(url, params)
        else:
            return client_logged_in.get(url)

    def update_source(self, client_logged_in, data, source_id):
        """Call the update endpoint."""
        url = reverse("v1:source-detail", args=(source_id,))
        return client_logged_in.put(url, data=data)

    def partially_update_source(self, client_logged_in, data, source_id):
        """Call the partialy update endpoint."""
        url = reverse("v1:source-detail", args=(source_id,))
        return client_logged_in.patch(url, data=data)

    def source_object_factory(self, data, client_logged_in, range_number):
        """Create source objects and return list with name and ids."""
        source_list = []
        for index in range(range_number):
            data["name"] = data["name"] + str(index)
            response = self.create_expect_201(data, client_logged_in)

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
        start = datetime.now(UTC)
        source = Source(
            name="source1",
            hosts=["1.2.3.4"],
            source_type="network",
            port=22,
        )
        source.save()
        end = datetime.now(UTC)
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

    @pytest.mark.parametrize("source_type", (ds for ds in DataSources))
    def test_successful_create(self, client_logged_in, valid_cred, source_type):
        """A valid create request should succeed."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [valid_cred_obj.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    @pytest.mark.parametrize(
        "source_type,default_port",
        (
            (DataSources.NETWORK, 22),
            (DataSources.VCENTER, 443),
            (DataSources.SATELLITE, 443),
            (DataSources.OPENSHIFT, 6443),
            (DataSources.ANSIBLE, 443),
            (DataSources.RHACS, 443),
        ),
    )
    def test_successful_create_no_port(
        self, client_logged_in, valid_cred, source_type, default_port
    ):
        """A valid create request should succeed without port."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "credentials": [valid_cred_obj.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response
        assert response.get("port") == default_port

    @pytest.mark.parametrize("source_type", (ds for ds in DataSources))
    def test_successful_create_custom_port(
        self, client_logged_in, valid_cred, source_type
    ):
        """A valid create request should succeed."""
        port = random.randint(1, 65535)
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "port": str(port),
            "credentials": [valid_cred_obj.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response
        assert response.get("port") == port

    def test_double_create(self, client_logged_in, net_cred):
        """A duplicate create should fail."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response
        self.create_expect_400(data, client_logged_in)

    def test_create_multiple_hosts(self, client_logged_in, net_cred):
        """A valid create request with two hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201(data, client_logged_in)

    def test_create_no_name(self, client_logged_in, net_cred):
        """A create request must have a name."""
        data = {
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_name(self, client_logged_in, net_cred):
        """Empty name is not valid."""
        data = {
            "name": "",
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_invalid_name(self, client_logged_in, net_cred):
        """A create request must have a string name."""
        data = {
            "name": 1,
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_unprintable_name(self, client_logged_in, net_cred):
        """The Source name must be printable."""
        data = {
            "name": "\r\n",
            "source_type": DataSources.NETWORK,
            "hosts": "1.2.3.4",
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_no_host(self, client_logged_in, net_cred):
        """A Source needs a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_host(self, client_logged_in, net_cred):
        """An empty array is not a host identifier."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_host_empty_string(self, client_logged_in, net_cred):
        """An empty string is not a host identifier."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [""],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_hosts_not_array(self, client_logged_in, net_cred):
        """Test error when hosts is not an array."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": {"1.2.3.4": "1.2.3.4"},
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_hosts_not_array_of_strings(self, client_logged_in, net_cred):
        """Test error when hosts is not an array of strings."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [1, 2, 3, 4],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_long_name(self, client_logged_in, net_cred):
        """A long source name."""
        data = {
            "name": "A" * 100,
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_ip(self, client_logged_in, net_cred):
        """An empty string passed with valid ips."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["10.10.181.9", ""],
            "port": "22",
            "credentials": [net_cred.id],
        }

        resp_json = self.create_expect_201(data, client_logged_in)
        resp_hosts = resp_json.get("hosts")
        assert len(resp_hosts) == 1
        assert resp_hosts == ["10.10.181.9"]

    def test_create_valid_hosts(self, client_logged_in, net_cred):
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
        self.create_expect_201(data, client_logged_in)

    def test_create_valid_exclude_hosts(self, client_logged_in, net_cred):
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

        self.create_expect_201(data, client_logged_in)

    def test_create_invalid_hosts(self, client_logged_in, net_cred):
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

        response = self.create(data, client_logged_in)
        assert response.status_code == 400
        assert len(response.json()["hosts"]) == len(hosts)

    def test_create_bad_host_pattern(self, client_logged_in, net_cred):
        """Test a invalid host pattern."""
        hosts = ["10.1.1.1-10.1.1.254"]

        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": hosts,
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create(data, client_logged_in)
        assert response.status_code == 400
        assert len(response.json()["hosts"]) == len(hosts)

    @pytest.mark.parametrize("bad_port", ("string*!", "-1", "False", -1, False))
    def test_create_bad_port(self, client_logged_in, net_cred, bad_port):
        """Some values are not a valid ssh port."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": bad_port,
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_no_credentials(self, client_logged_in):
        """A Source needs credentials."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_credentials(self, client_logged_in):
        """The empty string is not a valid credential list."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [],
        }

        self.create_expect_400(data, client_logged_in)

    def test_create_credential_does_not_exist(self, client_logged_in):
        """A random int is not a valid credential id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [42],
        }

        self.create_expect_400(data, client_logged_in)

    def test_create_credential_not_valid_id(self, client_logged_in):
        """A random int is not a valid credential id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": ["hi"],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_negative_credential_id(self, client_logged_in):
        """Negative numbers are not a valid id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [-5],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_invalid_cred_type(self, client_logged_in, vc_cred):
        """A source type and credential type must be the same."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_with_options_not_allowed_network_type(
        self, client_logged_in, net_cred
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
        self.create_expect_400(data, client_logged_in)

    def test_list(self, client_logged_in, net_cred):
        """List all Source objects."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "hosts": ["1.2.3.4"],
            "credentials": [net_cred.id],
        }

        source_list = self.source_object_factory(data, client_logged_in, range_number=3)

        response = self.get_source(client_logged_in)
        assert response.ok

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

    def test_filter_by_type_list(self, client_logged_in, vc_cred, net_cred):
        """List all Source objects filtered by type."""
        net_data = {
            "name": "net_source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
            "hosts": ["1.2.3.4"],
        }
        self.source_object_factory(net_data, client_logged_in, range_number=3)

        vcenter_data = {
            "name": "vc_source",
            "source_type": DataSources.VCENTER,
            "credentials": [vc_cred.id],
            "hosts": ["1.2.3.4"],
        }

        vcenter_source_list = self.source_object_factory(
            vcenter_data, client_logged_in, range_number=2
        )

        response = self.get_source(
            client_logged_in, {"source_type": DataSources.VCENTER}
        )
        assert response.ok

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
                "options": {"ssl_cert_verify": True},
                "credentials": [cred_for_response],
            }
            results.append(result_dict)
        expected = {"count": 2, "next": None, "previous": None, "results": results}
        assert content == expected

    def test_retrieve(self, client_logged_in, net_cred):
        """Get details on a specific Source by primary key."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        url = reverse("v1:source-detail", args=(initial["id"],))
        response = self.get_source(client_logged_in, url=url)
        assert response.ok
        response_json = response.json()
        assert "credentials" in response_json
        creds = response_json["credentials"]
        cred_for_response = {"id": net_cred.id, "name": net_cred.name}

        assert creds == [cred_for_response]
        assert "hosts" in response_json
        assert response_json["hosts"][0] == "1.2.3.4"
        assert response_json["exclude_hosts"][0] == "1.2.3.4"

    def test_retrieve_bad_id(self, client_logged_in):
        """Get details on a specific Source by bad primary key."""
        url = reverse("v1:source-detail", args=("string",))
        response = self.get_source(client_logged_in, url=url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update(self, client_logged_in, net_cred):
        """Completely update a Source."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source2",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

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

    def test_update_collide(self, client_logged_in, net_cred):
        """Fail update due to name conflict."""
        first_net_source = {
            "name": "net_source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201(first_net_source, client_logged_in)

        second_net_source = {
            "name": "net_source_2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(second_net_source, client_logged_in)

        updated_data = {
            "name": "net_source",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_missing_hosts(self, client_logged_in, net_cred):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )

        assert response.ok

    def test_partial_update_network_ssl_options_not_allowed(
        self, client_logged_in, net_cred
    ):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "port": 22,
            "credentials": [net_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_no_hosts_retains_initial_host(
        self, client_logged_in, net_cred
    ):
        """Partial update should keep initial host if no host provided."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }

        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.json()["hosts"] == ["1.2.3.4"]

    def test_partial_update_empty_hosts(self, client_logged_in, net_cred):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "port": 22,
            "hosts": [],
            "credentials": [net_cred.id],
        }
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_missing_hosts(self, client_logged_in, net_cred):
        """Fail update due to missing host array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_invalid_hosts(self, client_logged_in, net_cred):
        """Fail update due to invalid host."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "port": 22,
            "credentials": [net_cred.id],
            "hosts": ["1**2@33^"],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_empty_hosts(self, client_logged_in, net_cred):
        """Fail update due to empty host array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": [],
            "port": 22,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_HOSTS_CANNOT_BE_EMPTY

    def test_update_missing_credentials(self, client_logged_in, net_cred):
        """Fail update due to missing credentials array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "hosts": ["1.2.3.4"]}
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_empty_credentials(self, client_logged_in, net_cred):
        """Fail update due to empty credentials array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["credentials"][0] == messages.SOURCE_MIN_CREDS

    def test_update_type_passed(self, client_logged_in, net_cred):
        """Fail update due to type passed."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_bad_cred_type(self, client_logged_in, net_cred, vc_cred):
        """Fail update due to bad cred type."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_invalid_exclude_hosts(self, client_logged_in, net_cred):
        """Fail update due to invalid host."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
            "exclude_hosts": ["*invalid!!host&*"],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update(self, client_logged_in, net_cred):
        """Partially update a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source3-new", "hosts": ["1.2.3.5"]}
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.ok
        assert response.json()["name"] == "source3-new"
        assert response.json()["hosts"] == ["1.2.3.5"]

    def test_delete(self, client_logged_in, net_cred):
        """Delete a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response_source_creation = self.create_expect_201(data, client_logged_in)

        url = reverse("v1:source-detail", args=(response_source_creation["id"],))
        response = client_logged_in.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_with_scans(self, client_logged_in):
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
        response = client_logged_in.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["detail"] == messages.SOURCE_DELETE_NOT_VALID_W_SCANS
        assert response_json["scans"][0]["name"] == "test_scan"

    def test_delete_and_list(self, client_logged_in, net_cred):
        """Delete a Source and confirm other Sources remain intact."""
        total_sources = 3
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "hosts": ["1.2.3.4"],
            "credentials": [net_cred.id],
        }
        source_list = self.source_object_factory(
            data, client_logged_in, range_number=total_sources
        )
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

        removed_source = results.pop(random.randrange(0, total_sources))
        url = reverse("v1:source-detail", args=(removed_source["id"],))
        response = client_logged_in.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        expected = {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results,
        }
        response = self.get_source(client_logged_in)
        assert response.ok
        content = response.json()
        assert content == expected

    def test_successful_vcenter_create(self, client_logged_in, vc_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    def test_create_too_many_creds(self, client_logged_in, vc_cred, net_cred):
        """A vcenter source and have one credential."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id, net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_req_host(self, client_logged_in, vc_cred):
        """A vcenter source must have a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_hosts(self, client_logged_in, vc_cred):
        """A vcenter source not have empty hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": [],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    @pytest.mark.parametrize(
        "source_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    def test_negative_create_non_network_with_hosts(
        self, client_logged_in, valid_cred, source_type
    ):
        """A vcenter source must not have multiple hosts."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "credentials": [valid_cred_obj.id],
        }
        self.create_expect_400(data, client_logged_in)

    @pytest.mark.parametrize(
        "source_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    def test_negative_create_non_network_with_excluded_hosts(
        self, client_logged_in, valid_cred, source_type
    ):
        """A vcenter source must not have any excluded hosts."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "credentials": [valid_cred_obj.id],
        }
        self.create_expect_400(data, client_logged_in)

    @pytest.mark.parametrize(
        "source_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    @pytest.mark.parametrize("hosts_range", ("1.2.3.4/5", "1.2.3.[0:255]"))
    def test_negative_create_non_network_with_host_range(
        self, client_logged_in, valid_cred, source_type, hosts_range
    ):
        """A vcenter source must not have multiple hosts."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": [hosts_range],
            "credentials": [valid_cred_obj.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_vc_greenpath(self, client_logged_in, vc_cred):
        """VC - Success full update."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

    def test_update_vc_more_than_one_host(self, client_logged_in, vc_cred):
        """VC - Fail more than one host."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_with_exclude_host(self, client_logged_in, vc_cred):
        """VC - Fail when excluded hosts are provided."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_more_than_one_cred(self, client_logged_in, vc_cred):
        """VC - Fail more than one cred."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id, vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_range_hosts(self, client_logged_in, vc_cred):
        """Fail update due to empty host array."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_create_req_type(self, client_logged_in, vc_cred):
        """A vcenter source must have an type."""
        data = {
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_successful_sat_create(self, client_logged_in, sat_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    def test_successful_sat_create_with_options(self, client_logged_in, sat_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    def test_sat_too_many_creds(self, client_logged_in, sat_cred, net_cred):
        """A sat source and have one credential."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id, net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_sat_req_host(self, client_logged_in, sat_cred):
        """A satellite source must have a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_sat_req_empty_hosts(self, client_logged_in, sat_cred):
        """A satellite source must not have empty hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": [],
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_sat_greenpath(self, client_logged_in, sat_cred):
        """Sat - Valid full update."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)
        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

    def test_update_sat_with_options(self, client_logged_in, sat_cred):
        """Sat - Valid full update with options."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok
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

    def test_update_sat_more_than_one_hosts(self, client_logged_in, sat_cred):
        """Sat- Fail update due to multiple hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_exclude_hosts(self, client_logged_in, sat_cred):
        """Sat- Fail update due to including excluded hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_than_one_cred(self, client_logged_in, sat_cred):
        """Sat- Fail update due to multiple hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id, sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_range_hosts(self, client_logged_in, sat_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_openshift_source_create(self, client_logged_in, openshift_cred):
        """Ensure we can create a new openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        self.create_expect_201(data, client_logged_in)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "openshift_source_1"

    def test_openshift_missing_host(self, client_logged_in, openshift_cred):
        """Ensure hosts field is required when creating openshift credential."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "credentials": [openshift_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_openshift_extra_unallowed_fields(self, client_logged_in, openshift_cred):
        """Ensure unallowed fields are not accepted when creating openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
            "options": {"use_paramiko": True},
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_openshift_green_path(self, client_logged_in, openshift_cred):
        """Openshift source successful update."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)
        updated_data = {
            "name": "openshift_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [openshift_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

    def test_update_openshift_range_hosts(self, client_logged_in, openshift_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "openshift_source_1",
            "hosts": ["1.2.3.4/5"],
            "credentials": [openshift_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = response.json()
        assert response["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_rhacs_source_create(self, client_logged_in, rhacs_cred):
        """Ensure we can create a new RHACS source."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        self.create_expect_201(data, client_logged_in)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "acs_source_1"

    def test_rhacs_missing_host(self, client_logged_in, rhacs_cred):
        """Ensure hosts field is required when creating RHACS credential."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "credentials": [rhacs_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_rhacs_extra_unallowed_fields(self, client_logged_in, rhacs_cred):
        """Ensure unallowed fields are not accepted when creating RHACS source."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
            "options": {"use_paramiko": True},
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_rhacs_green_path(self, client_logged_in, rhacs_cred):
        """RHACS source successful update."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)
        updated_data = {
            "name": "acs_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [rhacs_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok


@pytest.mark.django_db
class TestSourceV2:
    """Test the basic V2 Source infrastructure."""

    def create(self, data, client_logged_in):
        """Call the create endpoint."""
        url = reverse("v2:source-list")
        return client_logged_in.post(url, data=data, headers=ACCEPT_JSON_HEADER)

    def create_expect_400(self, data, client_logged_in, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data, client_logged_in)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def create_expect_201(self, data, client_logged_in):
        """Create a source, return the response as a dict."""
        response = self.create(data, client_logged_in)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    @patch("api.source.view.start_scan", side_effect=dummy_start)
    def create_with_query(self, query, data, client_logged_in, start_scan):
        """Create a source with query param, return the response as a dict."""
        url = reverse("v2:source-list")
        url += query
        return client_logged_in.post(url, data=data, headers=ACCEPT_JSON_HEADER)

    def create_expect_201_with_query(self, query, data, client_logged_in):
        """Create a valid source with a query parameter."""
        response = self.create_with_query(query, data, client_logged_in)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def create_expect_400_with_query(
        self, query, data, client_logged_in, expected_response=None
    ):
        """Create an expect HTTP 400 with a query param."""
        response = self.create_with_query(query, data, client_logged_in)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_response:
            response_json = response.json()
            assert response_json == expected_response

    def get_source(self, client_logged_in, params=None, url=None):
        """Call the retrieve endpoint."""
        if not url:
            url = reverse("v2:source-list")
        if params is not None:
            return client_logged_in.get(url, params)
        else:
            return client_logged_in.get(url)

    def update_source(self, client_logged_in, data, source_id):
        """Call the update endpoint."""
        url = reverse("v2:source-detail", args=(source_id,))
        return client_logged_in.put(url, data=data)

    def partially_update_source(self, client_logged_in, data, source_id):
        """Call the partially update endpoint."""
        url = reverse("v2:source-detail", args=(source_id,))
        return client_logged_in.patch(url, data=data)

    def source_object_factory(self, data, client_logged_in, range_number):
        """Create source objects and return list with name and ids."""
        source_list = []
        for index in range(range_number):
            data["name"] = data["name"] + str(index)
            response = self.create_expect_201(data, client_logged_in)

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
        start = datetime.now(UTC)
        source = Source(
            name="source1",
            hosts=["1.2.3.4"],
            source_type="network",
            port=22,
        )
        source.save()
        end = datetime.now(UTC)
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

    @pytest.mark.parametrize("source_type", (ds for ds in DataSources))
    def test_successful_create(self, client_logged_in, valid_cred, source_type):
        """A valid create request should succeed."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [valid_cred_obj.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    @pytest.mark.parametrize(
        "source_type,default_port",
        (
            (DataSources.NETWORK, 22),
            (DataSources.VCENTER, 443),
            (DataSources.SATELLITE, 443),
            (DataSources.OPENSHIFT, 6443),
            (DataSources.ANSIBLE, 443),
            (DataSources.RHACS, 443),
        ),
    )
    def test_successful_create_no_port(
        self, client_logged_in, valid_cred, source_type, default_port
    ):
        """A valid create request should succeed without port."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "credentials": [valid_cred_obj.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response
        assert response.get("port") == default_port

    @pytest.mark.parametrize("source_type", (ds for ds in DataSources))
    def test_successful_create_custom_port(
        self, client_logged_in, valid_cred, source_type
    ):
        """A valid create request should succeed."""
        port = random.randint(1, 65535)
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "port": str(port),
            "credentials": [valid_cred_obj.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response
        assert response.get("port") == port

    def test_double_create(self, client_logged_in, net_cred):
        """A duplicate create should fail."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response
        self.create_expect_400(data, client_logged_in)

    def test_create_multiple_hosts(self, client_logged_in, net_cred):
        """A valid create request with two hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201(data, client_logged_in)

    def test_create_no_name(self, client_logged_in, net_cred):
        """A create request must have a name."""
        data = {
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_name(self, client_logged_in, net_cred):
        """Empty name is not valid."""
        data = {
            "name": "",
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_invalid_name(self, client_logged_in, net_cred):
        """A create request must have a string name."""
        data = {
            "name": 1,
            "hosts": "1.2.3.4",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_unprintable_name(self, client_logged_in, net_cred):
        """The Source name must be printable."""
        data = {
            "name": "\r\n",
            "source_type": DataSources.NETWORK,
            "hosts": "1.2.3.4",
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_no_host(self, client_logged_in, net_cred):
        """A Source needs a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_host(self, client_logged_in, net_cred):
        """An empty array is not a host identifier."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_host_empty_string(self, client_logged_in, net_cred):
        """An empty string is not a host identifier."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [""],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_hosts_not_array(self, client_logged_in, net_cred):
        """Test error when hosts is not an array."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": {"1.2.3.4": "1.2.3.4"},
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_hosts_not_array_of_strings(self, client_logged_in, net_cred):
        """Test error when hosts is not an array of strings."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": [1, 2, 3, 4],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_long_name(self, client_logged_in, net_cred):
        """A long source name."""
        data = {
            "name": "A" * 100,
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_ip(self, client_logged_in, net_cred):
        """An empty string passed with valid ips."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["10.10.181.9", ""],
            "port": "22",
            "credentials": [net_cred.id],
        }

        resp_json = self.create_expect_201(data, client_logged_in)
        resp_hosts = resp_json.get("hosts")
        assert len(resp_hosts) == 1
        assert resp_hosts == ["10.10.181.9"]

    def test_create_valid_hosts(self, client_logged_in, net_cred):
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
        self.create_expect_201(data, client_logged_in)

    def test_create_valid_exclude_hosts(self, client_logged_in, net_cred):
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

        self.create_expect_201(data, client_logged_in)

    def test_create_invalid_hosts(self, client_logged_in, net_cred):
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

        response = self.create(data, client_logged_in)
        assert response.status_code == 400
        assert len(response.json()["hosts"]) == len(hosts)

    def test_create_bad_host_pattern(self, client_logged_in, net_cred):
        """Test a invalid host pattern."""
        hosts = ["10.1.1.1-10.1.1.254"]

        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": hosts,
            "port": "22",
            "credentials": [net_cred.id],
        }
        response = self.create(data, client_logged_in)
        assert response.status_code == 400
        assert len(response.json()["hosts"]) == len(hosts)

    @pytest.mark.parametrize("bad_port", ("string*!", "-1", "False", -1, False))
    def test_create_bad_port(self, client_logged_in, net_cred, bad_port):
        """Some values are not a valid ssh port."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": bad_port,
            "credentials": [net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_no_credentials(self, client_logged_in):
        """A Source needs credentials."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_credentials(self, client_logged_in):
        """The empty string is not a valid credential list."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [],
        }

        self.create_expect_400(data, client_logged_in)

    def test_create_credential_does_not_exist(self, client_logged_in):
        """A random int is not a valid credential id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [42],
        }

        self.create_expect_400(data, client_logged_in)

    def test_create_credential_not_valid_id(self, client_logged_in):
        """A random int is not a valid credential id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": ["hi"],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_negative_credential_id(self, client_logged_in):
        """Negative numbers are not a valid id."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [-5],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_invalid_cred_type(self, client_logged_in, vc_cred):
        """A source type and credential type must be the same."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_with_options_not_allowed_network_type(
        self, client_logged_in, net_cred
    ):
        """Test network type doesn't allow ssl options."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
            "ssl_cert_verify": False,
        }
        self.create_expect_400(data, client_logged_in)

    def test_list(self, client_logged_in, net_cred):
        """List all Source objects."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "hosts": ["1.2.3.4"],
            "credentials": [net_cred.id],
        }

        source_list = self.source_object_factory(data, client_logged_in, range_number=3)

        response = self.get_source(client_logged_in)
        assert response.ok

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
                "exclude_hosts": None,
                "disable_ssl": None,
                "ssl_cert_verify": None,
                "ssl_protocol": None,
                "use_paramiko": None,
            }
            results.append(result_dict)
        expected = {"count": 3, "next": None, "previous": None, "results": results}
        assert content == expected

    def test_filter_by_type_list(self, client_logged_in, vc_cred, net_cred):
        """List all Source objects filtered by type."""
        net_data = {
            "name": "net_source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "credentials": [net_cred.id],
            "hosts": ["1.2.3.4"],
        }
        self.source_object_factory(net_data, client_logged_in, range_number=3)

        vcenter_data = {
            "name": "vc_source",
            "source_type": DataSources.VCENTER,
            "credentials": [vc_cred.id],
            "hosts": ["1.2.3.4"],
        }

        vcenter_source_list = self.source_object_factory(
            vcenter_data, client_logged_in, range_number=2
        )

        response = self.get_source(
            client_logged_in, {"source_type": DataSources.VCENTER}
        )
        assert response.ok

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
                "ssl_cert_verify": True,
                "ssl_protocol": None,
                "use_paramiko": None,
                "disable_ssl": None,
                "credentials": [cred_for_response],
                "exclude_hosts": None,
            }
            results.append(result_dict)
        expected = {"count": 2, "next": None, "previous": None, "results": results}
        assert content == expected

    def test_retrieve(self, client_logged_in, net_cred):
        """Get details on a specific Source by primary key."""
        data = {
            "name": "source1",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        url = reverse("v2:source-detail", args=(initial["id"],))
        response = self.get_source(client_logged_in, url=url)
        assert response.ok
        response_json = response.json()
        assert "credentials" in response_json
        creds = response_json["credentials"]
        cred_for_response = {"id": net_cred.id, "name": net_cred.name}

        assert creds == [cred_for_response]
        assert "hosts" in response_json
        assert response_json["hosts"][0] == "1.2.3.4"
        assert response_json["exclude_hosts"][0] == "1.2.3.4"

    def test_retrieve_bad_id(self, client_logged_in):
        """Get details on a specific Source by bad primary key."""
        url = reverse("v2:source-detail", args=("string",))
        response = self.get_source(client_logged_in, url=url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update(self, client_logged_in, net_cred):
        """Completely update a Source."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source2",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

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

    def test_update_collide(self, client_logged_in, net_cred):
        """Fail update due to name conflict."""
        first_net_source = {
            "name": "net_source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        self.create_expect_201(first_net_source, client_logged_in)

        second_net_source = {
            "name": "net_source_2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(second_net_source, client_logged_in)

        updated_data = {
            "name": "net_source",
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_missing_hosts(self, client_logged_in, net_cred):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )

        assert response.ok

    def test_partial_update_network_ssl_options_not_allowed(
        self, client_logged_in, net_cred
    ):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "port": 22,
            "credentials": [net_cred.id],
            "ssl_cert_verify": False,
        }
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_no_hosts_retains_initial_host(
        self, client_logged_in, net_cred
    ):
        """Partial update should keep initial host if no host provided."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }

        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.json()["hosts"] == ["1.2.3.4"]

    def test_partial_update_empty_hosts(self, client_logged_in, net_cred):
        """Partial update should succeed with missing hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "port": 22,
            "hosts": [],
            "credentials": [net_cred.id],
        }
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_missing_hosts(self, client_logged_in, net_cred):
        """Fail update due to missing host array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "credentials": [net_cred.id]}
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_invalid_hosts(self, client_logged_in, net_cred):
        """Fail update due to invalid host."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "port": 22,
            "credentials": [net_cred.id],
            "hosts": ["1**2@33^"],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_empty_hosts(self, client_logged_in, net_cred):
        """Fail update due to empty host array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": [],
            "port": 22,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_HOSTS_CANNOT_BE_EMPTY

    def test_update_missing_credentials(self, client_logged_in, net_cred):
        """Fail update due to missing credentials array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source", "port": 22, "hosts": ["1.2.3.4"]}
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_empty_credentials(self, client_logged_in, net_cred):
        """Fail update due to empty credentials array."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["credentials"][0] == messages.SOURCE_MIN_CREDS

    def test_update_type_passed(self, client_logged_in, net_cred):
        """Fail update due to type passed."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [net_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_bad_cred_type(self, client_logged_in, net_cred, vc_cred):
        """Fail update due to bad cred type."""
        data = {
            "name": "source2",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.5"],
            "port": 23,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_invalid_exclude_hosts(self, client_logged_in, net_cred):
        """Fail update due to invalid host."""
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
            "exclude_hosts": ["*invalid!!host&*"],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update(self, client_logged_in, net_cred):
        """Partially update a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {"name": "source3-new", "hosts": ["1.2.3.5"]}
        response = self.partially_update_source(
            client_logged_in, updated_data, initial["id"]
        )
        assert response.ok
        assert response.json()["name"] == "source3-new"
        assert response.json()["hosts"] == ["1.2.3.5"]

    def test_delete(self, client_logged_in, net_cred):
        """Delete a Source."""
        data = {
            "name": "source3",
            "source_type": DataSources.NETWORK,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [net_cred.id],
        }
        response_source_creation = self.create_expect_201(data, client_logged_in)

        url = reverse("v2:source-detail", args=(response_source_creation["id"],))
        response = client_logged_in.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_with_scans(self, client_logged_in):
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

        url = reverse("v2:source-detail", args=(source.id,))
        response = client_logged_in.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["detail"] == messages.SOURCE_DELETE_NOT_VALID_W_SCANS
        assert response_json["scans"][0]["name"] == "test_scan"

    def test_delete_and_list(self, client_logged_in, net_cred):
        """Delete a Source and confirm other Sources remain intact."""
        total_sources = 3
        data = {
            "name": "source",
            "source_type": DataSources.NETWORK,
            "port": "22",
            "hosts": ["1.2.3.4"],
            "credentials": [net_cred.id],
        }
        source_list = self.source_object_factory(
            data, client_logged_in, range_number=total_sources
        )
        cred_for_response = {"id": net_cred.id, "name": net_cred.name}
        results = []
        for source in source_list:
            result_dict = {
                "id": source["id"],
                "name": source["name"],
                "source_type": DataSources.NETWORK,
                "port": 22,
                "hosts": ["1.2.3.4"],
                "ssl_protocol": None,
                "ssl_cert_verify": None,
                "disable_ssl": None,
                "use_paramiko": None,
                "credentials": [cred_for_response],
                "exclude_hosts": None,
            }
            results.append(result_dict)

        removed_source = results.pop(random.randrange(0, total_sources))
        url = reverse("v2:source-detail", args=(removed_source["id"],))
        response = client_logged_in.delete(url, headers=ACCEPT_JSON_HEADER)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        expected = {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results,
        }
        response = self.get_source(client_logged_in)
        assert response.ok
        content = response.json()
        assert content == expected

    def test_successful_vcenter_create(self, client_logged_in, vc_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    def test_create_too_many_creds(self, client_logged_in, vc_cred, net_cred):
        """A vcenter source and have one credential."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id, net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_req_host(self, client_logged_in, vc_cred):
        """A vcenter source must have a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_create_empty_hosts(self, client_logged_in, vc_cred):
        """A vcenter source not have empty hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.VCENTER,
            "hosts": [],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    @pytest.mark.parametrize(
        "source_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    def test_negative_create_non_network_with_hosts(
        self, client_logged_in, valid_cred, source_type
    ):
        """A vcenter source must not have multiple hosts."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4", "1.2.3.5"],
            "credentials": [valid_cred_obj.id],
        }
        self.create_expect_400(data, client_logged_in)

    @pytest.mark.parametrize(
        "source_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    def test_negative_create_non_network_with_excluded_hosts(
        self, client_logged_in, valid_cred, source_type
    ):
        """A vcenter source must not have any excluded hosts."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "credentials": [valid_cred_obj.id],
        }
        self.create_expect_400(data, client_logged_in)

    @pytest.mark.parametrize(
        "source_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    @pytest.mark.parametrize("hosts_range", ("1.2.3.4/5", "1.2.3.[0:255]"))
    def test_negative_create_non_network_with_host_range(
        self, client_logged_in, valid_cred, source_type, hosts_range
    ):
        """A vcenter source must not have multiple hosts."""
        valid_cred_obj = valid_cred(source_type)
        data = {
            "name": "source1",
            "source_type": source_type,
            "hosts": [hosts_range],
            "credentials": [valid_cred_obj.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_vc_greenpath(self, client_logged_in, vc_cred):
        """VC - Success full update."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

    def test_update_vc_more_than_one_host(self, client_logged_in, vc_cred):
        """VC - Fail more than one host."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_with_exclude_host(self, client_logged_in, vc_cred):
        """VC - Fail when excluded hosts are provided."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_more_than_one_cred(self, client_logged_in, vc_cred):
        """VC - Fail more than one cred."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [vc_cred.id, vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_vc_range_hosts(self, client_logged_in, vc_cred):
        """Fail update due to empty host array."""
        data = {
            "name": "source",
            "source_type": DataSources.VCENTER,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [vc_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [vc_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_create_req_type(self, client_logged_in, vc_cred):
        """A vcenter source must have an type."""
        data = {
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credentials": [vc_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_successful_sat_create(self, client_logged_in, sat_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    def test_successful_sat_create_with_options(self, client_logged_in, sat_cred):
        """A valid create request should succeed."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id],
            "options": {"ssl_cert_verify": False},
        }
        response = self.create_expect_201(data, client_logged_in)
        assert "id" in response

    def test_sat_too_many_creds(self, client_logged_in, sat_cred, net_cred):
        """A sat source and have one credential."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "credentials": [sat_cred.id, net_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_sat_req_host(self, client_logged_in, sat_cred):
        """A satellite source must have a host."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_sat_req_empty_hosts(self, client_logged_in, sat_cred):
        """A satellite source must not have empty hosts."""
        data = {
            "name": "source1",
            "source_type": DataSources.SATELLITE,
            "hosts": [],
            "credentials": [sat_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_sat_greenpath(self, client_logged_in, sat_cred):
        """Sat - Valid full update."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)
        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

    def test_update_sat_with_options(self, client_logged_in, sat_cred):
        """Sat - Valid full update with options."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
            "ssl_cert_verify": False,
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok
        expected = {
            "id": initial["id"],
            "name": "source",
            "source_type": "satellite",
            "port": 22,
            "hosts": ["1.2.3.4"],
            "ssl_cert_verify": False,
            "ssl_protocol": None,
            "use_paramiko": None,
            "disable_ssl": None,
            "credentials": [{"id": sat_cred.id, "name": "sat_cred1"}],
            "exclude_hosts": None,
        }
        assert response.json() == expected

    def test_update_sat_more_than_one_hosts(self, client_logged_in, sat_cred):
        """Sat- Fail update due to multiple hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4", "2.3.4.5"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_exclude_hosts(self, client_logged_in, sat_cred):
        """Sat- Fail update due to including excluded hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "exclude_hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_more_than_one_cred(self, client_logged_in, sat_cred):
        """Sat- Fail update due to multiple hosts."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4"],
            "port": 22,
            "credentials": [sat_cred.id, sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sat_range_hosts(self, client_logged_in, sat_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "source",
            "source_type": DataSources.SATELLITE,
            "hosts": ["1.2.3.4"],
            "port": "22",
            "credentials": [sat_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "source",
            "hosts": ["1.2.3.4/5"],
            "port": 22,
            "credentials": [sat_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_openshift_source_create(self, client_logged_in, openshift_cred):
        """Ensure we can create a new openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        self.create_expect_201(data, client_logged_in)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "openshift_source_1"

    def test_openshift_missing_host(self, client_logged_in, openshift_cred):
        """Ensure hosts field is required when creating openshift credential."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "credentials": [openshift_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_openshift_extra_unallowed_fields(self, client_logged_in, openshift_cred):
        """Ensure unallowed fields are not accepted when creating openshift source."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
            "use_paramiko": True,
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_openshift_green_path(self, client_logged_in, openshift_cred):
        """Openshift source successful update."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)
        updated_data = {
            "name": "openshift_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [openshift_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok

    def test_update_openshift_range_hosts(self, client_logged_in, openshift_cred):
        """Fail update due to invalid host array."""
        data = {
            "name": "openshift_source_1",
            "source_type": DataSources.OPENSHIFT,
            "hosts": ["1.2.3.4"],
            "credentials": [openshift_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)

        updated_data = {
            "name": "openshift_source_1",
            "hosts": ["1.2.3.4/5"],
            "credentials": [openshift_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = response.json()
        assert response["hosts"][0] == messages.SOURCE_ONE_HOST

    def test_rhacs_source_create(self, client_logged_in, rhacs_cred):
        """Ensure we can create a new RHACS source."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        self.create_expect_201(data, client_logged_in)
        assert Source.objects.count() == 1
        assert Source.objects.get().name == "acs_source_1"

    def test_rhacs_missing_host(self, client_logged_in, rhacs_cred):
        """Ensure hosts field is required when creating RHACS credential."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "credentials": [rhacs_cred.id],
        }
        self.create_expect_400(data, client_logged_in)

    def test_rhacs_extra_unallowed_fields(self, client_logged_in, rhacs_cred):
        """Ensure unallowed fields are not accepted when creating RHACS source."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
            "use_paramiko": True,
        }
        self.create_expect_400(data, client_logged_in)

    def test_update_rhacs_green_path(self, client_logged_in, rhacs_cred):
        """RHACS source successful update."""
        data = {
            "name": "acs_source_1",
            "source_type": DataSources.RHACS,
            "hosts": ["1.2.3.4"],
            "credentials": [rhacs_cred.id],
        }
        initial = self.create_expect_201(data, client_logged_in)
        updated_data = {
            "name": "acs_source_1",
            "hosts": ["5.3.2.1"],
            "credentials": [rhacs_cred.id],
        }
        response = self.update_source(client_logged_in, updated_data, initial["id"])
        assert response.ok


@pytest.mark.django_db
def test_source_model_str():
    """Test the __str__ method."""
    source = SourceFactory()
    source_str = f"{source}"
    assert f"id={source.id}" in source_str
    assert f"source_type={source.source_type}" in source_str
    assert f"name={source.name}" in source_str
