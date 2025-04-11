"""Test the API application."""

import random
import re
from datetime import UTC, timedelta

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.models import Scan, ScanTask
from api.scan.serializer import ScanSerializer
from api.scan.view import expand_scan
from tests.factories import ReportFactory, ScanFactory, SourceFactory
from tests.scanner.test_util import create_scan_job


def disabled_optional_products_default():
    """Return the default disabled_optional_products."""
    disabled_optional_products = {}
    for prod in Scan.SUPPORTED_PRODUCTS:
        prod_def = Scan.PRODUCTS[prod]
        disabled_optional_products[prod_def.name] = not prod_def.enabled
    return disabled_optional_products


def enabled_optional_products_default():
    """Return the default enabled_optional_products."""
    enabled_optional_products = {}
    for prod in Scan.SUPPORTED_PRODUCTS:
        prod_def = Scan.PRODUCTS[prod]
        enabled_optional_products[prod_def.name] = prod_def.enabled
    return enabled_optional_products


def enabled_extended_product_search_default():
    """Return the default enabled_extended_product_search."""
    enabled_extended_product_search = {}
    for prod in Scan.SUPPORTED_PRODUCTS:
        prod_def = Scan.PRODUCTS[prod]
        enabled_extended_product_search[prod_def.name] = prod_def.ext_enabled
    return enabled_extended_product_search


def scan_options_default():
    """Return default scan_options."""
    return {
        "disabled_optional_products": disabled_optional_products_default(),
        "enabled_extended_product_search": enabled_extended_product_search_default(),
    }


@pytest.mark.django_db
class TestScanCreate:
    """Test POST /api/v1/scans/."""

    @pytest.mark.parametrize("scan_type", [ScanTask.SCAN_TYPE_INSPECT, None])
    def test_successful_create(self, client_logged_in, faker, scan_type, mocker):
        """Ensure a scan is successfully created."""
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
        }
        if scan_type:
            payload["scan_type"] = scan_type
            expected_scan_type = scan_type
        else:
            expected_scan_type = ScanTask.SCAN_TYPE_INSPECT
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            "id": mocker.ANY,
            "name": payload["name"],
            "options": {"max_concurrency": 25},
            "scan_type": expected_scan_type,
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                }
            ],
        }

    def test_create_no_name(self, client_logged_in):
        """A create request MUST have a name."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level).
        source = SourceFactory()
        payload = {"sources": [source.id]}
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"name": ["This field is required."]}

    @pytest.mark.parametrize(
        "extra_payload,expected_error_message",
        (
            ({}, "This field is required."),
            ({"sources": []}, "Scan job must have one or more sources."),
        ),
    )
    def test_create_no_source(
        self, extra_payload, expected_error_message, client_logged_in, faker
    ):
        """A create request MUST have a source."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level).
        payload = {"name": faker.bothify("Scan ????-######")}
        payload.update(extra_payload)
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"sources": [expected_error_message]}

    @pytest.mark.parametrize("scan_type", [ScanTask.SCAN_TYPE_FINGERPRINT, "banana"])
    def test_invalid_scan_type(self, client_logged_in, faker, scan_type, mocker):
        """Ensure a scan is successfully created."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level).
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
            "scan_type": scan_type,
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"scan_type": [mocker.ANY]}
        error_message = response.json()["scan_type"][0]
        matched_pattern = re.match(r"(\w+), is an invalid choice.", error_message)
        assert matched_pattern
        assert matched_pattern.group(1) == scan_type

    def test_create_blank_scan_type(self, client_logged_in, faker):
        """A create request must not have a blank scan_type."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level).
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
            "scan_type": "",
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "scan_type": ["This field may not be blank. Valid values are inspect."]
        }

    def test_create_invalid_sources_type(self, client_logged_in, faker):
        """A create request must have integer ids."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level).
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [faker.slug()],
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "sources": ["Source identifiers must be integer values."]
        }

    def test_create_invalid_sources_id(self, client_logged_in, faker):
        """A create request must have integer ids."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level - which SHOULD not be).
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [999999],
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "sources": ["Source with id=999999 could not be found in database."]
        }

    def test_create_with_options(self, client_logged_in, mocker):
        """A valid create request should with valid options input."""
        source = SourceFactory()
        payload = {
            "name": "test",
            "sources": [source.id],
            "options": {
                "disabled_optional_products": {
                    "jboss_eap": True,
                }
            },
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_201_CREATED
        default_max_concurrency = 25
        assert response.json() == {
            "id": mocker.ANY,
            "name": payload["name"],
            # it's extremely odd options will only be part of the response if some
            # part of it is customized.
            # TODO: change this behavior in v2 api
            "options": {
                "disabled_optional_products": {
                    "jboss_eap": True,
                    "jboss_fuse": False,
                    "jboss_ws": False,
                },
                "max_concurrency": default_max_concurrency,
            },
            "scan_type": ScanTask.SCAN_TYPE_INSPECT,
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                }
            ],
        }

    def test_create_invalid_forks(self, client_logged_in, faker):
        """Test valid number of forks."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level - which SHOULD not be).
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
            "options": {
                "max_concurrency": -5,
            },
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "options": {
                "max_concurrency": ["Ensure this value is greater than or equal to 1."]
            }
        }

    def test_create_large_forks(self, client_logged_in, faker):
        """Test valid number of forks with a large number of forks specified."""
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
            "options": {
                "max_concurrency": 10000,
            },
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "options": {
                "max_concurrency": [
                    "Ensure this value is less than"
                    f" or equal to {Scan.UPPER_MAX_CONCURRENCY}."
                ]
            }
        }

    def test_create_disable_optional_products_type(self, client_logged_in, faker):
        """Test invalid type for disabled_optional_products type."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level - which SHOULD not be).
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
            "options": {"disabled_optional_products": "foo"},
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "options": {
                "disabled_optional_products": {
                    "non_field_errors": [
                        "Invalid data. Expected a dictionary, but got str."
                    ]
                }
            }
        }

    @pytest.mark.parametrize("option_value", ("hamburger", "87", 42, "*", []))
    def test_create_disable_optional_products_value_type(
        self, client_logged_in, faker, option_value
    ):
        """Test invalid type for disabled_optional_products value."""
        source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [source.id],
            "options": {"disabled_optional_products": {"jboss_eap": option_value}},
        }
        response = client_logged_in.post(reverse("v1:scan-list"), data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "options": {
                "disabled_optional_products": {
                    "jboss_eap": ["Must be a valid boolean."]
                }
            }
        }


