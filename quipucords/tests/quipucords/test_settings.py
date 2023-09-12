"""Test settings module."""

from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings as django_settings

from quipucords import settings
from quipucords.settings import app_secret_key_and_path


def read_secret_key(secret_file):
    """Return the secret stored in the secret file specified."""
    return secret_file.read_text(encoding="utf-8").strip()


@pytest.fixture
def secret_key(faker):
    """Return a random secret key for testing."""
    return faker.password(length=64)


class TestSecretKey:
    """Tests to verify SECRET_KEY and DJANGO_SECRET_PATH are properly defined."""

    def test_django_secret_key(self, secret_key, tmp_path, mocker):
        """Test DJANGO_SECRET_KEY is honored."""
        secret_file = tmp_path / "secret"
        mocker.patch.dict(
            settings.os.environ,
            {
                "DJANGO_SECRET_PATH": str(secret_file),
                "DJANGO_SECRET_KEY": secret_key,
            },
            clear=True,
        )

        django_secret, django_secret_path = app_secret_key_and_path()
        assert django_secret == secret_key
        assert django_secret_path == secret_file
        assert read_secret_key(django_secret_path) == secret_key

    def test_django_secret_path(self, tmp_path, secret_key, mocker):
        """Test DJANGO_SECRET_PATH is honored."""
        secret_file = tmp_path / "secret"
        secret_file.write_text(secret_key)
        mocker.patch.dict(
            settings.os.environ,
            {
                "DJANGO_SECRET_PATH": str(secret_file),
                "DJANGO_SECRET_KEY": secret_key,
            },
            clear=True,
        )

        django_secret, django_secret_path = app_secret_key_and_path()
        assert django_secret == secret_key
        assert django_secret_path == secret_file
        assert read_secret_key(django_secret_path) == secret_key

    def test_base_secret_key(self, mocker):
        """Test base secret file is read and honored."""
        base_secret_path = Path(str(django_settings.DEFAULT_DATA_DIR / "secret.txt"))
        mocker.patch.dict(settings.os.environ, {}, clear=True)
        if base_secret_path.exists():
            base_secret_key = read_secret_key(base_secret_path)
            django_secret, django_secret_path = app_secret_key_and_path()
            assert django_secret == base_secret_key
            assert base_secret_path == django_secret_path
            assert read_secret_key(base_secret_path) == base_secret_key

    @patch("quipucords.settings.create_random_key")
    @patch("quipucords.settings.Path.exists")
    def test_default_random_key(  # noqa: PLR0913
        self, mock_path_exists, mock_create_random_key, tmp_path, mocker, secret_key
    ):
        """Test default random key generated if no secrets are specified."""
        mock_path_exists.return_value = False
        mock_create_random_key.return_value = secret_key
        secret_file = tmp_path / "secret"
        mocker.patch.dict(
            settings.os.environ,
            {"DJANGO_SECRET_PATH": str(secret_file)},
            clear=True,
        )
        django_secret, django_secret_path = app_secret_key_and_path()
        assert django_secret == secret_key
        assert django_secret_path == secret_file
        assert read_secret_key(django_secret_path) == secret_key
        mock_create_random_key.assert_called()
