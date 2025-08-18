"""Test settings module."""

import os
import stat
from pathlib import Path
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

from quipucords import settings


def assert_secret_file_content(secret_path, expected_content):
    """Assert that the secret file modes are correct."""
    secret_path = Path(secret_path)
    # We cast to Path because tmpdir produces PosixPath objects,
    # but PosixPath.stat() does not return all mode data.
    assert secret_path.exists()
    secret_path_stats = secret_path.stat()
    assert secret_path_stats.st_mode & stat.S_IRUSR  # owner has access
    assert not secret_path_stats.st_mode & stat.S_IRWXG  # group no access
    assert not secret_path_stats.st_mode & stat.S_IRWXO  # others no access
    assert expected_content == secret_path.read_text(encoding="utf-8")


def test_get_secret_settings_with_all_env_vars(faker, tmpdir, mocker):
    """
    Test get_secret_settings works when all related env vars are set.

    This is an unusual use case but may be present during a transition period
    for some users as we migrate from quipucords-installer to quipucordsctl.
    """
    expected_django_secret = faker.password()
    expected_encryption_secret = faker.password()
    expected_django_secret_path = tmpdir / faker.slug()
    expected_encryption_secret_path = tmpdir / faker.slug()

    new_environ = {
        "DJANGO_SECRET_KEY": expected_django_secret,
        "DJANGO_SECRET_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_SESSION_SECRET_KEY": expected_django_secret,
        "QUIPUCORDS_SESSION_SECRET_KEY_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY": expected_encryption_secret,
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY_PATH": str(expected_encryption_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)
    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_reads_from_files(faker, tmpdir, mocker):
    """Test get_secret_settings reads from files when secrets are not in env vars."""
    expected_django_secret = faker.password()
    expected_encryption_secret = faker.password()
    expected_django_secret_path = tmpdir / faker.slug()
    expected_encryption_secret_path = tmpdir / faker.slug()

    new_environ = {
        "DJANGO_SECRET_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY_PATH": str(expected_encryption_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)

    expected_django_secret_path.write_text(expected_django_secret, encoding="utf-8")
    expected_encryption_secret_path.write_text(
        expected_encryption_secret, encoding="utf-8"
    )

    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_file_not_present_at_path(faker, tmpdir, mocker):
    """
    Test get_secret_settings handles when env var defined path does not actually exist.

    This means that the env vars define paths for the session and encryption secret key
    files, but nothing actually exists at those paths on the filesystem yet. Invoking
    the get_secret_settings() call should create files and write secret keys into them.

    If the `*_SECRET_KEY` is not set and its related `*_PATH` is either empty or does
    not exist, then we fall back again to generating a new random secret key value.
    In this specific test, because no secret value was found in either the paths or the
    related `*_SECRET_KEY` env var, this means we also reuse the Django session secret
    key value as the encryption secret key value, preserving legacy behavior.
    """
    expected_django_secret = faker.password()
    expected_encryption_secret = expected_django_secret  # expect same value
    expected_django_secret_path = tmpdir / faker.slug()
    expected_encryption_secret_path = tmpdir / faker.slug()

    new_environ = {
        "DJANGO_SECRET_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY_PATH": str(expected_encryption_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)
    # Expect random generation of new secrets if no env vars and no files exist.
    mock_create_random_key = mock.Mock()
    mock_create_random_key.side_effect = [
        expected_django_secret,
        expected_encryption_secret,
    ]
    mocker.patch.object(settings, "create_random_key", mock_create_random_key)

    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_only_legacy_env_vars(faker, tmpdir, mocker):
    """Test get_secret_settings when configured by quipucords-installer."""
    expected_django_secret = faker.password()
    # TODO This should have a new value when we stop reusing django_secret_key.
    expected_encryption_secret = expected_django_secret
    expected_django_secret_path = tmpdir / faker.slug()
    expected_encryption_secret_path = tmpdir / "secret-encryption.txt"

    new_environ = {
        "DJANGO_SECRET_KEY": expected_django_secret,
        "DJANGO_SECRET_PATH": str(expected_django_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)
    # Mock DEFAULT_DATA_DIR to force new files with default paths into tmpdir.
    mocker.patch.object(settings, "DEFAULT_DATA_DIR", tmpdir)

    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    # Note that because we did not set ENCRYPTION_* env vars, we assume this represents
    # quipucords being installed via the older quipucords-installer, not quipucordsctl.
    # Therefore, Django's secret and the Ansible encryption key should be the same.
    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert django_secret == encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_only_modern_env_vars(faker, tmpdir, mocker):
    """Test get_secret_settings when configured by quipucordsctl."""
    expected_django_secret = faker.password()
    expected_encryption_secret = faker.password()
    expected_django_secret_path = tmpdir / faker.slug()
    expected_encryption_secret_path = tmpdir / faker.slug()

    new_environ = {
        "QUIPUCORDS_SESSION_SECRET_KEY": expected_django_secret,
        "QUIPUCORDS_SESSION_SECRET_KEY_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY": expected_encryption_secret,
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY_PATH": str(expected_encryption_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)

    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_only_key_env_vars_no_paths(faker, tmpdir, mocker):
    """
    Test get_secret_settings when the key env vars are set but not path env vars.

    We expect the keys defined in the env vars will be written to the default paths.
    """
    expected_django_secret = faker.password()
    expected_encryption_secret = faker.password()
    expected_django_secret_path = tmpdir / "secret.txt"
    expected_encryption_secret_path = tmpdir / "secret-encryption.txt"

    new_environ = {
        "QUIPUCORDS_SESSION_SECRET_KEY": expected_django_secret,
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY": expected_encryption_secret,
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)
    # Mock DEFAULT_DATA_DIR to force new files with default paths into tmpdir.
    mocker.patch.object(settings, "DEFAULT_DATA_DIR", tmpdir)

    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_no_env_vars(faker, tmpdir, mocker):
    """
    Test get_secret_settings generates random values when env vars are absent.

    This should never happen under normal deployed circumstances, but it may
    be common when developing, running from source, or running unit tests.
    """
    expected_django_secret = faker.password()
    # Expect same value due to "Until we move..." comment in settings.py
    # TODO This should have a new value when we stop reusing django_secret_key.
    expected_encryption_secret = expected_django_secret

    # Expect default construction of paths using DEFAULT_DATA_DIR if no env vars.
    expected_django_secret_path = tmpdir / "secret.txt"
    expected_encryption_secret_path = tmpdir / "secret-encryption.txt"
    mocker.patch.dict(os.environ, {}, clear=True)
    # Mock DEFAULT_DATA_DIR to force new files with default paths into tmpdir.
    mocker.patch.object(settings, "DEFAULT_DATA_DIR", tmpdir)
    # Expect random generation of new secrets if no env vars and no files exist.
    mock_create_random_key = mock.Mock()
    mock_create_random_key.return_value = expected_django_secret
    mocker.patch.object(settings, "create_random_key", mock_create_random_key)

    django_secret, encryption_secret, encryption_secret_path = (
        settings.get_secret_settings()
    )

    assert django_secret == expected_django_secret
    assert encryption_secret == expected_encryption_secret
    assert str(encryption_secret_path) == str(expected_encryption_secret_path)
    assert_secret_file_content(expected_django_secret_path, django_secret)
    assert_secret_file_content(expected_encryption_secret_path, encryption_secret)


def test_get_secret_settings_forbids_same_file_for_two_secrets(faker, tmpdir, mocker):
    """Test get_secret_settings forbids secrets sharing the same file path."""
    expected_django_secret_path = tmpdir / faker.slug()
    expected_encryption_secret_path = expected_django_secret_path

    new_environ = {
        "QUIPUCORDS_SESSION_SECRET_KEY_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY_PATH": str(expected_encryption_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)
    with pytest.raises(ImproperlyConfigured):
        settings.get_secret_settings()


def test_get_secret_settings_forbids_same_inode_for_two_secrets(faker, tmpdir, mocker):
    """Test get_secret_settings forbids secrets sharing the same file inode."""
    expected_django_secret_path = Path(tmpdir / faker.slug())
    expected_encryption_secret_path = Path(tmpdir / faker.slug())

    expected_django_secret_path.touch()
    expected_encryption_secret_path.hardlink_to(expected_django_secret_path)

    new_environ = {
        "QUIPUCORDS_SESSION_SECRET_KEY_PATH": str(expected_django_secret_path),
        "QUIPUCORDS_ENCRYPTION_SECRET_KEY_PATH": str(expected_encryption_secret_path),
    }
    mocker.patch.dict(os.environ, new_environ, clear=True)
    with pytest.raises(ImproperlyConfigured):
        settings.get_secret_settings()
