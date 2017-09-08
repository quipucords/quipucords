#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the API application"""

from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
from . import models


class HostCredentialTest(TestCase):
    """ Tests against the HostCredential model and view set"""
    # pylint: disable= no-self-use
    def create_hostcredential(self, name="test_cred",
                              username="testuser", password="testpass"):
        """Creates a HostCredential model for use within test cases

        :param name: name of the host credential
        :param username: the user used during the discovery and inspection
        :param password: the connection password
        :returns: A HostCredential model
        """
        return models.HostCredential.objects.create(name=name,
                                                    username=username,
                                                    password=password,
                                                    created=timezone.now())

    def test_hostcred_creation(self):
        """Tests the creation of a HostCredential model and asserts its type"""
        host_cred = self.create_hostcredential()
        self.assertTrue(isinstance(host_cred, models.HostCredential))

    def test_hostcred_list_view(self):
        """Tests the list view set of the HostCredential API"""
        url = reverse("hostcred-list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
