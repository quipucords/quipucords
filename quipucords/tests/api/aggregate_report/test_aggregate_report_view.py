"""Test the aggregate report view."""

from unittest import mock

import pytest
from django.urls import reverse


@pytest.mark.django_db
@mock.patch("api.aggregate_report.view.get_serialized_aggregate_report")
def test_aggregate_report_view_success(
    mock_get_aggregate_report, faker, client_logged_in
):
    """Test happy path for aggregate report view."""
    report_id = faker.pyint()
    expected_response = {faker.slug(): faker.slug()}
    mock_get_aggregate_report.return_value = expected_response
    url = reverse("v1:reports-aggregate", args=(report_id,))
    response = client_logged_in.get(url)
    mock_get_aggregate_report.assert_called_once_with(report_id)
    assert response.ok
    assert response.json() == expected_response


@pytest.mark.django_db
@mock.patch("api.aggregate_report.view.get_serialized_aggregate_report")
def test_aggregate_report_view_not_found(
    mock_get_aggregate_report, faker, client_logged_in
):
    """Test 404 handling for aggregate report view when report does not exist."""
    mock_get_aggregate_report.return_value = None
    report_id = faker.pyint()
    url = reverse("v1:reports-aggregate", args=(report_id,))
    response = client_logged_in.get(url)
    mock_get_aggregate_report.assert_called_once_with(report_id)
    assert not response.ok
    assert response.status_code == 404