@pytest.mark.django_db
class TestScanRetrieve:
    """Test ScanViewSet retrieve."""

    def test_retrieve(self, client_logged_in, mocker):
        """Get Scan details by primary key."""
        scan = ScanFactory(most_recent_scanjob=None)
        source = scan.sources.first()
        response = client_logged_in.get(reverse("v1:scan-detail", args=(scan.id,)))
        assert response.ok, response.json()
        assert response.json() == {
            "id": scan.id,
            "name": scan.name,
            "scan_type": scan.scan_type,
            "options": {"max_concurrency": 25},
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                }
            ],
        }

    def test_retrieve_bad_id(self, client_logged_in):
        """Attempt to get scan details with bad pk."""
        # TODO: this and many other negative tests here seem to be in the wrong place.
        # They are probably better done at Serializer level (assuming the logic is not
        # at view level - which SHOULD not be).
        response = client_logged_in.get(reverse("v1:scan-detail", args=("invalid",)))
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestScanUpdate:
    """Test ScanViewSet update."""

    def test_update(self, client_logged_in, faker):
        """Completely update a scan."""
        scan = ScanFactory()
        ReportFactory(scanjob=scan.most_recent_scanjob)
        url = reverse("v1:scan-detail", args=(scan.id,))
        original_response = client_logged_in.get(url)
        assert original_response.ok
        original_json = original_response.json()

        new_source = SourceFactory()
        payload = {
            "name": faker.bothify("Scan ????-######"),
            "sources": [new_source.id],
            "scan_type": ScanTask.SCAN_TYPE_INSPECT,
        }
        response = client_logged_in.put(url, data=payload)
        assert response.ok, response.json()
        assert response.json() != original_json

        assert response.json() == {
            "id": scan.id,
            "most_recent_scanjob": scan.most_recent_scanjob.id,
            "options": {"max_concurrency": 25},
            "jobs": [
                {
                    "id": scan.most_recent_scanjob.id,
                    "report_id": scan.most_recent_scanjob.report_id,
                }
            ],
            **payload,
        }

    def test_partial_update_retains(self, client_logged_in):
        """Test partial update retains unprovided info."""
        scan = ScanFactory()
        ReportFactory(scanjob=scan.most_recent_scanjob)
        url = reverse("v1:scan-detail", args=(scan.id,))
        original_response = client_logged_in.get(url)
        assert original_response.ok
        original_json = original_response.json()

        response_update = client_logged_in.patch(url, data={"name": "NEW NAME"})
        assert response_update.ok
        assert response_update.json() == {
            "id": original_json["id"],
            "most_recent_scanjob": scan.most_recent_scanjob.id,
            "jobs": [
                {
                    "id": scan.most_recent_scanjob.id,
                    "report_id": scan.most_recent_scanjob.report_id,
                }
            ],
            "name": "NEW NAME",
            "scan_type": original_json["scan_type"],
            "options": {"max_concurrency": 25},
            "sources": [original_json["sources"][0]["id"]],
        }

    def test_partial_update_sources(self, client_logged_in):
        """Test partial update on sources."""
        scan = ScanFactory()
        ReportFactory(scanjob=scan.most_recent_scanjob)
        original_source = scan.sources.first()
        new_source = SourceFactory()
        assert original_source.id != new_source.id
        url = reverse("v1:scan-detail", args=(scan.id,))
        response = client_logged_in.patch(url, data={"sources": [new_source.id]})
        assert response.ok, response.json()
        assert response.json() == {
            "id": scan.id,
            "most_recent_scanjob": scan.most_recent_scanjob.id,
            "jobs": [
                {
                    "id": scan.most_recent_scanjob.id,
                    "report_id": scan.most_recent_scanjob.report_id,
                }
            ],
            "name": scan.name,
            "scan_type": scan.scan_type,
            "options": {"max_concurrency": 25},
            "sources": [new_source.id],
        }

    def test_partial_update_options(self, client_logged_in):
        """Test partial update of options on sources."""
        scan = ScanFactory()
        url = reverse("v1:scan-detail", args=(scan.id,))
        max_concurrency = random.randint(1, 49)
        payload = {
            "options": {
                "disabled_optional_products": {
                    "jboss_ws": True,
                },
                "max_concurrency": max_concurrency,
            },
        }
        response = client_logged_in.patch(url, data=payload)
        assert response.ok, response.json()
        assert response.json() == {
            "id": scan.id,
            "most_recent_scanjob": scan.most_recent_scanjob.id,
            "jobs": [{"id": scan.most_recent_scanjob.id}],
            "options": {
                "disabled_optional_products": {
                    "jboss_eap": False,
                    "jboss_fuse": False,
                    "jboss_ws": True,
                },
                "max_concurrency": max_concurrency,
            },
            "name": scan.name,
            "scan_type": scan.scan_type,
            "sources": [s.id for s in scan.sources.all()],
        }

    def test_partial_update_name(self, client_logged_in):
        """Test partial update on sources."""
        scan = ScanFactory()
        new_scan_data = ScanFactory.build()
        url = reverse("v1:scan-detail", args=(scan.id,))
        assert scan.name != new_scan_data.name
        response = client_logged_in.patch(url, data={"name": new_scan_data.name})
        assert response.ok, response.json()
        assert response.json() == {
            "id": scan.id,
            "most_recent_scanjob": scan.most_recent_scanjob.id,
            "jobs": [{"id": scan.most_recent_scanjob.id}],
            "name": new_scan_data.name,
            "scan_type": scan.scan_type,
            "options": {"max_concurrency": 25},
            "sources": [s.id for s in scan.sources.all()],
        }

    def test_partial_update_enabled(self, client_logged_in):
        """Test partial update retains unprovided info."""
        scan = ScanFactory(
            enabled_extended_product_search=enabled_extended_product_search_default(),
            enabled_optional_products=enabled_optional_products_default(),
        )
        url = reverse("v1:scan-detail", args=(scan.id,))
        original_response = client_logged_in.get(url)
        assert original_response.ok
        original_json = original_response.json()

        payload = {
            "options": {
                "enabled_extended_product_search": {
                    "search_directories": ["/some/path/"]
                }
            }
        }
        response_patch = client_logged_in.patch(url, data=payload)
        assert response_patch.ok, response_patch.json()

        updated_response = client_logged_in.get(url)
        assert updated_response.ok, updated_response.json()
        assert updated_response.json() != original_json
        expected_result = original_json
        expected_result["options"]["enabled_extended_product_search"][
            "search_directories"
        ] = ["/some/path/"]
        assert updated_response.json() == expected_result

    def test_partial_update_scan_type(self, client_logged_in, faker):
        """Test partial update retains unprovided info."""
        scan = ScanFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        url = reverse("v1:scan-detail", args=(scan.id,))
        new_name = faker.slug()
        response = client_logged_in.patch(
            url,
            data={"name": new_name},
        )
        assert response.ok, response.json()
        assert response.json()["name"] == new_name


