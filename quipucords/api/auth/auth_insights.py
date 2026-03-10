"""Authentication support for Insights."""

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
from api.auth.utils import AuthError, decode_jwt
from api.common.enumerators import AuthStatus
from api.secure_token.model import SecureToken
from quipucords.settings import QUIPUCORDS_AUTH_INSIGHTS_TIMEOUT

logger = getLogger(__name__)

# At this time, we support a single Insights JWT token for the logged in Discovery user.
# So we use the single "insights-jwt-token" SecureToken token for the user.

DISCOVERY_CLIENT_ID = "discovery-client-id"
INSIGHTS_REALM = "redhat-external"
INSIGHTS_SCOPE = "api.console"
GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
OPENID_CONFIG_ENDPOINT = (
    f"/auth/realms/{INSIGHTS_REALM}/.well-known/openid-configuration"
)
DEVICE_AUTH_ENDPOINT_KEY = "device_authorization_endpoint"
ENDPOINT_KEY = "token_endpoint"

CONFIG_HOST_KEY = "host"
CONFIG_PORT_KEY = "port"
CONFIG_USE_HTTP = "use_http"
CONFIG_SSL_VERIFY = "ssl_verify"
CONFIG_SSO_HOST_KEY = "sso_host"

DEFAULT_HOST_INSIGHTS_CONFIG = "console.redhat.com"
DEFAULT_PORT_INSIGHTS_CONFIG = 443
DEFAULT_USE_HTTP_INSIGHTS_CONFIG = False
DEFAULT_SSO_HOST_INSIGHTS_CONFIG = "sso.redhat.com"

DEFAULT_INSIGHTS_CONFIG = {
    CONFIG_HOST_KEY: DEFAULT_HOST_INSIGHTS_CONFIG,
    CONFIG_PORT_KEY: DEFAULT_PORT_INSIGHTS_CONFIG,
    CONFIG_USE_HTTP: DEFAULT_USE_HTTP_INSIGHTS_CONFIG,
    CONFIG_SSO_HOST_KEY: DEFAULT_SSO_HOST_INSIGHTS_CONFIG,
}

INSIGHTS_NAME = "insights-jwt-token"
INSIGHTS_TYPE = "insights-jwt"


class InsightsAuthError(Exception):
    """Class for Insights device authorization errors."""

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


def update_secure_token_metadata(secure_token, decoded_insights_jwt):
    """Update the SecureToken metadata based on the Insights Auth Token."""
    payload = decoded_insights_jwt["payload"]
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
    secure_token.expires_at = decoded_insights_jwt["expires_at"]
    secure_token.save()


def insights_login_request(user):
    """Request an Insights login authorization for the user."""
    # we send the request for device authorization here, however, we can't block
    # the API on waiting for the user to authorize it, so we kick off the
    # insights_wait_for_authorization task asynchronously via celery.
    try:
        auth_request = insights_request_auth()
        logger.info("Insights login authorization requested")
        logger.info(f"User Code: {auth_request['user_code']}")
        logger.info(f"Authorization URL: {auth_request['verification_uri_complete']}")
        insights_secure_token = get_or_create_insights_secure_token(user)
        clear_insights_auth_token(insights_secure_token)
        update_secure_token_status(insights_secure_token, AuthStatus.PENDING)

        data = {
            "status": insights_secure_token.metadata["status"],
            "user_code": auth_request["user_code"],
            "verification_uri": auth_request["verification_uri"],
            "verification_uri_complete": auth_request["verification_uri_complete"],
        }

        insights_wait_for_authorization.delay(
            insights_secure_token.id,
            auth_request["device_code"],
            auth_request["interval"],
            auth_request["expires_in"],
        )

        return data
    except InsightsAuthError as err:
        logger.error(_(err.message))
        raise AuthError(err.message)


