"""Authentication support for Insights."""

from api.secure_token.model import SecureToken

# At this time, we support a single Insights JWT token for the logged in Discovery user.
# So we use the single "insights-jwt-token" SecureToken token for the user.

INSIGHTS_NAME = "insights-jwt-token"
INSIGHTS_TYPE = "insights-jwt"


def insights_login(user):
    """Login the Discovery user to the Insights server and get a token."""
    auth_token, created = SecureToken.objects.get_or_create(
        name=INSIGHTS_NAME, token_type=INSIGHTS_TYPE, user=user
    )

    if created:
        print(
            f"New {auth_token.token_type} Token {auth_token.name}"
            f" created for user {user.username}, Token id: {auth_token.id}"
        )
    else:
        print(
            f"Using {auth_token.token_type} Token {auth_token.name}"
            f" for user {user.username}, Token id: {auth_token.id}"
        )

    data = {
        "token_id": auth_token.id,
        "token_name": auth_token.name,
        "token_type": auth_token.token_type,
        "expires_at": auth_token.expires_at,
    }
    return data
