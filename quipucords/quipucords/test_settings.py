"""Test settings module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import faker
from django.conf import settings as django_settings
from django.test import TestCase

from quipucords.settings import app_secret_key_and_path

_faker = faker.Faker()


def read_secret_key(secret_file):
    """Return the secret stored in the secret file specified."""
    return secret_file.read_text(encoding="utf-8").strip()


class SecretKeyTests(TestCase):
    """Tests to verify SECRET_KEY and DJANGO_SECRET_PATH are properly defined."""

    def setUp(self):
        """Initialize common variables for the tests."""
        self.test_key = _faker.password(length=64)

    def test_django_secret_key(self):
        """Test DJANGO_SECRET_KEY is honored."""
        with patch.dict(os.environ, {"DJANGO_SECRET_KEY": self.test_key}):
            secret_key, django_secret_path = app_secret_key_and_path()
            self.assertEqual(secret_key, self.test_key)
            self.assertEqual(read_secret_key(django_secret_path), self.test_key)

    def test_django_secret_path(self):
        """Test DJANGO_SECRET_PATH is honored."""
        with tempfile.NamedTemporaryFile("w+") as secret_file:
            secret_file.write(self.test_key)
            secret_file.flush()
            with patch.dict(os.environ, {"DJANGO_SECRET_PATH": secret_file.name}):
                secret_key, django_secret_path = app_secret_key_and_path()
                self.assertEqual(secret_key, self.test_key)
                self.assertEqual(str(django_secret_path), secret_file.name)
                self.assertEqual(read_secret_key(django_secret_path), self.test_key)

    def test_base_secret_key(self):
        """Test base secret file is read and honored."""
        base_secret_path = Path(str(django_settings.BASE_DIR / "secret.txt"))
        if base_secret_path.exists():
            base_secret_key = base_secret_path.read_text(encoding="utf-8").strip()
            secret_key, django_secret_path = app_secret_key_and_path()
            self.assertEqual(secret_key, base_secret_key)
            self.assertEqual(base_secret_path, django_secret_path)
            self.assertEqual(read_secret_key(base_secret_path), base_secret_key)

    @patch("quipucords.settings.create_random_key")
    @patch("quipucords.settings.Path.exists")
    def test_default_random_key(self, mock_path_exists, mock_create_random_key):
        """Test default random key generated if no secrets are specified."""
        mock_path_exists.return_value = False
        mock_create_random_key.return_value = self.test_key
        secret_key, django_secret_path = app_secret_key_and_path()
        self.assertEqual(secret_key, self.test_key)
        self.assertEqual(read_secret_key(django_secret_path), self.test_key)
        mock_create_random_key.assert_called()
