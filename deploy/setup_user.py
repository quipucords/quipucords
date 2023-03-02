"""Setup admin user for quipucords server."""

import os

from django.contrib.auth import get_user_model

User = get_user_model()

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