def insights_token_check_expiration(insights_secure_token):
    """Check and Update the Insights SecureToken status if expired."""
    if insights_secure_token.metadata:
        metadata = insights_secure_token.metadata
        status = metadata["status"]
        if status == AuthStatus.VALID.value:
            if insights_secure_token.is_expired():
                if insights_secure_token.user:
                    logger.info(
                        _(
                            messages.INSIGHTS_TOKEN_EXPIRED_FOR_USER
                            % insights_secure_token.user.username
                        )
                    )
                update_secure_token_status(
                    insights_secure_token,
                    AuthStatus.EXPIRED,
                    _(messages.INSIGHTS_TOKEN_EXPIRED),
                )


def insights_auth_status(user):
    """Return the Insights Authentication status for the user."""
    insights_secure_token = get_insights_secure_token(user)
    auth_token_missing = {
        "status": AuthStatus.MISSING.value,
    }
    if insights_secure_token:
        insights_token_check_expiration(insights_secure_token)
        metadata = insights_secure_token.metadata
        if metadata:
            return {
                "status": metadata["status"],
                "metadata": metadata,
            }
    return auth_token_missing


def get_insights_secure_token(user) -> SecureToken | None:
    """Get the SecureToken for the user, None if it does not exist."""
    user_secure_token = SecureToken.objects.filter(user=user)
    if user_secure_token.exists():
        return user_secure_token.first()
    return None

def get_or_create_insights_secure_token(user) -> SecureToken:
    """Get a SecureToken for the user."""
    secure_token, created = SecureToken.objects.get_or_create(
        name=INSIGHTS_NAME, token_type=INSIGHTS_TYPE, user=user
    )
    if created:
        logger.debug(
            f"New {secure_token.token_type} Token {secure_token.name}"
            f" created for user {user.username}, Token id: {secure_token.id}"
        )
    return secure_token


def clear_insights_auth_token(insights_auth_token: SecureToken):
    """Clear the Insights authentication token."""
    if insights_auth_token:
        insights_auth_token.token = None
        insights_auth_token.metadata = None
        insights_auth_token.expires_at = None
        insights_auth_token.save()


def get_sso_endpoint(endpoint):
    """Get the SSO OpenID Configuration endpoint."""
    insights_sso_server = DEFAULT_INSIGHTS_CONFIG[CONFIG_SSO_HOST_KEY]
    url = f"https://{insights_sso_server}{OPENID_CONFIG_ENDPOINT}"  # Always SSL
    try:
        logger.info(_(messages.INSIGHTS_SSO_CONFIG_QUERY), url, endpoint)
        response = requests.get(url, timeout=QUIPUCORDS_AUTH_INSIGHTS_TIMEOUT)
    except ConnectionError as err:
        raise err
    except BaseHTTPError as err:
        raise err

    config = response.json()
    if endpoint not in config:
        raise InsightsAuthError(_(messages.INSIGHTS_SSO_QUERY_FAILED % endpoint))
    return config[endpoint]


def insights_request_auth():
    """Initialize an Insights a device authorization workflow request.

    :returns: authorization request object
    """
    auth_request = None

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "grant_type": GRANT_TYPE,
        "scope": INSIGHTS_SCOPE,
        "client_id": DISCOVERY_CLIENT_ID,
    }
    try:
        device_auth_endpoint = get_sso_endpoint(DEVICE_AUTH_ENDPOINT_KEY)
        logger.info(_(messages.INSIGHTS_LOGIN_REQUEST), device_auth_endpoint)
        response = requests.post(
            device_auth_endpoint,
            headers=headers,
            data=params,
            timeout=settings.QUIPUCORDS_AUTH_INSIGHTS_TIMEOUT,
        )
    except ConnectionError as err:
        raise InsightsAuthError(_(messages.INSIGHTS_LOGIN_REQUEST_FAILED % err))
    except BaseHTTPError as err:
        raise InsightsAuthError(_(messages.INSIGHTS_LOGIN_REQUEST_FAILED % err))

    if response.status_code == http.HTTPStatus.OK:
        auth_request = response.json()
        logger.debug(_(messages.INSIGHTS_RESPONSE), device_auth_endpoint, auth_request)
    else:
        logger.debug(_(messages.INSIGHTS_RESPONSE), device_auth_endpoint, response.text)
        raise InsightsAuthError(
            _(messages.INSIGHTS_LOGIN_REQUEST_FAILED % response.reason)
        )

    return auth_request


