"""Define the Fixtures shared with the Auth API Tests."""

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest


# Fixtures for testing the Auth login endpoint.
@pytest.fixture()
def device_code(faker):
    """Fixture to create a device_code."""
    return faker.lexify("?" * 32)


@pytest.fixture()
def user_code(faker):
    """Fixture to create a user_code."""
    return f"{faker.lexify('?' * 4)}-{faker.lexify('?' * 4)}"


@pytest.fixture()
def verification_uri():
    """Fixture to define a verification URI."""
    return "https://sso.example.com/device"


@pytest.fixture()
def verification_uri_complete(verification_uri, user_code):
    """Define a verification complete URI for the generated user_code."""
    return f"{verification_uri}?user_code={user_code}"


@pytest.fixture
def lightspeed_auth_response(
    device_code, user_code, verification_uri, verification_uri_complete
):
    """Return a Lightspeed device authorization workflow response."""
    auth_response = {
        "device_code": device_code,
        "user_code": user_code,
        "verification_uri": verification_uri,
        "verification_uri_complete": verification_uri_complete,
        "expires_in": 600,
        "interval": 5,
    }
    return auth_response


# Fixtures for testing the Auth status endpoint.
@pytest.fixture
def lightspeed_user_metadata(faker):
    """Fixture to create metadata for a lightspeed user."""
    return {
        "org_id": faker.numerify(text="#######"),
        "account_number": faker.numerify(text="#######"),
        "username": faker.user_name(),
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "email": faker.email(),
    }


# Fixtures for testing and decoding JWTs
@pytest.fixture()
def jwt_header_dict(faker):
    """Represent a JWT header."""
    return {"alg": "RS256", "typ": "JWT", "kid": faker.lexify("?" * 32)}


@pytest.fixture()
def jwt_header(jwt_header_dict):
    """Build a header portion of a JWT token."""
    json_str = json.dumps(jwt_header_dict)
    encoded_str = json_str.encode("utf-8")
    base64encoded_str = base64.urlsafe_b64encode(encoded_str)
    return base64encoded_str.decode("utf-8")


@pytest.fixture()
def jwt_payload_dict(faker):
    """Build a payload portion of a JWT token."""
    auth_time = datetime.now(UTC)
    expiration_time = auth_time + timedelta(hours=4)
    return {
        "exp": int(expiration_time.timestamp()),
        "auth_time": int(auth_time.timestamp()),
        "jti": faker.uuid4(),
        "iss": "https://sso.example.com/auth/realms/example-company-external",
        "aud": "example.api",
        "azp": "sample-application-client-id",
        "sid": "8041485b-84a9-4102-a179-cdac8cc754fa",
        "realm_access": {"roles": ["authenticated", "example:employees"]},
        "scope": "example.api",
        "idp": "auth.example.com",
        "organization": {
            "account_number": faker.pyint(min_value=1000001, max_value=2999999),
            "name": "Example Company, Inc.",
            "id": faker.pyint(min_value=3000001, max_value=9999999),
        },
        "preferred_username": faker.slug(),
        "session_state": faker.uuid4(),
        "given_name": faker.first_name(),
        "locale": "en_US",
        "family_name": faker.last_name(),
        "email": faker.email(),
    }


@pytest.fixture()
def jwt_payload(jwt_payload_dict):
    """Build a payload portion of a JWT token."""
    json_str = json.dumps(jwt_payload_dict)
    encoded_str = json_str.encode("utf-8")
    base64encoded_str = base64.urlsafe_b64encode(encoded_str)
    return base64encoded_str.decode("utf-8")


@pytest.fixture()
def test_jwt(jwt_header, jwt_payload, faker):
    """Build a test JWT token."""
    jwt_signature = faker.lexify("?" * 32)
    return ".".join([jwt_header, jwt_payload, jwt_signature])


@pytest.fixture()
def token_endpoint_response(test_jwt):
    """Return a successful token endpoint response."""
    return {
        "access_token": test_jwt,
    }
