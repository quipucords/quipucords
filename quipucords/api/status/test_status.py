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
        self.assertTrue(response.has_header("X-Server-Version"))
        self.assertEqual(response["X-Server-Version"], server_version())
        json_result = response.json()
        self.assertEqual(json_result["api_version"], 1)
