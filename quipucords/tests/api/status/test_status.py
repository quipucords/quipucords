"""Test the status API view."""

from rest_framework.reverse import reverse

from quipucords.environment import server_version


class TestStatus:
    """Tests the status view."""

    def test_status_endpoint(self, django_client):
        """Test the status endpoint."""
        url = reverse("server-status")
        response = django_client.get(url)
        assert response.headers.get("X-Server-Version")
        assert response.headers["X-Server-Version"] == server_version()
        assert response.json()["api_version"] == 1
