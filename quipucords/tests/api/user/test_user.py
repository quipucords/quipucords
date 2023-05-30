"""Test the API application."""


from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.views import UserViewSet


class UserTest(TestCase):
    """Test the basic user APIs."""

    def setUp(self):
        """Create test case setup."""
        self.user = User.objects.create_superuser("test", "test@example.com", "pass")

    def test_current(self):
        """Test the current API endpoint."""
        url = reverse("users-current")
        factory = APIRequestFactory()
        request = factory.get(url, content_type="application/json")
        force_authenticate(request, user=self.user)
        user_current = UserViewSet.as_view({"get": "current"})
        response = user_current(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
