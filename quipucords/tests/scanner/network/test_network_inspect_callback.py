"""Test the scanner.network.InspectCallback class."""

import logging

from scanner.network import InspectCallback


def test_inspect_callback_task_on_unreachable(caplog, faker):
    """Test task_on_unreachable populates _unreachable_hosts and logs an error."""
    caplog.set_level(logging.ERROR)
    callback = InspectCallback()
    assert len(callback._unreachable_hosts) == 0
    expected_address = faker.ipv4_private()
    expected_error_message = faker.sentence()
    # Real values for this dict originate from within Ansible and are far more complex.
    # This is a minimal representation of only what task_on_unreachable needs.
    event_dict = {
        "event_data": {"host": expected_address, "res": {"msg": expected_error_message}}
    }
    callback.task_on_unreachable(event_dict)

    assert len(callback._unreachable_hosts) == 1
    assert expected_address in callback._unreachable_hosts

    first_error_log = caplog.messages[0]
    assert expected_address in first_error_log
    assert expected_error_message in first_error_log
    assert "UNREACHABLE" in first_error_log
