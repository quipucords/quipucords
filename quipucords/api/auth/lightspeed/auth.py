"""Authentication support for Lightspeed."""

import http
import time
from logging import getLogger

import celery
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.translation import gettext as _
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

from api import messages
from api.auth.lightspeed.serializer import (
    LightspeedAuthLoginResponseSerializer,
    LightspeedAuthLogoutResponseSerializer,
    LightspeedAuthStatusResponseSerializer,
)
from api.auth.utils import decode_jwt
from api.common.enumerators import AuthStatus
from api.secure_token.model import SecureToken
from quipucords.settings import QUIPUCORDS_AUTH_LIGHTSPEED_TIMEOUT

logger = getLogger(__name__)

# At this time, we support a single Lightspeed JWT token for the logged in
# Discovery user. So we use the single "lightspeed-jwt-token" SecureToken
# token for the user.

DISCOVERY_CLIENT_ID = "discovery-client-id"
LIGHTSPEED_REALM = "redhat-external"
LIGHTSPEED_SCOPE = "api.console"
GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
OPENID_CONFIG_ENDPOINT = (
    f"/auth/realms/{LIGHTSPEED_REALM}/.well-known/openid-configuration"
)
DEVICE_AUTH_ENDPOINT_KEY = "device_authorization_endpoint"
ENDPOINT_KEY = "token_endpoint"

LIGHTSPEED_NAME = "lightspeed-jwt-token"
LIGHTSPEED_TYPE = "lightspeed-jwt"


class LightspeedAuthError(Exception):
    """Class for Lightspeed device authorization errors."""

    def __init__(self, message, *args):
        """Take message as mandatory attribute."""
        super().__init__(message, *args)
        self.message = message


def update_secure_token_status(secure_token, status, status_reason=""):
    """Update the SecureToken status and status_reason."""
    metadata = secure_token.metadata or {}
    metadata["status"] = status.value
    metadata["status_reason"] = status_reason
    secure_token.metadata = metadata
    secure_token.save()


def update_secure_token_metadata(secure_token, decoded_lightspeed_jwt):
    """Update the SecureToken metadata based on the Lightspeed Auth Token."""
    payload = decoded_lightspeed_jwt["payload"]
    metadata = secure_token.metadata or {}
    metadata.update(
        {
            "org_id": payload["organization"]["id"],
            "account_number": payload["organization"]["account_number"],
            "username": payload["preferred_username"],
            "first_name": payload["given_name"],
            "last_name": payload["family_name"],
            "email": payload["email"],
        }
    )
    secure_token.metadata = metadata
    secure_token.expires_at = decoded_lightspeed_jwt["expires_at"]
    secure_token.save()


def lightspeed_login_request(user) -> LightspeedAuthLoginResponseSerializer:
    """Request a Lightspeed login authorization for the user."""
    # we send the request for device authorization here, however, we can't block
    # the API on waiting for the user to authorize it, so we kick off the
    # lightspeed_wait_for_authorization task asynchronously via celery.
    try:
        auth_request = lightspeed_request_auth()
        logger.info(f"Lightspeed login authorization requested for {user.username}")
        logger.debug(
            f"Lightspeed authorization URL for user {user.username}:"
            f" {auth_request['verification_uri_complete']}"
        )
        lightspeed_secure_token = get_or_create_lightspeed_secure_token(user)
        clear_lightspeed_auth_token(lightspeed_secure_token)
        update_secure_token_status(lightspeed_secure_token, AuthStatus.PENDING)

        serializer = LightspeedAuthLoginResponseSerializer(
            {
                "status": lightspeed_secure_token.metadata["status"],
                "user_code": auth_request["user_code"],
                "verification_uri": auth_request["verification_uri"],
                "verification_uri_complete": auth_request["verification_uri_complete"],
            }
        )

        lightspeed_wait_for_authorization.delay(
            lightspeed_secure_token.id,
            auth_request["device_code"],
            auth_request["interval"],
            auth_request["expires_in"],
        )

        return serializer
    except LightspeedAuthError as err:
        logger.error(err.message)
        raise err


def lightspeed_logout_request(user) -> LightspeedAuthLogoutResponseSerializer:
    """Request a Lightspeed logout for the user."""
    lightspeed_secure_token = get_lightspeed_secure_token(user)
    data = dict(status="successful")
    if lightspeed_secure_token:
        lightspeed_secure_token.delete()
        data["status_reason"] = _(messages.LIGHTSPEED_LOGOUT_SUCCESSFUL)
    else:
        data["status_reason"] = _(messages.LIGHTSPEED_ALREADY_LOGGED_OUT)
    return LightspeedAuthLogoutResponseSerializer(data)


