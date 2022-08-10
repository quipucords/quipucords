#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the API application."""

# pylint: disable=imported-auth-user
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
