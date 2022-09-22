# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test OCPEntities methods."""

import pytest

from scanner.openshift.entities import OCPError


@pytest.mark.parametrize("reason", ["FOO", "BAR"])
@pytest.mark.parametrize("status", [999, 123, 456])
@pytest.mark.parametrize(
    "error_body,expected_message",
    [
        ('{"foo": "bar"}', '{"foo": "bar"}'),
        ('{"foo": "bar", "message": "error message"}', "error message"),
        ("<NOTAJSON", "<NOTAJSON"),
    ],
)
def test_message_parsing(mocker, error_body, expected_message, status, reason):
    """Test OCPError message parsing."""
    # mimic OCP lib ApiException
    mock_exception = mocker.Mock(status=status, reason=reason, body=error_body)
    error = OCPError.from_api_exception(mock_exception)
    assert isinstance(error, OCPError)
    assert error.status == status
    assert error.reason == reason
    assert error.message == expected_message
