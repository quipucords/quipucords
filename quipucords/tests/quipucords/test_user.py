"""Test user module."""

import re

import pytest
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError

from quipucords import settings
from quipucords.user import create_random_password

User = get_user_model()


class TestUserRandomPasswords:
    """Tests to verify user module functions."""

    def test_create_random_password_size(self):
        """Test user random password is minimum size."""
        assert len(create_random_password()) == settings.QPC_MINIMUM_PASSWORD_LENGTH

    def test_create_random_password_includes_allowed_characters(self):
        """Test user random password includes only allowed characters."""
        random_password = create_random_password()
        assert re.search("[a-zA-Z0-9]*", random_password).group() == random_password


class TestUserPasswordValidators:
    """Tests the user password validators that we imposed."""

    def test_minimum_size(self):
        """Test that we impose a minimum size."""
        with pytest.raises(ValidationError, match="This password is too short"):
            password_validation.validate_password("hjK4")

    def test_reject_common_words(self):
        """Test that we reject common words."""
        with pytest.raises(ValidationError, match="This password is too common"):
            password_validation.validate_password("hello")

    def test_reject_qpc_common_words(self):
        """Test that we reject quipucords common words."""
        with pytest.raises(ValidationError, match="This password is too common"):
            password_validation.validate_password("qpcpassw0rd")

    def test_reject_all_numeric(self):
        """Test that we reject all numeric passwords."""
        with pytest.raises(ValidationError, match="This password is entirely numeric"):
            password_validation.validate_password("9812319372384")

    @pytest.mark.django_db
    def test_reject_user_attribute_similarities(self):
        """Test that we reject passwords that are similar to user attributes."""
        test_user = User.objects.create_superuser(
            "test", "test@example.com", "Pass1234User"
        )
        with pytest.raises(
            ValidationError, match="The password is too similar to the username"
        ):
            password_validation.validate_password("test", user=test_user)