@celery.shared_task()
@transaction.atomic
def insights_wait_for_authorization(secure_token_id, device_code, interval, expires_in):  # noqa: C901 PLR0911 PLR0912
    """Wait for the user to log in and authorize the Insights authorization request.

    Updates the Insights Authentication SecureToken.
    """
    try:
        insights_auth_token = SecureToken.objects.get(id=secure_token_id)
    except ObjectDoesNotExist:
        logger.error(
            _(
                "Invalid Insights SecureToken id %s specified,"
                " cannot wait for authorization."
            )
            % secure_token_id
        )
        return

    elapsed_time = 0
    insights_jwt = None

    update_secure_token_status(insights_auth_token, AuthStatus.PENDING)

    token_endpoint = None
    while not insights_jwt:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": GRANT_TYPE,
            "client_id": DISCOVERY_CLIENT_ID,
            "device_code": device_code,
        }
        try:
            if not token_endpoint:
                token_endpoint = get_sso_endpoint(ENDPOINT_KEY)
            logger.debug(_(messages.INSIGHTS_LOGIN_VERIFYING), token_endpoint)
            response = requests.post(
                token_endpoint,
                headers=headers,
                data=params,
                timeout=settings.QUIPUCORDS_AUTH_INSIGHTS_TIMEOUT,
            )
        except ConnectionError as err:
            update_secure_token_status(
                insights_auth_token,
                AuthStatus.FAILED,
                _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % err),
            )
            return
        except BaseHTTPError as err:
            update_secure_token_status(
                insights_auth_token,
                AuthStatus.FAILED,
                _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % err),
            )
            return

        if response.status_code == http.HTTPStatus.OK:
            token_response = response.json()
            insights_jwt = token_response["access_token"]
            decoded_insights_jwt = decode_jwt(insights_jwt)
            if not decoded_insights_jwt:
                update_secure_token_status(
                    insights_auth_token,
                    AuthStatus.FAILED,
                    _(messages.INSIGHTS_INVALID_TOKEN),
                )
                return
            insights_auth_token.token = insights_jwt
            insights_auth_token.save()
            update_secure_token_metadata(insights_auth_token, decoded_insights_jwt)
            update_secure_token_status(insights_auth_token, AuthStatus.VALID)
            return
        if response.status_code == http.HTTPStatus.BAD_REQUEST:
            token_response = response.json()
            response_error = token_response.get("error")
            if response_error == "expired_token":
                logger.debug(
                    _(messages.INSIGHTS_RESPONSE), token_endpoint, response.text
                )
                update_secure_token_status(
                    insights_auth_token,
                    AuthStatus.FAILED,
                    _(messages.INSIGHTS_LOGIN_VERIFICATION_TIMEOUT),
                )
                return
            if response_error != "authorization_pending":
                logger.debug(
                    _(messages.INSIGHTS_RESPONSE), token_endpoint, response.text
                )
                update_secure_token_status(
                    insights_auth_token,
                    AuthStatus.FAILED,
                    _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % response.reason),
                )
                return
            logger.debug(_(messages.INSIGHTS_RESPONSE), token_endpoint, token_response)
        else:
            logger.debug(_(messages.INSIGHTS_RESPONSE), token_endpoint, response.text)
            update_secure_token_status(
                insights_auth_token,
                AuthStatus.FAILED,
                _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % response.reason),
            )
            return

        time.sleep(interval)
        elapsed_time += interval
        if elapsed_time > expires_in:
            update_secure_token_status(
                insights_auth_token,
                AuthStatus.FAILED,
                _(messages.INSIGHTS_LOGIN_VERIFICATION_TIMEOUT),
            )
            return
