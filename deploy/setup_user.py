"""Setup admin user for quipucords server."""

import os
import sys

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError

from quipucords.user import create_random_password

User = get_user_model()

QPC_SERVER_USERNAME = os.environ.get("QPC_SERVER_USERNAME", "admin")
QPC_SERVER_USER_EMAIL = os.environ.get("QPC_SERVER_USER_EMAIL", "admin@example.com")
QPC_SERVER_PASSWORD = os.environ.get("QPC_SERVER_PASSWORD")


def validate_server_password(password):
    """Validate the server password specified."""
    # We want to make sure the server password specified passes our password validators.
    # If validation fails, let's display the errors for the failed validations
    # and trigger a failure exit.
    try:
        password_validation.validate_password(password)
    except ValidationError as error:
        print("Invalid server password specified:", file=sys.stderr)
        for err in error:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)


ADMIN_NOT_PRESENT = User.objects.filter(username=QPC_SERVER_USERNAME).count() == 0

if ADMIN_NOT_PRESENT:
    use_random_password = not QPC_SERVER_PASSWORD
    if use_random_password:
        QPC_SERVER_PASSWORD = create_random_password()
    else:
        validate_server_password(QPC_SERVER_PASSWORD)
    User.objects.create_superuser(
        QPC_SERVER_USERNAME, QPC_SERVER_USER_EMAIL, QPC_SERVER_PASSWORD
    )
    if use_random_password:
        print(
            f"Created user {QPC_SERVER_USERNAME}"
            f" with random password {QPC_SERVER_PASSWORD}"
        )
    else:
        print(f"Created user {QPC_SERVER_USERNAME}")
elif QPC_SERVER_PASSWORD:
    # Note: If the QPC_SERVER_PASSWORD is specified, that may be coming to us
    # from an OpenShift or Kubernetes secret, we need to update the admin password
    # accordingly.
    validate_server_password(QPC_SERVER_PASSWORD)
    user = User.objects.get(username=QPC_SERVER_USERNAME)
    user.set_password(QPC_SERVER_PASSWORD)
    user.save()
    print(f"User {QPC_SERVER_USERNAME} already exists, updated password")
else:
    print(f"User {QPC_SERVER_USERNAME} already exists")
