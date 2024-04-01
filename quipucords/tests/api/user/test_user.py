"""Test the API application."""

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse

pytestmark = pytest.mark.django_db  # all user tests require the database


def test_current(qpc_user_simple, client_logged_in):
    """Test the current API endpoint."""
    url = reverse("v1:users-current")
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {"username": qpc_user_simple.username}


def test_logout_sends_clear_header(client_logged_in):
    """Test that user logout sends the Clear-Site-Data header."""
    logout_url = reverse("v1:users-logout")
    response = client_logged_in.put(logout_url)
    assert response.ok
    assert "Clear-Site-Data" in response.headers
    assert response.content == b""


def test_logout_deletes_token(qpc_user_simple, client_logged_in):
    """Test that user logout deletes its auth tokens."""
    auth_token, _ = Token.objects.get_or_create(user=qpc_user_simple)
    assert auth_token is not None
    logout_url = reverse("v1:users-logout")
    response = client_logged_in.put(logout_url)
    assert response.ok
    assert Token.objects.filter(user=qpc_user_simple).count() == 0
