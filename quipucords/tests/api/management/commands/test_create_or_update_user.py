"""Test the create_or_update_user management command."""

import os
from contextlib import contextmanager
from io import StringIO
from unittest import mock

import pytest
from django.conf import settings
from django.core.management import call_command

from quipucords.user import User

password_failed_requirements_message = (
    "QUIPUCORDS_SERVER_PASSWORD value failed password requirements"
)


@contextmanager
def patch_environ(username=None, password=None):
    """Patch os.environ values used by these tests."""
    new_environ = dict()
    if username:
        new_environ["QUIPUCORDS_SERVER_USERNAME"] = username
    if password:
        new_environ["QUIPUCORDS_SERVER_PASSWORD"] = password
    with mock.patch.dict(os.environ, new_environ, clear=True):
        yield


@pytest.mark.django_db
def test_create_or_update_user_create_with_no_password(faker):
    """Test creation of a user with no password."""
    out = StringIO()
    username = faker.user_name()
    expected_message = f"Created user '{username}' with random password:"
    with patch_environ(username):
        call_command("create_or_update_user", stdout=out)
    assert expected_message in out.getvalue()
    assert password_failed_requirements_message not in out.getvalue()


@pytest.mark.django_db
def test_create_or_update_user_create_with_valid_password(faker):
    """Test creation of a user with a valid password."""
    out = StringIO()
    username = faker.user_name()
    password = faker.password(length=settings.QUIPUCORDS_MINIMUM_PASSWORD_LENGTH)
    expected_message = (
        f"Created user '{username}' with password from QUIPUCORDS_SERVER_PASSWORD"
    )
    with patch_environ(username, password):
        call_command("create_or_update_user", stdout=out)
    assert expected_message in out.getvalue()
    assert password not in out.getvalue()
    assert password_failed_requirements_message not in out.getvalue()


@pytest.mark.django_db
def test_create_or_update_user_fail_create_with_bad_password(faker):
    """Test creating a user with a bad password (generating a better random one)."""
    out = StringIO()
    username = faker.user_name()
    password = "1"
    with patch_environ(username, password):
        call_command("create_or_update_user", stdout=out)
    expected_message = f"Created user '{username}' with random password:"
    assert expected_message in out.getvalue()
    assert password_failed_requirements_message in out.getvalue()


@pytest.mark.django_db
def test_create_or_update_user_update_with_no_password(qpc_user_simple: User):
    """Test updating a user with no password has no effect."""
    out = StringIO()
    username = qpc_user_simple.username
    expected_message = f"User '{username}' already exists and was not updated"
    with patch_environ(username):
        call_command("create_or_update_user", stdout=out)
    assert expected_message in out.getvalue()
    assert password_failed_requirements_message not in out.getvalue()


@pytest.mark.django_db
def test_create_or_update_user_update_with_valid_password(qpc_user_simple: User, faker):
    """Test updating a user with a valid password."""
    out = StringIO()
    username = qpc_user_simple.username
    password = faker.password(length=settings.QUIPUCORDS_MINIMUM_PASSWORD_LENGTH)
    expected_message = (
        f"Updated user '{username}' with password from QUIPUCORDS_SERVER_PASSWORD"
    )
    with patch_environ(username, password):
        call_command("create_or_update_user", stdout=out)
    assert expected_message in out.getvalue()
    assert password not in out.getvalue()
    assert password_failed_requirements_message not in out.getvalue()


@pytest.mark.django_db
def test_create_or_update_user_update_with_bad_password(qpc_user_simple: User):
    """Test updating a user with a bad password (generating a better random one)."""
    out = StringIO()
    username = qpc_user_simple.username
    password = "1"
    with patch_environ(username, password):
        call_command("create_or_update_user", stdout=out)
    expected_message = f"Updated user '{username}' with random password:"
    assert expected_message in out.getvalue()
    assert password_failed_requirements_message in out.getvalue()
