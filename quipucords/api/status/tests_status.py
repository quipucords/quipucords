"""Test the status API view."""

from django.test import TestCase
from django.urls import reverse

from quipucords.environment import server_version


class StatusTest(TestCase):
    """Tests the status view."""

    def test_status_endpoint(self):
        """Test the status endpoint."""
        url = reverse("server-status")
        response = self.client.get(url)
        assert response.has_header("X-Server-Version")
        assert response["X-Server-Version"] == server_version()
        json_result = response.json()
        assert json_result["api_version"] == 1
