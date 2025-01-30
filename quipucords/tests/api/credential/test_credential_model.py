"""Test credential model methods."""

from pathlib import Path

import pytest

from api.models import Credential
from api.vault import decrypt_data_as_unicode
from tests.factories import CredentialFactory


class TestGenerateSSHKeyfile:
    """Test Credential.generate_ssh_keyfile."""

    def test_with_ssh_key(self):
        """Test the method when credential has a ssh_key."""
        credential: Credential = CredentialFactory.build(with_ssh_key=True)
        with credential.generate_ssh_keyfile() as ssh_keyfile:
            assert Path(ssh_keyfile).exists()
            expected_ssh_key_contents = (
                decrypt_data_as_unicode(credential.ssh_key) + "\n"
            )
            assert Path(ssh_keyfile).read_text() == expected_ssh_key_contents
        # ensure the key is destroyed outside of the with block
        assert not Path(ssh_keyfile).exists()

    def test_without_ssh_key(self):
        """Test the method when credential has no ssh_key."""
        credential: Credential = CredentialFactory.build()

        with credential.generate_ssh_keyfile() as ssh_keyfile:
            assert ssh_keyfile is None

    def test_with_error(self):
        """Ensure the generated file is destroyed even on errors on nested code."""
        credential: Credential = CredentialFactory.build(with_ssh_key=True)

        with pytest.raises(RuntimeError):
            with credential.generate_ssh_keyfile() as ssh_keyfile:
                raise RuntimeError

        # make sure the file is destroyed
        assert not Path(ssh_keyfile).exists()
