"""Test SecureToken model."""

from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from api.secure_token.model import SecureToken
from quipucords.user import make_random_password

TOKEN_TYPE_INSIGHTS = "insights-jwt"

User = get_user_model()


@pytest.fixture
def test_user(faker):
    """Fixture to create a test user."""
    return User.objects.create(
        username=faker.name(),
        email=faker.email(),
        password=make_random_password(),
    )


@pytest.fixture()
def test_jwt(faker):
    """Fixture to create a test JWT token."""
    jwt = f"{faker.lexify('?' * 32)}.{faker.lexify('?' * 32)}.{faker.lexify('?' * 32)}"
    print(f"\nJWT = {jwt}")
    return jwt


@pytest.mark.django_db
class TestSecureToken:
    """Test SecureToken model."""

    def test_create_without_token_type(self, faker):
        """Test create fails with missing token type."""
        with pytest.raises(ValidationError) as validation_error:
            SecureToken.objects.create(name=faker.slug())
        token_type_error = validation_error.value.message_dict["token_type"]
        assert "This field cannot be blank" in str(token_type_error)

    def test_create_without_invalid_token_type(self, faker):
        """Test create fails with invalid token type."""
        invalid_token_type = "bogus_token_type"
        with pytest.raises(ValidationError) as validation_error:
            SecureToken.objects.create(name=faker.slug(), token_type=invalid_token_type)
        token_type_error = validation_error.value.message_dict["token_type"]
        assert f"Value '{invalid_token_type}' is not a valid choice" in str(
            token_type_error
        )

    def test_create_with_duplicate_name(self, faker):
        """Test create fails with duplicate token name."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        SecureToken.objects.create(name=token_name, token_type=token_type)
        with pytest.raises(ValidationError) as validation_error:
            SecureToken.objects.create(name=token_name, token_type=token_type)
        error_messages = ", ".join(validation_error.value.message_dict["__all__"])
        assert "unique_secure_token_name" in error_messages

    def test_create_with_empty_token(self, faker):
        """Test create succeeds with empty token."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token=None, token_type=token_type
        )
        secure_token.refresh_from_db()
        assert secure_token.token is None

    def test_create_with_empty_metadata(self, faker):
        """Test create succeeds with empty metadata."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, metadata=None, token_type=token_type
        )
        secure_token.refresh_from_db()
        assert secure_token.metadata is None

    def test_create_with_empty_token_and_metadata(self, faker):
        """Test create succeeds with empty token and metadata."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token=None, metadata=None, token_type=token_type
        )
        secure_token.refresh_from_db()
        assert secure_token.token is None
        assert secure_token.metadata is None

    def test_create(self, faker):
        """Test create a SecureToken - Happy Path."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token_type=token_type
        )
        secure_token.refresh_from_db()
        assert secure_token.name == token_name
        assert secure_token.token_type == token_type


@pytest.mark.django_db
class TestUserSecureToken:
    """Test SecureToken model bound to a user."""

    def test_create_without_token_type(self, faker, test_user):
        """Test create fails with missing token type."""
        token_name = faker.slug()
        with pytest.raises(ValidationError) as validation_error:
            SecureToken.objects.create(name=token_name, user=test_user)
        token_type_error = validation_error.value.message_dict["token_type"]
        assert "This field cannot be blank" in str(token_type_error)

    def test_create_without_invalid_token_type(self, faker, test_user):
        """Test create fails with invalid token type."""
        token_name = faker.slug()
        invalid_token_type = "bogus_token_type"
        with pytest.raises(ValidationError) as validation_error:
            SecureToken.objects.create(
                name=token_name, token_type=invalid_token_type, user=test_user
            )
        token_type_error = validation_error.value.message_dict["token_type"]
        assert f"Value '{invalid_token_type}' is not a valid choice" in str(
            token_type_error
        )

    def test_create_with_duplicate_name(self, faker, test_user):
        """Test create fails with duplicate token name."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        SecureToken.objects.create(
            name=token_name, token_type=token_type, user=test_user
        )
        with pytest.raises(ValidationError) as validation_error:
            SecureToken.objects.create(
                name=token_name, token_type=token_type, user=test_user
            )
        error_messages = ", ".join(validation_error.value.message_dict["__all__"])
        assert "Secure Token with this User and Name already exists" in error_messages

    def test_delete_user_deletes_secure_tokens(self, faker, test_user):
        """Test that deleting a user also deletes the user's secure tokens."""
        token_type = TOKEN_TYPE_INSIGHTS
        token1_name = faker.slug()
        token2_name = faker.slug()
        SecureToken.objects.create(
            name=token1_name, token_type=token_type, user=test_user
        )
        SecureToken.objects.create(
            name=token2_name, token_type=token_type, user=test_user
        )
        test_user.delete()
        assert not SecureToken.objects.filter(name=token1_name).exists()
        assert not SecureToken.objects.filter(name=token2_name).exists()

    def test_tokens_and_metadata_are_returned_unencrypted(
        self, faker, test_user, test_jwt
    ):
        """Test that makes sure encrypted fields are returned unencrypted."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        token = test_jwt
        token_metadata = {
            "insights_user": faker.pyint(min_value=101),
            "insights_group": faker.pyint(min_value=101),
        }
        secure_token = SecureToken.objects.create(
            name=token_name,
            token_type=token_type,
            user=test_user,
            token=token,
            metadata=token_metadata,
        )
        secure_token.refresh_from_db()
        assert secure_token.token == test_jwt
        assert secure_token.metadata == token_metadata

    def test_create(self, faker, test_user):
        """Test create a user SecureToken - Happy Path."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token_type=token_type, user=test_user
        )
        secure_token.refresh_from_db()
        assert secure_token.name == token_name
        assert secure_token.token_type == token_type
        assert secure_token.user.username == test_user.username


@pytest.mark.django_db
class TestUserSecureTokenExpiration:
    """Test user SecureToken expiration."""

    def test_create_default_expiration(self, faker, test_user):
        """Test create a user SecureToken - Happy Path."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token_type=token_type, user=test_user
        )
        secure_token.refresh_from_db()
        assert not secure_token.is_expired()

    def test_create_set_expiration_future(self, faker, test_user):
        """Test future expiration date."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token_type=token_type, user=test_user
        )
        secure_token.refresh_from_db()
        secure_token.set_expiration(expires_at=datetime.now(UTC) + timedelta(hours=4))
        assert not secure_token.is_expired()

    def test_create_set_expiration_past(self, faker, test_user):
        """Test past expiration date."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name, token_type=token_type, user=test_user
        )
        secure_token.refresh_from_db()
        assert not secure_token.is_expired()
        secure_token.set_expiration(expires_at=datetime.now(UTC) - timedelta(hours=4))
        assert secure_token.is_expired()

    def test_clear_expiration(self, faker, test_user):
        """Test clear expiration of SecureToken."""
        token_name = faker.slug()
        token_type = TOKEN_TYPE_INSIGHTS
        secure_token = SecureToken.objects.create(
            name=token_name,
            token_type=token_type,
            user=test_user,
            expires_at=datetime.now(UTC) - timedelta(hours=4),
        )
        secure_token.refresh_from_db()
        assert secure_token.is_expired()
        secure_token.clear_expiration()
        assert not secure_token.is_expired()