def lightspeed_token_check_expiration(lightspeed_secure_token):
    """Check and Update the Lightspeed SecureToken status if expired."""
    if lightspeed_secure_token.metadata:
        metadata = lightspeed_secure_token.metadata
        status = metadata["status"]
        if status == AuthStatus.VALID.value:
            if lightspeed_secure_token.is_expired():
                if lightspeed_secure_token.user:
                    logger.info(
                        messages.LIGHTSPEED_TOKEN_EXPIRED_FOR_USER,
                        lightspeed_secure_token.user.username,
                    )
                update_secure_token_status(
                    lightspeed_secure_token,
                    AuthStatus.EXPIRED,
                    _(messages.LIGHTSPEED_TOKEN_EXPIRED),
                )


def user_lightspeed_auth_status(user) -> LightspeedAuthStatusResponseSerializer:
    """Return the Lightspeed Authentication status for the user."""
    lightspeed_secure_token = get_lightspeed_secure_token(user)
    if lightspeed_secure_token:
        lightspeed_token_check_expiration(lightspeed_secure_token)
        metadata = lightspeed_secure_token.metadata
        if metadata:
            return LightspeedAuthStatusResponseSerializer(
                {
                    "status": metadata["status"],
                    "metadata": metadata,
                }
            )
    return LightspeedAuthStatusResponseSerializer({"status": AuthStatus.MISSING.value})


def get_lightspeed_secure_token(user) -> SecureToken | None:
    """Get the Lightspeed SecureToken for the user, None if it does not exist."""
    return SecureToken.objects.filter(
        name=LIGHTSPEED_NAME, token_type=LIGHTSPEED_TYPE, user=user
    ).first()


def get_or_create_lightspeed_secure_token(user) -> SecureToken:
    """Get a SecureToken for the user."""
    secure_token, created = SecureToken.objects.get_or_create(
        name=LIGHTSPEED_NAME, token_type=LIGHTSPEED_TYPE, user=user
    )
    if created:
        logger.debug(
            f"New {secure_token.token_type} Token {secure_token.name}"
            f" created for user {user.username}, Token id: {secure_token.id}"
        )
    return secure_token


def clear_lightspeed_auth_token(lightspeed_auth_token: SecureToken):
    """Clear the Lightspeed authentication token."""
    if lightspeed_auth_token:
        lightspeed_auth_token.token = None
        lightspeed_auth_token.metadata = None
        lightspeed_auth_token.expires_at = None
        lightspeed_auth_token.save()


def get_sso_endpoint(endpoint):
    """Get the SSO OpenID Configuration endpoint."""
    lightspeed_sso_server = settings.QUIPUCORDS_LIGHTSPEED_SSO_HOST
    url = f"https://{lightspeed_sso_server}{OPENID_CONFIG_ENDPOINT}"  # Always SSL
    try:
        logger.info(messages.LIGHTSPEED_SSO_CONFIG_QUERY, url, endpoint)
        response = requests.get(url, timeout=QUIPUCORDS_AUTH_LIGHTSPEED_TIMEOUT)
    except ConnectionError as err:
        raise err
    except BaseHTTPError as err:
        raise err

    config = response.json()
    if endpoint not in config:
        raise LightspeedAuthError(_(messages.LIGHTSPEED_SSO_QUERY_FAILED % endpoint))
    return config[endpoint]


def lightspeed_request_auth():
    """Initialize a Lightspeed device authorization workflow request.

    :returns: authorization request object
    """
    auth_request = None

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "grant_type": GRANT_TYPE,
        "scope": LIGHTSPEED_SCOPE,
        "client_id": DISCOVERY_CLIENT_ID,
    }
    try:
        device_auth_endpoint = get_sso_endpoint(DEVICE_AUTH_ENDPOINT_KEY)
        logger.info(messages.LIGHTSPEED_LOGIN_REQUEST, device_auth_endpoint)
        response = requests.post(
            device_auth_endpoint,
            headers=headers,
            data=params,
            timeout=settings.QUIPUCORDS_AUTH_LIGHTSPEED_TIMEOUT,
        )
    except ConnectionError as err:
        raise LightspeedAuthError(_(messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % err))
    except BaseHTTPError as err:
        raise LightspeedAuthError(_(messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % err))

    if response.status_code == http.HTTPStatus.OK:
        auth_request = response.json()
        logger.debug(messages.LIGHTSPEED_RESPONSE, device_auth_endpoint, auth_request)
    else:
        logger.debug(messages.LIGHTSPEED_RESPONSE, device_auth_endpoint, response.text)
        raise LightspeedAuthError(
            _(messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % response.reason)
        )

    return auth_request


