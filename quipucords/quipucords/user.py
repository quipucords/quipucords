"""Utilities for User management."""

from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import transaction

User = get_user_model()


class InvalidPasswordError(ValidationError):
    """Custom exception for invalid passwords."""


def make_random_password():
    """Create a random password for a User."""
    return User.objects.make_random_password(settings.QPC_MINIMUM_PASSWORD_LENGTH)


def validate_password(password: str, user: User | None = None):
    """Validate the given password."""
    try:
        password_validation.validate_password(password, user)
    except ValidationError as error:
        raise InvalidPasswordError(error)


def update_password(user: User, password: str):
    """Update the password for a User."""
    validate_password(password, user)
    user.set_password(password)
    user.save()


@transaction.atomic
def create_or_update_user(
    username: str, email: str, password: str | None
) -> tuple[bool, bool, str | None]:
    """
    Create or update a User, optionally with a random password.

    If a User does not exist, create a new User.
    If a User does not exist and no password is given, use a random password.
    If a User already exists and a password is given, update the User.
    If a User already exits and no password is given, make no changes.

    Note: To preserve legacy behavior, this function does not update the User's
    email address if an existing user is found with the given username but the
    email address does not match. At the time of this writing, nothing in the
    server uses the email address; so, this omission probably doesn't matter.

    Returns a tuple containing:
    - "created" bool True if a new User was created, False otherwise.
    - "updated" bool True if an existing User was updated, False otherwise.
    - "password" str contains the new password only if a new random password was set.
    """
    if password:
        validate_password(password)
    user, created = User.objects.get_or_create(
        username=username, defaults={"email": email}
    )
    updated = not created and password is not None
    generate_password = created and password is None
    if generate_password:
        password = make_random_password()
    if created or updated:
        update_password(user, password)

    return created, updated, password if generate_password else None
