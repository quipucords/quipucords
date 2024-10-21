"""Test the quipucords.api.signals module."""

import pytest
from axes.models import AccessAttempt
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings as drf_settings

NON_FIELD_ERRORS_KEY = drf_settings.NON_FIELD_ERRORS_KEY


@pytest.fixture
def axes_blocked(qpc_user_simple, faker):
    """Ensure the user has sufficient Axes login failures to be blocked."""
    AccessAttempt.objects.select_for_update().get_or_create(
        username=qpc_user_simple.username,
        ip_address=faker.ipv4(),
        user_agent=faker.user_agent(),
        defaults={
            "failures_since_start": 1234567890,
        },
    )


@pytest.mark.django_db
def test_token_login_triggers_axes_limit_error(
    qpc_user_simple, axes_blocked, settings, client_logged_out, faker
):
    """Test expected 403 response from token API when Axes blocks login."""
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"] = "1/day"
    response = client_logged_out.post(
        reverse("v1:token"),
        data={"username": qpc_user_simple.username, "password": faker.password()},
    )
    assert not response.ok
    assert response.status_code == status.HTTP_403_FORBIDDEN
    response_json = response.json()
    assert response_json[NON_FIELD_ERRORS_KEY] == ["Too many failed login attempts."]
