"""Integration test for ACS scanner."""

import re

import pytest

from tests.integration.test_smoker import Smoker


@pytest.fixture
def max_date(faker):
    """Return mock date."""
    return str(faker.date_time())


@pytest.fixture
def mocked_requests(requests_mock, live_server, max_date):
    """
    Mock all requests a scanner will make.

    Mocked responses contain only the data we care about (otherwise this module would be
    unreadable).
    """
    # allow calling all endpoints on django live server
    django_url_matcher = re.compile(rf"{live_server.url}.*")
    for method in ("GET", "POST"):
        requests_mock.register_uri(method, django_url_matcher, real_http=True)
    acs_host = "https://acs.host:443"
    requests_mock.get(f"{acs_host}/v1/ping")
    requests_mock.get(
        f"{acs_host}/v1/product/usage/secured-units/current",
        json={"numNodes": "3", "numCpuUnits": "20"},
    )

    requests_mock.get(
        f"{acs_host}/v1/product/usage/secured-units/max",
        json={
            "maxNodesAt": max_date,
            "maxNodes": "4",
            "maxCpuUnitsAt": max_date,
            "maxCpuUnits": "30",
        },
    )


@pytest.fixture
def expected_facts(max_date):
    """Return expected facts for ACS."""
    return [
        {
            "secured_units_current": {"numNodes": "3", "numCpuUnits": "20"},
            "secured_units_max": {
                "maxNodesAt": max_date,
                "maxNodes": "4",
                "maxCpuUnitsAt": max_date,
                "maxCpuUnits": "30",
            },
        }
    ]


@pytest.fixture
def fingerprint_fact_map():
    """Return fingerprint to raw fact map."""
    return {
        "name": "N/A",
    }


@pytest.fixture
def expected_fingerprints():
    """Return expected fingerprints for ACS."""
    return {
        "name": "collected-from-acs",
    }


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.usefixtures("mocked_requests")
class TestACSScan(Smoker):
    """Smoke test ACS scanner."""

    MAX_RETRIES = 10
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = "acs"

    @pytest.fixture
    def credential_payload(self):
        """Return payload to create ACS credential."""
        return {
            "name": "testing credential",
            "auth_token": "<AUTH_TOKEN>",
        }

    @pytest.fixture
    def source_payload(self):
        """Return Payload used to create ACS source."""
        return {
            "hosts": ["acs.host"],
            "name": self.SOURCE_NAME,
        }

    def test_insights_report(self, django_client, report_id):
        """Smoke test insights report."""
        response = django_client.get(f"reports/{report_id}/insights/")
        assert (
            response.status_code == 404
        ), "'systems' from acs sources should not be part of insights report"
