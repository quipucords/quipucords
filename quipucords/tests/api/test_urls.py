"""Test quipucords api urls."""


import pytest
from rest_framework.reverse import reverse


@pytest.mark.parametrize(
    "name,kwargs,expected_url",
    (
        ("v1:cred-list", {}, "/api/v1/credentials/"),
        ("v1:cred-detail", {"pk": 1}, "/api/v1/credentials/1/"),
        # why reports (plural)? other named views use singular...
        ("v1:reports-list", {}, "/api/v1/reports/"),
        ("v1:source-list", {}, "/api/v1/sources/"),
        ("v1:source-detail", {"pk": 1}, "/api/v1/sources/1/"),
        ("v1:scan-list", {}, "/api/v1/scans/"),
        ("v1:scan-detail", {"pk": 1}, "/api/v1/scans/1/"),
        ("v1:scan-filtered-jobs", {"scan_id": 1}, "/api/v1/scans/1/jobs/"),
        # why scanjob and not simply "job"? or the other way around?
        ("v1:scanjob-detail", {"pk": 1}, "/api/v1/jobs/1/"),
        ("v1:scanjob-connection", {"pk": 1}, "/api/v1/jobs/1/connection/"),
        ("v1:scanjob-inspection", {"pk": 1}, "/api/v1/jobs/1/inspection/"),
        ("v1:scanjob-pause", {"pk": 1}, "/api/v1/jobs/1/pause/"),
        ("v1:scanjob-cancel", {"pk": 1}, "/api/v1/jobs/1/cancel/"),
        ("v1:scanjob-restart", {"pk": 1}, "/api/v1/jobs/1/restart/"),
        # why users (plural)? other named views use singular...
        ("v1:users-current", {}, "/api/v1/users/current/"),
        ("v1:users-logout", {}, "/api/v1/users/logout/"),
        ("v1:server-status", {}, "/api/v1/status/"),
    ),
)
def test_named_url_resolution(name, kwargs, expected_url):
    """Ensure named urls can be properly resolved."""
    assert reverse(name, kwargs=kwargs) == expected_url
