"""Supporting methods for handling JWT tokens."""

import base64
import datetime
import json

# Number of dot separated parts in a valid JWT token.
JWT_PARTS = 3


class AuthError(Exception):
    """Class for /auth authentication errors."""

    def __init__(self, message, *args):
        """Take message as mandatory attribute."""
        super().__init__(message, *args)
        self.message = message


# Methods that add support for decoding JWT tokens.
def decode_jwt_part(jwt_part):
    """Decode the URL-safe base64 encoded JWT part, handling padding issues."""
    # Add max padding (==) - it will be ignored if not needed
    padded_jwt_part = jwt_part + "=="
    # Decode from URL-safe base64
    decoded_bytes = base64.urlsafe_b64decode(padded_jwt_part)
    # Convert bytes to string and load as JSON
    decoded_string = decoded_bytes.decode("utf-8")
    return json.loads(decoded_string)


def decode_jwt(jwt_token) -> dict | None:
    """Split the token into its parts and return header, payload and expires_at."""
    jwt_token_parts = jwt_token.split(".")

    if len(jwt_token_parts) == JWT_PARTS:
        header = decode_jwt_part(jwt_token_parts[0])
        payload = decode_jwt_part(jwt_token_parts[1])
        expires_at = (
            datetime.datetime.fromtimestamp(int(payload["exp"]), datetime.UTC)
            if payload["exp"]
            else None
        )

        return {"header": header, "payload": payload, "expires_at": expires_at}
    else:
        # Not 3-parts, Invalid JWT Token received
        return None
