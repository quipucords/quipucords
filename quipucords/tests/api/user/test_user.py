"""Test the API application."""

import pytest
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse

pytestmark = pytest.mark.django_db  # all user tests require the database


def test_current(qpc_user, django_client):
    """Test the current API endpoint."""
    url = reverse("v1:users-current")
    response = django_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"username": qpc_user.username}


def test_logout_sends_clear_header(qpc_user, django_client):
    """Test that user logout sends the Clear-Site-Data header."""
    logout_url = reverse("v1:users-logout")
    response = django_client.put(logout_url)
    assert response.status_code == status.HTTP_200_OK
    assert "Clear-Site-Data" in response.headers
    assert response.text == ""
