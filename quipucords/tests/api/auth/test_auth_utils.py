"""Test the Auth API Utils."""

from api.auth.utils import decode_jwt


class TestJWT:
    """Test the JWT decoding functions."""

    def test_jwt_decode(self, jwt_header_dict, jwt_payload_dict, test_jwt):
        """Test that a JWT is properly decoded."""
        decoded_jwt_token = decode_jwt(test_jwt)
        assert isinstance(decoded_jwt_token, dict)
        assert decoded_jwt_token["header"] == jwt_header_dict
        assert decoded_jwt_token["payload"] == jwt_payload_dict

    def test_invalid_jwt_decode(self, jwt_header, jwt_payload):
        """Test that an Invalid JWT returns None."""
        invalid_jwt = f"{jwt_header}.{jwt_payload}"
        decoded_jwt_token = decode_jwt(invalid_jwt)
        assert decoded_jwt_token is None
