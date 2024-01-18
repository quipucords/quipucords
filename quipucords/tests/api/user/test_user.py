"""Test the API application."""


import pytest
from rest_framework import status
from rest_framework.reverse import reverse


@pytest.mark.django_db
class TestUser:
    """Test the basic user APIs."""

    def test_current(self, qpc_user, django_client):
        """Test the current API endpoint."""
        url = reverse("users-current")
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"username": qpc_user.username}