@celery.shared_task()
def lightspeed_wait_for_authorization(  # noqa: C901 PLR0911 PLR0912
    secure_token_id, device_code, interval, expires_in
):
    """Wait for the user to log in and authorize the Lightspeed authorization request.

    Updates the Lightspeed Authentication SecureToken.
    """
    try:
        lightspeed_auth_token = SecureToken.objects.get(id=secure_token_id)
    except ObjectDoesNotExist:
        logger.error(
            "Invalid Lightspeed SecureToken id %s specified,"
            " cannot wait for authorization.",
            secure_token_id,
        )
        return

    elapsed_time = 0
    lightspeed_jwt = None

    update_secure_token_status(lightspeed_auth_token, AuthStatus.PENDING)

    token_endpoint = None
    while not lightspeed_jwt:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": GRANT_TYPE,
            "client_id": DISCOVERY_CLIENT_ID,
            "device_code": device_code,
        }
        try:
            if not token_endpoint:
                token_endpoint = get_sso_endpoint(ENDPOINT_KEY)
            logger.debug(messages.LIGHTSPEED_LOGIN_VERIFYING, token_endpoint)
            response = requests.post(
                token_endpoint,
                headers=headers,
                data=params,
                timeout=settings.QUIPUCORDS_AUTH_LIGHTSPEED_TIMEOUT,
            )
        except ConnectionError as err:
            update_secure_token_status(
                lightspeed_auth_token,
                AuthStatus.FAILED,
                _(messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % err),
            )
            return
        except BaseHTTPError as err:
            update_secure_token_status(
                lightspeed_auth_token,
                AuthStatus.FAILED,
                _(messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % err),
            )
            return

        if response.status_code == http.HTTPStatus.OK:
            token_response = response.json()
            lightspeed_jwt = token_response["access_token"]
            decoded_lightspeed_jwt = decode_jwt(lightspeed_jwt)
            if not decoded_lightspeed_jwt:
                update_secure_token_status(
                    lightspeed_auth_token,
                    AuthStatus.FAILED,
                    _(messages.LIGHTSPEED_INVALID_TOKEN),
                )
                return
            with transaction.atomic():
                lightspeed_auth_token.token = lightspeed_jwt
                lightspeed_auth_token.save()
                update_secure_token_metadata(
                    lightspeed_auth_token, decoded_lightspeed_jwt
                )
                update_secure_token_status(lightspeed_auth_token, AuthStatus.VALID)
            return
        if response.status_code == http.HTTPStatus.BAD_REQUEST:
            token_response = response.json()
            response_error = token_response.get("error")
            if response_error == "expired_token":
                logger.debug(
                    messages.LIGHTSPEED_RESPONSE, token_endpoint, response.text
                )
                update_secure_token_status(
                    lightspeed_auth_token,
                    AuthStatus.FAILED,
                    _(messages.LIGHTSPEED_TOKEN_EXPIRED),
                )
                return
            if response_error != "authorization_pending":
                logger.debug(
                    messages.LIGHTSPEED_RESPONSE, token_endpoint, response.text
                )
                update_secure_token_status(
                    lightspeed_auth_token,
                    AuthStatus.FAILED,
                    _(messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % response.reason),
                )
                return
            logger.debug(messages.LIGHTSPEED_RESPONSE, token_endpoint, token_response)
        else:
            logger.debug(messages.LIGHTSPEED_RESPONSE, token_endpoint, response.text)
            update_secure_token_status(
                lightspeed_auth_token,
                AuthStatus.FAILED,
                _(messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % response.reason),
            )
            return

        time.sleep(interval)
        elapsed_time += interval
        if elapsed_time > expires_in:
            update_secure_token_status(
                lightspeed_auth_token,
                AuthStatus.FAILED,
                _(messages.LIGHTSPEED_LOGIN_VERIFICATION_TIMEOUT),
            )
            return
