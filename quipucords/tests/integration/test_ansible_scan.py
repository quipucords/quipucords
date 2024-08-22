"""Integration test for Ansible scanner."""

import re

import pytest

from tests.integration.test_smoker import Smoker


@pytest.fixture
def mocked_requests(requests_mock, live_server):
    """
    Mock all requests ansible controller scanner will make.

    Mocked responses contain only the data we care about (otherwise this module would be
    unreadable).
    """
    # allow calling all endpoints on django live server
    django_url_matcher = re.compile(rf"{live_server.url}.*")
    for method in ("GET", "POST"):
        requests_mock.register_uri(method, django_url_matcher, real_http=True)
    ansible_host = "https://ansible-controller.host:443"
    # only thing we care "me" is if it has a valid status code.
    requests_mock.get(f"{ansible_host}/api/v2/me/")
    requests_mock.get(
        f"{ansible_host}/api/v2/ping/",
        json={
            "version": "<ANSIBLE_CONTROLLER_VERSION>",
            "active_node": "<NODE_IP>",
        },
    )
    requests_mock.get(
        f"{ansible_host}/api/v2/hosts/",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "type": "host",
                    "created": "<CREATED_DATE>",
                    "modified": "<MODIFIED_DATE>",
                    "name": "<LISTED_HOST>",
                }
            ],
        },
    )

    requests_mock.get(
        f"{ansible_host}/api/v2/jobs/",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"id": 1, "type": "job"}, {"id": 2, "type": "job"}],
        },
    )
    requests_mock.get(
        f"{ansible_host}/api/v2/jobs/1/job_events/?event=runner_on_start",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"id": 1, "type": "job_event", "host_name": "<DELETED_HOST>"}],
        },
    )
    requests_mock.get(
        f"{ansible_host}/api/v2/jobs/2/job_events/?event=runner_on_start",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"id": 1, "type": "job_event", "host_name": "<LISTED_HOST>"}],
        },
    )


@pytest.fixture
def expected_facts():
    """Return expected facts for ansible controller integration."""
    return [
        {
            "comparison": {
                "hosts_in_inventory": ["<LISTED_HOST>"],
                "hosts_only_in_jobs": ["<DELETED_HOST>"],
                "number_of_hosts_in_inventory": 1,
                "number_of_hosts_only_in_jobs": 1,
            },
            "hosts": [
                {
                    "created": "<CREATED_DATE>",
                    "host_id": 1,
                    "last_job": None,
                    "modified": "<MODIFIED_DATE>",
                    "name": "<LISTED_HOST>",
                }
            ],
            "instance_details": {
                "active_node": "<NODE_IP>",
                "system_name": "<NODE_IP>",
                "version": "<ANSIBLE_CONTROLLER_VERSION>",
            },
            "jobs": {
                "job_ids": [1, 2],
                "unique_hosts": ["<DELETED_HOST>", "<LISTED_HOST>"],
            },
        },
    ]


@pytest.fixture
def fingerprint_fact_map():
    """Return fingerprint to raw fact map."""
    return {
        "name": "instance_details__system_name",
        "os_version": "instance_details__version",
    }


@pytest.fixture
def expected_fingerprints():
    """Return expected fingerprints for ansible controller."""
    return {
        "name": "<NODE_IP>",
        "os_version": "<ANSIBLE_CONTROLLER_VERSION>",
    }


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.usefixtures("mocked_requests")
class TestAnsibleScan(Smoker):
    """Smoke test Ansible automation controller scanner."""

    MAX_RETRIES = 10
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = "ansible"

    @pytest.fixture
    def credential_payload(self):
        """Return payload to create ansible credential."""
        return {
            "name": "testing credential",
            "username": "<USER>",
            "password": "<PASSWORD>",
        }

    @pytest.fixture
    def source_payload(self):
        """Return Payload used to create ansible source."""
        return {
            "hosts": ["ansible-controller.host"],
            "name": self.SOURCE_NAME,
        }

    def test_insights_report(self, client_logged_in, report_id):
        """Smoke test insights report."""
        response = client_logged_in.get(f"reports/{report_id}/insights/")
        assert (
            response.status_code == 404
        ), "'systems' from ansible sources should not be part of insights report"
