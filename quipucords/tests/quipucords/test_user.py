"""Test user module."""

import re

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import override_settings

from quipucords.user import (
    InvalidPasswordError,
    create_or_update_user,
    make_random_password,
    validate_password,
)

User = get_user_model()


class TestUserRandomPasswords:
    """Tests to verify user module functions."""

    def test_make_random_password_size(self):
        """Test user random password is minimum size."""
        assert len(make_random_password()) == settings.QPC_MINIMUM_PASSWORD_LENGTH

    def test_make_random_password_includes_allowed_characters(self):
        """Test user random password includes only allowed characters."""
        random_password = make_random_password()
        assert re.search("[a-zA-Z0-9]*", random_password).group() == random_password


class TestUserPasswordValidators:
    """Tests the user password validators that we imposed."""

    def test_minimum_size(self):
        """Test that we impose a minimum size."""
        with pytest.raises(ValidationError, match="This password is too short"):
            validate_password("hjK4")

    @pytest.mark.parametrize("password", ["hello", "qpcpassw0rd", "dscpassw0rd"])
    def test_reject_common_words(self, password):
        """Test that we reject common words."""
        with pytest.raises(ValidationError, match="This password is too common"):
            validate_password(password)

    def test_reject_all_numeric(self):
        """Test that we reject all numeric passwords."""
        with pytest.raises(ValidationError, match="This password is entirely numeric"):
            validate_password("9812319372384")

    @pytest.mark.django_db
    def test_reject_user_attribute_similarities(self):
        """Test that we reject passwords that are similar to user attributes."""
        test_user = User.objects.create_superuser(
            "test", "test@example.com", "Pass1234User"
        )
        with pytest.raises(
            ValidationError, match="The password is too similar to the username"
        ):
            validate_password("test", user=test_user)


@pytest.mark.django_db
class TestCreateOrUpdateUser:
    """Test create_or_update_user with various inputs."""

    def test_new_user_no_password(self, client, faker):
        """Test create_or_update_user with a new username and no password."""
        username = faker.name()
        email = faker.email()
        password = None
        created, updated, generated_password = create_or_update_user(
            username, email, password
        )
        assert created
        assert not updated
        assert generated_password
        assert User.objects.filter(username=username).exists()
        with override_settings(AXES_ENABLED=False):
            assert client.login(username=username, password=generated_password)

    def test_new_user_good_password(self, client, faker):
        """Test create_or_update_user with a new username and a good password."""
        username = faker.name()
        email = faker.email()
        password = f"{faker.password(length=settings.QPC_MINIMUM_PASSWORD_LENGTH)}"
        created, updated, generated_password = create_or_update_user(
            username, email, password
        )
        assert created
        assert not updated
        assert not generated_password
        assert User.objects.filter(username=username).exists()
        with override_settings(AXES_ENABLED=False):
            assert client.login(username=username, password=password)

    def test_new_user_bad_password(self, faker):
        """Test create_or_update_user with a new username and a bad password."""
        username = faker.name()
        email = faker.email()
        password = "1"
        with pytest.raises(InvalidPasswordError):
            create_or_update_user(username, email, password)
        assert not User.objects.filter(username=username).exists()

    def test_update_user_no_password(self, qpc_user_simple: User):
        """Test create_or_update_user with an existing username and no password."""
        old_password_hash = qpc_user_simple.password
        password = None
        created, updated, generated_password = create_or_update_user(
            qpc_user_simple.username, None, password
        )
        assert not created
        assert not updated
        assert not generated_password
        qpc_user_simple.refresh_from_db()
        assert old_password_hash == qpc_user_simple.password

    def test_update_user_good_password(self, client, faker, qpc_user_simple: User):
        """Test create_or_update_user with an existing username and a good password."""
        username = qpc_user_simple.username
        password = f"{faker.password(length=settings.QPC_MINIMUM_PASSWORD_LENGTH)}"
        created, updated, generated_password = create_or_update_user(
            username, None, password
        )
        assert not created
        assert updated
        assert not generated_password
        with override_settings(AXES_ENABLED=False):
            assert client.login(username=username, password=password)

    def test_update_user_bad_password(self, qpc_user_simple: User):
        """Test create_or_update_user with an existing username and a bad password."""
        old_password_hash = qpc_user_simple.password
        password = "1"
        with pytest.raises(InvalidPasswordError):
            create_or_update_user(qpc_user_simple.username, None, password)
        qpc_user_simple.refresh_from_db()
        assert old_password_hash == qpc_user_simple.password
