"""Test the Auth HashiCorp Vault methods."""

import base64
import http

import hvac
import pytest
from django.conf import settings
from django.urls import reverse
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

from api import messages
from api.auth.auth_hashicorp_vault import (
    HASHICORP_VAULT_CA_CERT,
    HASHICORP_VAULT_CLIENT_CERT,
    HASHICORP_VAULT_CLIENT_KEY,
    HashiCorpVaultAuthError,
    decode_cert_from_content,
    delete_hashicorp_vault_token,
    get_hashicorp_vault_token,
    get_or_create_hashicorp_vault_token,
    hashicorp_vault_address,
    hashicorp_vault_authenticate,
    hashicorp_vault_client,
    hashicorp_vault_url,
)


@pytest.mark.django_db
class TestHashiCorpVaultHelpers:
    """Test the HashiCorp Vault helper functions."""

    def test_get_hashicorp_vault_token_not_exists(self):
        """Test getting a HashiCorp Vault token when it doesn't exist."""
        vault_token = get_hashicorp_vault_token()
        assert vault_token is None

    def test_get_or_create_hashicorp_vault_token(self):
        """Test creating a HashiCorp Vault token."""
        vault_token = get_or_create_hashicorp_vault_token()
        assert vault_token is not None
        assert vault_token.name == "hashicorp-vault-server"
        assert vault_token.token_type == "hashicorp-vault"

    def test_get_or_create_hashicorp_vault_token_already_exists(self):
        """Test we're working with a Singleton HashiCorp Vault token."""
        vault_token1 = get_or_create_hashicorp_vault_token()
        vault_token2 = get_or_create_hashicorp_vault_token()
        assert vault_token1.id == vault_token2.id

    def test_delete_hashicorp_vault_token(self):
        """Test deleting a HashiCorp Vault token."""
        get_or_create_hashicorp_vault_token()
        delete_hashicorp_vault_token()
        vault_token = get_hashicorp_vault_token()
        assert vault_token is None

    def test_delete_hashicorp_vault_token_not_exists(self):
        """Test deleting a HashiCorp Vault token when it doesn't exist."""
        delete_hashicorp_vault_token()
        vault_token = get_hashicorp_vault_token()
        assert vault_token is None

    def test_hashicorp_vault_address(self):
        """Test generating the HashiCorp Vault address."""
        metadata = {"address": "vault.example.com", "port": 8210}
        address = hashicorp_vault_address(metadata)
        assert address == "vault.example.com:8210"

    def test_hashicorp_vault_address_default_port(self):
        """Test generating the HashiCorp Vault address with default port."""
        metadata = {"address": "vault.example.com"}
        address = hashicorp_vault_address(metadata)
        assert (
            address
            == f"vault.example.com:{settings.QUIPUCORDS_HASHICORP_VAULT_DEFAULT_PORT}"
        )

    def test_hashicorp_vault_url(self):
        """Test generating the HashiCorp Vault URL."""
        metadata = {"address": "vault.example.com", "port": 8300}
        vault_url = hashicorp_vault_url(metadata)
        assert vault_url == "https://vault.example.com:8300"

    def test_decode_cert_from_content_valid(self, hashicorp_vault_cert_content):
        """Test decoding valid base64 encoded certificate content."""
        cert_b64 = base64.b64encode(
            hashicorp_vault_cert_content.encode("utf-8")
        ).decode("utf-8")
        decoded = decode_cert_from_content("test_cert", cert_b64)
        assert decoded == hashicorp_vault_cert_content

    def test_decode_cert_from_content_invalid_base64(self):
        """Test decoding invalid base64 content raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            decode_cert_from_content("test_cert", "not-valid-base64!@#$")
        assert "Failed to base64 decode" in str(exc_info.value)

    def test_decode_cert_from_content_invalid_utf8(self):
        """Test decoding non-UTF8 content raises ValueError."""
        invalid_utf8 = base64.b64encode(b"\x80\x81\x82\x83").decode("utf-8")
        with pytest.raises(ValueError) as exc_info:
            decode_cert_from_content("test_cert", invalid_utf8)
        assert "Failed to decode" in str(exc_info.value)

    def test_decode_cert_from_content_empty(self):
        """Test decoding empty content returns None."""
        result = decode_cert_from_content("test_cert", None)
        assert result is None

    def test_hashicorp_vault_client_raises_auth_error_invalid_client_cert(
        self, hashicorp_vault_data
    ):
        """Test hashicorp_vault_client raises exception with bad client cert."""
        invalid_cert = "not-valid-base64!@#$"
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data | {
            HASHICORP_VAULT_CLIENT_CERT: invalid_cert
        }
        vault_token.save()

        with pytest.raises(HashiCorpVaultAuthError) as exc_info:
            with hashicorp_vault_client(vault_token) as _:
                pass

        assert messages.HASHICORP_VAULT_VALID_CLIENT_CERT_REQUIRED in str(
            exc_info.value
        )

    def test_hashicorp_vault_client_raises_auth_error_invalid_client_key(
        self, hashicorp_vault_data
    ):
        """Test hashicorp_vault_client raises exception with bad client key."""
        invalid_cert = "not-valid-base64!@#$"
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data | {
            HASHICORP_VAULT_CLIENT_KEY: invalid_cert
        }
        vault_token.save()

        with pytest.raises(HashiCorpVaultAuthError) as exc_info:
            with hashicorp_vault_client(vault_token) as _:
                pass

        assert messages.HASHICORP_VAULT_VALID_CLIENT_KEY_REQUIRED in str(exc_info.value)

    def test_hashicorp_vault_client_raises_auth_error_invalid_ca_cert(
        self, hashicorp_vault_data
    ):
        """Test hashicorp_vault_client raises exception with bad ca_cert."""
        invalid_cert = "not-valid-base64!@#$"
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data | {
            "ssl_verify": True,
            HASHICORP_VAULT_CA_CERT: invalid_cert,
        }
        vault_token.save()

        with pytest.raises(HashiCorpVaultAuthError) as exc_info:
            with hashicorp_vault_client(vault_token) as _:
                pass

        assert messages.HASHICORP_VAULT_VALID_CA_CERT_REQUIRED in str(exc_info.value)

    def test_hashicorp_vault_client_returns_an_hvac_client(self, hashicorp_vault_data):
        """Test hashicorp_vault_client returns a hvac Client."""
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data
        vault_token.save()

        with hashicorp_vault_client(vault_token) as vault_client:
            pass

        assert isinstance(vault_client, hvac.Client)


@pytest.mark.django_db
class TestHashiCorpVaultAuthenticate:
    """Test the HashiCorp Vault authentication function."""

    def test_hashicorp_vault_authenticate_success(
        self, mocker, hashicorp_vault_data, hashicorp_vault_cert_content
    ):
        """Test successful authentication to HashiCorp Vault."""
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data
        vault_token.save()

        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        result = hashicorp_vault_authenticate(vault_token=vault_token)
        assert result is True
        mock_client.is_authenticated.assert_called_once()

    def test_hashicorp_vault_authenticate_failure(
        self, mocker, hashicorp_vault_data, hashicorp_vault_cert_content
    ):
        """Test failed authentication to HashiCorp Vault."""
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data
        vault_token.save()

        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = False
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        result = hashicorp_vault_authenticate(vault_token=vault_token)
        assert result is False

    def test_hashicorp_vault_authenticate_connection_error(
        self, mocker, hashicorp_vault_data
    ):
        """Test authentication with connection error."""
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data
        vault_token.save()

        mock_client = mocker.MagicMock()
        error_message = "Connection refused"
        mock_client.is_authenticated.side_effect = ConnectionError(error_message)
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        with pytest.raises(HashiCorpVaultAuthError) as exc_info:
            hashicorp_vault_authenticate(vault_token=vault_token)
        vault_address = hashicorp_vault_address(hashicorp_vault_data)
        vault_err_message = (
            messages.HASHICORP_VAULT_FAILED_AUTHENTICATION % vault_address
        )
        assert vault_err_message in str(exc_info.value)
        assert f"ConnectionError: {error_message}" in str(exc_info.value)

    def test_hashicorp_vault_authenticate_http_error(
        self, mocker, hashicorp_vault_data
    ):
        """Test authentication with HTTP error."""
        vault_token = get_or_create_hashicorp_vault_token()
        vault_token.metadata = hashicorp_vault_data
        vault_token.save()

        mock_client = mocker.MagicMock()
        error_message = "HTTP Error"
        mock_client.is_authenticated.side_effect = BaseHTTPError(error_message)
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        with pytest.raises(HashiCorpVaultAuthError) as exc_info:
            hashicorp_vault_authenticate(vault_token=vault_token)
        vault_address = hashicorp_vault_address(hashicorp_vault_data)
        vault_err_message = (
            messages.HASHICORP_VAULT_FAILED_AUTHENTICATION % vault_address
        )
        assert vault_err_message in str(exc_info.value)
        assert f"BaseHTTPError: {error_message}" in str(exc_info.value)


@pytest.mark.django_db
class TestHashiCorpVaultCreate:
    """Test the CREATE operation for HashiCorp Vault endpoint."""

    def test_create_hashicorp_vault_unauthenticated(
        self, client_logged_out, hashicorp_vault_data
    ):
        """Test failing to create a HashiCorp Vault definition if unauthenticated."""
        response = client_logged_out.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_create_hashicorp_vault_success(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test successfully creating a HashiCorp Vault server definition."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.CREATED
        assert response.data == {
            "address": "vault.example.com",
            "port": 8200,
            "ssl_verify": False,
        }

    def test_create_hashicorp_vault_already_exists(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test creating a HashiCorp Vault when one already exists."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.CONFLICT
        assert messages.HASHICORP_VAULT_ALREADY_EXISTS in response.data["detail"]

    def test_create_hashicorp_vault_missing_address(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test creating a HashiCorp Vault without address field."""
        invalid_data = {**hashicorp_vault_data}
        del invalid_data["address"]

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data["address"][0]
        assert "This field is required" in str(err_message)

    def test_create_hashicorp_vault_missing_client_cert(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test creating a HashiCorp Vault without client_cert field."""
        invalid_data = {**hashicorp_vault_data}
        del invalid_data[HASHICORP_VAULT_CLIENT_CERT]

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data[HASHICORP_VAULT_CLIENT_CERT][0]
        assert "This field is required" in str(err_message)

    def test_create_hashicorp_vault_missing_client_key(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test creating a HashiCorp Vault without client_key field."""
        invalid_data = {**hashicorp_vault_data}
        del invalid_data[HASHICORP_VAULT_CLIENT_KEY]

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data[HASHICORP_VAULT_CLIENT_KEY][0]
        assert "This field is required" in str(err_message)

    def test_create_hashicorp_vault_invalid_base64_cert(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test creating a HashiCorp Vault with invalid base64 client_cert."""
        invalid_data = {
            **hashicorp_vault_data,
            HASHICORP_VAULT_CLIENT_CERT: "not-valid-base64!@#",
        }

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data[HASHICORP_VAULT_CLIENT_CERT][0]
        assert (
            f"Failed to base64 decode the HashiCorp Vault {HASHICORP_VAULT_CLIENT_CERT}"
        ) in str(err_message)

    def test_create_hashicorp_vault_ssl_verify_without_ca_cert(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test creating a HashiCorp Vault with ssl_verify=True but no ca_cert."""
        invalid_data = {**hashicorp_vault_data, "ssl_verify": True}
        del invalid_data[HASHICORP_VAULT_CA_CERT]

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data[HASHICORP_VAULT_CA_CERT][0]
        assert messages.HASHICORP_VAULT_MUST_SPECIFY_CA_CERT in str(err_message)

    def test_create_hashicorp_vault_authentication_failure(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test creating a HashiCorp Vault with authentication failure."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = False
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data["non_field_errors"][0]
        vault_address = hashicorp_vault_address(hashicorp_vault_data)
        assert (messages.HASHICORP_VAULT_FAILED_AUTHENTICATION % vault_address) in str(
            err_message
        )

    def test_create_hashicorp_vault_connection_error(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test creating a HashiCorp Vault with connection error."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.side_effect = ConnectionError("Connection refused")
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data["non_field_errors"][0]
        vault_address = hashicorp_vault_address(hashicorp_vault_data)
        vault_err_message = (
            messages.HASHICORP_VAULT_FAILED_AUTHENTICATION % vault_address
        )
        assert vault_err_message in str(err_message)
        assert "ConnectionError: Connection refused" in str(err_message)

    def test_create_hashicorp_vault_invalid_port(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test creating a HashiCorp Vault with invalid port."""
        invalid_data = {**hashicorp_vault_data, "port": "not-an-integer"}

        response = client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data["port"][0]
        assert "A valid integer is required" in str(err_message)


@pytest.mark.django_db
class TestHashiCorpVaultRetrieve:
    """Test the Retrieve operation for HashiCorp Vault endpoint."""

    def test_retrieve_hashicorp_vault_unauthenticated(
        self, client_logged_out, hashicorp_vault_data
    ):
        """Test failing to retrieve a HashiCorp Vault definition if unauthenticated."""
        response = client_logged_out.get(reverse("v2:hashicorp-vault"))
        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_retrieve_hashicorp_vault_success(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test successfully retrieving a HashiCorp Vault server definition."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        response = client_logged_in.get(reverse("v2:hashicorp-vault"))

        assert response.status_code == http.HTTPStatus.OK
        assert response.data == {
            "address": "vault.example.com",
            "port": 8200,
            "ssl_verify": False,
        }

    def test_retrieve_hashicorp_vault_not_found(self, client_logged_in):
        """Test retrieving a HashiCorp Vault when it doesn't exist."""
        response = client_logged_in.get(reverse("v2:hashicorp-vault"))

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        assert messages.HASHICORP_VAULT_NOT_DEFINED in response.data["detail"]


@pytest.mark.django_db
class TestHashiCorpVaultUpdate:
    """Test the UPDATE operation for HashiCorp Vault endpoint."""

    def test_update_hashicorp_vault_unauthenticated(
        self, client_logged_out, hashicorp_vault_data
    ):
        """Test failing to update a HashiCorp Vault definition if unauthenticated."""
        response = client_logged_out.put(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_update_hashicorp_vault_success(
        self,
        client_logged_in,
        hashicorp_vault_data,
        hashicorp_vault_cert_content,
        mocker,
    ):
        """Test successfully updating a HashiCorp Vault server definition."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )
        ssl_verify = hashicorp_vault_data["ssl_verify"]

        updated_data = {
            **hashicorp_vault_data,
            "address": "newvault.example.com",
            "port": 8210,
        }
        response = client_logged_in.put(
            reverse("v2:hashicorp-vault"),
            data=updated_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.data == {
            "address": "newvault.example.com",
            "port": 8210,
            "ssl_verify": ssl_verify,
        }

    def test_update_hashicorp_vault_not_found(
        self, client_logged_in, hashicorp_vault_data
    ):
        """Test updating a HashiCorp Vault when it doesn't exist."""
        response = client_logged_in.put(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        assert messages.HASHICORP_VAULT_NOT_DEFINED in response.data["detail"]

    def test_update_hashicorp_vault_missing_required_field(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test updating a HashiCorp Vault with missing required field."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        invalid_data = {**hashicorp_vault_data}
        del invalid_data[HASHICORP_VAULT_CLIENT_KEY]

        response = client_logged_in.put(
            reverse("v2:hashicorp-vault"),
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data[HASHICORP_VAULT_CLIENT_KEY][0]
        assert "This field is required" in str(err_message)

    def test_update_hashicorp_vault_authentication_failure(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test updating a HashiCorp Vault with authentication failure."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        mock_client.is_authenticated.return_value = False
        updated_data = {
            **hashicorp_vault_data,
            "address": "newvault.example.com",
        }
        response = client_logged_in.put(
            reverse("v2:hashicorp-vault"),
            data=updated_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        vault_address = hashicorp_vault_address(updated_data)
        err_message = response.data["non_field_errors"][0]
        assert (messages.HASHICORP_VAULT_FAILED_AUTHENTICATION % vault_address) in str(
            err_message
        )


@pytest.mark.django_db
class TestHashiCorpVaultPartialUpdate:
    """Test the PARTIAL_UPDATE operation for HashiCorp Vault endpoint."""

    def test_partial_update_hashicorp_vault_unauthenticated(self, client_logged_out):
        """Test failing to patch a HashiCorp Vault definition if unauthenticated."""
        partial_data = {"port": 8210}
        response = client_logged_out.patch(
            reverse("v2:hashicorp-vault"),
            data=partial_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_partial_update_hashicorp_vault_success(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test successfully partially updating a HashiCorp Vault server definition."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        partial_data = {"port": 8230}
        response = client_logged_in.patch(
            reverse("v2:hashicorp-vault"),
            data=partial_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.data == {
            "address": "vault.example.com",
            "port": 8230,
            "ssl_verify": False,
        }

    def test_partial_update_hashicorp_vault_address(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test partially updating just the address field."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )
        port = hashicorp_vault_data["port"]
        ssl_verify = hashicorp_vault_data["ssl_verify"]

        partial_data = {"address": "updated-vault.example.com"}
        response = client_logged_in.patch(
            reverse("v2:hashicorp-vault"),
            data=partial_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.data == {
            "address": "updated-vault.example.com",
            "port": port,
            "ssl_verify": ssl_verify,
        }

    def test_partial_update_hashicorp_vault_not_found(self, client_logged_in):
        """Test partially updating a HashiCorp Vault when it doesn't exist."""
        partial_data = {"port": 8230}
        response = client_logged_in.patch(
            reverse("v2:hashicorp-vault"),
            data=partial_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        assert messages.HASHICORP_VAULT_NOT_DEFINED in response.data["detail"]

    def test_partial_update_hashicorp_vault_invalid_port(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test partially updating with an invalid port value."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        partial_data = {"port": "not-an-integer"}
        response = client_logged_in.patch(
            reverse("v2:hashicorp-vault"),
            data=partial_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data["port"][0]
        assert "A valid integer is required" in str(err_message)

    def test_partial_update_hashicorp_vault_ssl_verify_requires_ca_cert(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test partially updating ssl_verify to True requires ca_cert."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        hashicorp_vault_data_no_ca = {**hashicorp_vault_data}
        del hashicorp_vault_data_no_ca[HASHICORP_VAULT_CA_CERT]

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data_no_ca,
            content_type="application/json",
        )

        partial_data = {"ssl_verify": True}
        response = client_logged_in.patch(
            reverse("v2:hashicorp-vault"),
            data=partial_data,
            content_type="application/json",
        )

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        err_message = response.data[HASHICORP_VAULT_CA_CERT][0]
        assert messages.HASHICORP_VAULT_MUST_SPECIFY_CA_CERT in str(err_message)


@pytest.mark.django_db
class TestHashiCorpVaultDelete:
    """Test the DELETE operation for HashiCorp Vault endpoint."""

    def test_delete_hashicorp_vault_unauthenticated(self, client_logged_out):
        """Test failing to delete a HashiCorp Vault definition if unauthenticated."""
        response = client_logged_out.delete(reverse("v2:hashicorp-vault"))

        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_delete_hashicorp_vault_success(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test successfully deleting a HashiCorp Vault server definition."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        response = client_logged_in.delete(reverse("v2:hashicorp-vault"))

        assert response.status_code == http.HTTPStatus.NO_CONTENT
        assert get_hashicorp_vault_token() is None

    def test_delete_hashicorp_vault_already_deleted(self, client_logged_in):
        """Test deleting a HashiCorp Vault when it's already deleted."""
        response = client_logged_in.delete(reverse("v2:hashicorp-vault"))

        assert response.status_code == http.HTTPStatus.NO_CONTENT

    def test_delete_hashicorp_vault_idempotent(
        self, client_logged_in, hashicorp_vault_data, mocker
    ):
        """Test that deleting twice is idempotent."""
        mock_client = mocker.MagicMock()
        mock_client.is_authenticated.return_value = True
        mocker.patch(
            "api.auth.auth_hashicorp_vault.hvac.Client", return_value=mock_client
        )

        client_logged_in.post(
            reverse("v2:hashicorp-vault"),
            data=hashicorp_vault_data,
            content_type="application/json",
        )

        response1 = client_logged_in.delete(reverse("v2:hashicorp-vault"))
        response2 = client_logged_in.delete(reverse("v2:hashicorp-vault"))

        assert response1.status_code == http.HTTPStatus.NO_CONTENT
        assert response2.status_code == http.HTTPStatus.NO_CONTENT
