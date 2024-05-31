"""Test user module."""

import re

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from quipucords import settings
from quipucords.user import make_random_password, validate_password

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