@pytest.mark.django_db
def test_expand_scan():
    """Test view expand_scan."""
    source = SourceFactory()
    scan_job, scan_task = create_scan_job(source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
    scan_task.update_stats(
        "TEST_VC.", sys_count=2, sys_failed=1, sys_scanned=1, sys_unreachable=0
    )

    serializer = ScanSerializer(scan_job.scan)
    json_scan = serializer.data
    json_scan = expand_scan(json_scan)
    assert json_scan["sources"].first()["name"] == source.name
    assert json_scan["most_recent"] == {
        "id": scan_job.id,
        "scan_type": ScanTask.SCAN_TYPE_INSPECT,
        "status": scan_job.status,
        "status_details": {"job_status_message": "Job is pending."},
    }


@pytest.mark.django_db
def test_delete(client_logged_in):
    """Delete a scan."""
    scan = ScanFactory()
    url = reverse("v1:scan-detail", args=(scan.id,))
    response = client_logged_in.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Scan.objects.count() == 0


@pytest.mark.django_db
class TestScanList:
    """Test ScanViewSet list."""

    @pytest.fixture
    def expected_scans(self, faker, mocker):
        """Return a 'json' with 2 Scan objects."""
        start_time1 = faker.date_time(tzinfo=UTC)
        scan1 = ScanFactory(
            name="SCAN1",
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            most_recent_scanjob__start_time=start_time1,
        )
        # scan 2 has start time before scan1 - this will be useful
        # to test ordering
        start_time2 = start_time1 - timedelta(days=1)
        scan2 = ScanFactory(
            name="SCAN2",
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            most_recent_scanjob__start_time=start_time2,
        )
        expected_results = []
        for scan in [scan1, scan2]:
            source = scan.sources.first()
            data = {
                "id": scan.id,
                "name": scan.name,
                "scan_type": scan.scan_type,
                "most_recent": mocker.ANY,
                "jobs": mocker.ANY,
                "options": {"max_concurrency": 25},
                "sources": [
                    {
                        "id": source.id,
                        "name": source.name,
                        "source_type": source.source_type,
                    }
                ],
            }
            expected_results.append(data)
        return expected_results

    def test_list(self, client_logged_in, expected_scans):
        """List Scan objects."""
        response = client_logged_in.get(reverse("v1:scan-list"))
        assert response.ok, response.json()
        assert response.json() == {
            "count": 2,
            "next": None,
            "previous": None,
            "results": expected_scans,
        }

    def test_filtered_list(self, client_logged_in, expected_scans):
        """Test filtered scan list."""
        response = client_logged_in.get(reverse("v1:scan-list"), data={"name": "SCAN1"})
        assert response.ok, response.json()
        assert response.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            # first of expected_scans is the only result
            "results": [expected_scans[0]],
        }

    def test_list_by_scanjob_end_time(self, client_logged_in, expected_scans):
        """List all scan objects, ordered by ScanJob start time."""
        response = client_logged_in.get(
            reverse("v1:scan-list"),
            data={"ordering": "most_recent_scanjob__start_time"},
        )
        assert response.ok, response.json()
        assert response.json() == {
            "count": 2,
            "next": None,
            "previous": None,
            # second scan started before first
            "results": expected_scans[::-1],
        }
