"""Authentication support for Insights."""

import http
import time
from logging import getLogger

import requests
from django.conf import settings
from django.utils.translation import gettext as _
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

from api import messages
from api.auth.utils import AuthError, decode_jwt
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


def insights_login(user):
    """Login the Discovery user to the Insights server and get a token."""
    insights_jwt = request_insights_jwt(user)
    decoded_insights_jwt = decode_jwt(insights_jwt)
    if not decoded_insights_jwt:
        raise AuthError(_("Invalid Insights JWT Token received."))
    insights_secure_token = get_insights_secure_token(user)
    insights_secure_token.token = insights_jwt
    payload = decoded_insights_jwt["payload"]
    insights_secure_token.metadata = {
        "org_id": payload["organization"]["id"],
        "account_number": payload["organization"]["account_number"],
        "username": payload["preferred_username"],
        "first_name": payload["given_name"],
        "last_name": payload["family_name"],
        "email": payload["email"],
    }
    insights_secure_token.expires_at = decoded_insights_jwt["expires_at"]
    insights_secure_token.save()
    data = {
        "token_id": insights_secure_token.id,
        "token_name": insights_secure_token.name,
        "token_type": insights_secure_token.token_type,
        "expires_at": insights_secure_token.expires_at,
        "token_size": len(insights_secure_token.token),
        "metadata": insights_secure_token.metadata,
    }
    return data


def request_insights_jwt(user):
    """Request Insights login authorization."""
    try:
        insights_auth = InsightsAuth()
        auth_request = insights_auth.request_auth()
        logger.info("Insights login authorization requested")
        logger.info(f"User Code: {auth_request['user_code']}")
        logger.info(f"Authorization URL: {auth_request['verification_uri_complete']}")
        logger.info("Waiting for login authorization ...")
        insights_jwt = insights_auth.wait_for_authorization()
        logger.info("Login authorization successful.")
        return insights_jwt
    except InsightsAuthError as err:
        logger.error(_(err.message))
        raise err


def get_insights_secure_token(user):
    """Get a SecureToken for the user."""
    secure_token, created = SecureToken.objects.get_or_create(
        name=INSIGHTS_NAME, token_type=INSIGHTS_TYPE, user=user
    )
    if created:
        logger.info(
            f"New {secure_token.token_type} Token {secure_token.name}"
            f" created for user {user.username}, Token id: {secure_token.id}"
        )
    else:
        logger.info(
            f"Using {secure_token.token_type} Token {secure_token.name}"
            f" for user {user.username}, Token id: {secure_token.id}"
        )
    clear_insights_auth_token(secure_token)
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


class InsightsAuth:
    """Implement the Insights Device Authorization workflow."""

    def __init__(self):
        self.auth_request = None
        self.token_response = None
        self.auth_token = None

    def request_auth(self):
        """Initialize a device authorization workflow request.

        :returns: authorization request object
        """
        self.auth_request = None

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
            self.auth_request = response.json()
            logger.debug(
                _(messages.INSIGHTS_RESPONSE), device_auth_endpoint, self.auth_request
            )
        else:
            logger.debug(
                _(messages.INSIGHTS_RESPONSE), device_auth_endpoint, response.text
            )
            raise InsightsAuthError(
                _(messages.INSIGHTS_LOGIN_REQUEST_FAILED % response.reason)
            )

        return self.auth_request

    def wait_for_authorization(self):  # noqa: C901 PLR0912
        """Wait for the user to log in and authorize the request.

        :returns: user JWT token
        """
        if self.auth_request:
            device_code = self.auth_request["device_code"]
            interval = self.auth_request.get("interval", 5)  # SSO default
            expires_in = self.auth_request.get("expires_in", 600)  # SSO default

            elapsed_time = 0
            self.auth_token = None

            token_endpoint = None
            while not self.auth_token:
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
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % err)
                    )
                except BaseHTTPError as err:
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % err)
                    )

                if response.status_code == http.HTTPStatus.OK:
                    self.token_response = response.json()
                    self.auth_token = self.token_response["access_token"]
                    break
                if response.status_code == http.HTTPStatus.BAD_REQUEST:
                    self.token_response = response.json()
                    response_error = self.token_response.get("error")
                    if response_error == "expired_token":
                        logger.debug(
                            _(messages.INSIGHTS_RESPONSE),
                            token_endpoint,
                            response.text,
                        )
                        raise InsightsAuthError(
                            _(messages.INSIGHTS_LOGIN_VERIFICATION_TIMEOUT)
                        )
                    if response_error != "authorization_pending":
                        logger.debug(
                            _(messages.INSIGHTS_RESPONSE),
                            token_endpoint,
                            response.text,
                        )
                        raise InsightsAuthError(
                            _(
                                messages.INSIGHTS_LOGIN_VERIFICATION_FAILED
                                % response.reason
                            )
                        )
                    else:
                        logger.debug(
                            _(messages.INSIGHTS_RESPONSE),
                            token_endpoint,
                            self.token_response,
                        )
                else:
                    logger.debug(
                        _(messages.INSIGHTS_RESPONSE),
                        token_endpoint,
                        response.text,
                    )
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % response.reason)
                    )

                time.sleep(interval)
                elapsed_time += interval
                if elapsed_time > expires_in:
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_TIMEOUT)
                    )

        return self.auth_token
