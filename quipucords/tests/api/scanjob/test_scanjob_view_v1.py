"""Test ScanJobViewSet v1 and related v1 view functions."""

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.models import ScanTask
from tests.factories import ScanFactory, ScanJobFactory, SourceFactory

pytestmark = pytest.mark.django_db  # all user tests require the database


def test_retrieve(client_logged_in):
    """Get ScanJob details by primary key."""
    scan = ScanFactory()
    scanjob = scan.most_recent_scanjob
    url = reverse("v1:scanjob-detail", args=(scanjob.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert "scan" in response.json()
    scan_json = response.json()["scan"]
    assert scan_json == {"id": scan.id, "name": scan.name}


def test_post_jobs_not_allowed(client_logged_in):
    """Test post jobs not allowed."""
    url = reverse("v1:scanjob-detail", args=(1,))
    url = url[:-2]
    response = client_logged_in.post(url, {})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_not_allowed(client_logged_in):
    """Test list all jobs not allowed."""
    url = reverse("v1:scanjob-detail", args=(1,))
    url = url[:-2]
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_not_allowed(client_logged_in):
    """Test update scanjob not allowed."""
    source = SourceFactory()
    scan = ScanFactory()

    data = {
        "sources": [source.id],
        "scan_type": ScanTask.SCAN_TYPE_INSPECT,
        "options": {
            "disabled_optional_products": {
                "jboss_eap": True,
                "jboss_fuse": True,
                "jboss_ws": True,
            }
        },
    }
    url = reverse("v1:scanjob-detail", args=(scan.most_recent_scanjob.id,))
    response = client_logged_in.put(url, data=data)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_update_not_allowed_disable_optional_products(client_logged_in):
    """Test update scan job options not allowed."""
    scan = ScanFactory()
    scan_job = scan.most_recent_scanjob
    source = SourceFactory()

    data = {
        "sources": [source.id],
        "scan_type": ScanTask.SCAN_TYPE_INSPECT,
        "options": {"disabled_optional_products": "bar"},
    }
    url = reverse("v1:scanjob-detail", args=(scan_job.id,))
    response = client_logged_in.put(url, data=data)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_partial_update(client_logged_in):
    """Test partial update not allow for scanjob."""
    scan = ScanFactory()
    scan_job = scan.most_recent_scanjob

    data = {"scan_type": ScanTask.SCAN_TYPE_INSPECT}
    url = reverse("v1:scanjob-detail", args=(scan_job.id,))
    response = client_logged_in.patch(url, data=data)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_delete(client_logged_in):
    """Delete a ScanJob is not supported."""
    scan_job = ScanJobFactory()

    url = reverse("v1:scanjob-detail", args=(scan_job.id,))
    response = client_logged_in.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_cancel(client_logged_in):
    """Cancel a scanjob."""
    scan_job = ScanJobFactory()
    url = reverse("v1:scanjob-cancel", args=(scan_job.id,))
    response = client_logged_in.put(url)
    assert response.ok


def test_cancel_bad_id(client_logged_in):
    """Cancel a scanjob with bad id."""
    url = reverse("v1:scanjob-cancel", args=("string",))
    response = client_logged_in.put(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
