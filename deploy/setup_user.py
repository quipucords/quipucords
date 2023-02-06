#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Setup admin user for quipucords server."""

import os

from django.contrib.auth.models import User

QPC_SERVER_USERNAME = os.environ.get("QPC_SERVER_USERNAME", "admin")
QPC_SERVER_USER_EMAIL = os.environ.get("QPC_SERVER_USER_EMAIL", "admin@example.com")
QPC_SERVER_PASSWORD = os.environ.get("QPC_SERVER_PASSWORD", "qpcpassw0rd")

ADMIN_NOT_PRESENT = User.objects.filter(username=QPC_SERVER_USERNAME).count() == 0

if ADMIN_NOT_PRESENT:
    User.objects.create_superuser(
        QPC_SERVER_USERNAME, QPC_SERVER_USER_EMAIL, QPC_SERVER_PASSWORD
    )
    print(f"Created user {QPC_SERVER_USERNAME}")
else:
    print(f"User {QPC_SERVER_USERNAME} already exists")
