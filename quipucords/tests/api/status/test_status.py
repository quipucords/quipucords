"""Test the status API view."""

import pytest
from rest_framework.reverse import reverse

from quipucords.environment import server_version


class TestStatus:
    """Tests the status view."""

    @pytest.mark.django_db
    def test_status_endpoint(self, client_logged_in):
        """Test the status endpoint."""
        url = reverse("v1:server-status")
        response = client_logged_in.get(url)
        assert response.headers.get("X-Server-Version")
        assert response.headers["X-Server-Version"] == server_version()
        assert response.json()["api_version"] == 1

    def test_ping_endpoint(self, client_logged_out):
        """Test the public ping endpoint."""
        url = reverse("v1:server-ping")
        response = client_logged_out.get(url)
        assert response.headers.get("Content-type") == "text/plain"
        assert response.text == "pong"
