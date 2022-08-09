#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
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
