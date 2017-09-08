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

from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
from . import models



class HostCredentialTest(TestCase):

    def create_hostcredential(self, name="test_cred",
                              username="testuser", password="testpass"):
        return models.HostCredential.objects.create(name=name,
                                                    username=username,
                                                    password=password,
                                                    created=timezone.now())

    def test_hostcred_creation(self):
        hc = self.create_hostcredential()
        self.assertTrue(isinstance(hc, models.HostCredential))

    def test_hostcred_list_view(self):
        hc = self.create_hostcredential()
        url = reverse("hostcred-list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
