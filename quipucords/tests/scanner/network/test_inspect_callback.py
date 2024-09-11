"""Test InspectCallback."""

import logging
import os

import ansible_runner
import pytest
import yaml
from ansible.parsing.yaml.dumper import AnsibleDumper

from api.models import InspectResult, Scan
from log_messages import TASK_UNEXPECTED_FAILURE
from scanner.network.inspect_callback import InspectCallback


@pytest.fixture
def event_ok():
    """
    Return a successful Ansible event.

    This was collected while debugging `InspectCallback.event_callback` during an actual
    network scan.
    """
    return {
        "uuid": "9d097760-4d2c-43e5-8aba-d1a0e825aed7",
        "counter": 140,
        "stdout": "ok: [127.0.0.1] => <...>",
        "start_line": 395,
        "end_line": 401,
        "runner_ident": "84418d26-0363-4924-92f2-d9f545f2a8ef",
        "event": "runner_on_ok",
        "pid": 84005,
        "created": "2024-02-02T12:25:42.424553",
        "parent_uuid": "6c946626-0f07-0f23-a006-000000000038",
        "event_data": {
            "playbook": "<...>",
            "playbook_uuid": "470be249-5d66-43f8-a768-8bbfa7446f7b",
            "play": "group_0",
            "play_uuid": "6c946626-0f07-0f23-a006-000000000002",
            "play_pattern": " group_0 ",
            "task": "set internal_have_rpm_user",
            "task_uuid": "6c946626-0f07-0f23-a006-000000000038",
            "task_action": "set_fact",
            "resolved_action": "ansible.builtin.set_fact",
            "task_args": "",
            "task_path": "<...>",
            "role": "check_dependencies",
            "host": "127.0.0.1",
            "remote_addr": "127.0.0.1",
            "res": {
                "ansible_facts": {"internal_have_rpm_user": True},
                "_ansible_no_log": None,
                "changed": False,
            },
            "start": "2024-02-02T12:25:42.412059",
            "end": "2024-02-02T12:25:42.424405",
            "duration": 0.012346,
            "event_loop": None,
            "uuid": "9d097760-4d2c-43e5-8aba-d1a0e825aed7",
        },
    }


@pytest.fixture
def event_failed():
    """
    Return an Ansible event with "failed" status.

    This was collected while debugging `InspectCallback.event_callback` during an actual
    network scan.
    """
    return {
        "uuid": "5a29fb37-da65-4d2e-92f6-826b924ccfbf",
        "counter": 125,
        "stdout": "fatal: [127.0.0.1]: FAILED! => <...>",
        "start_line": 309,
        "end_line": 321,
        "runner_ident": "13ff256b-b793-47d7-b26f-9028f05d9e09",
        "event": "runner_on_failed",
        "pid": 74971,
        "created": "2024-02-02T11:49:38.377767",
        "parent_uuid": "6c946626-0f07-7c1b-37f1-000000000035",
        "event_data": {
            "playbook": "<...>",
            "playbook_uuid": "a0ff6f63-c1b8-46fe-ab9c-092a50cffb28",
            "play": "group_0",
            "play_uuid": "6c946626-0f07-7c1b-37f1-000000000002",
            "play_pattern": " group_0 ",
            "task": "gather internal_have_java_cmd",
            "task_uuid": "6c946626-0f07-7c1b-37f1-000000000035",
            "task_action": "raw",
            "resolved_action": "ansible.builtin.raw",
            "task_args": "",
            "task_path": "<...>",
            "role": "check_dependencies",
            "host": "127.0.0.1",
            "remote_addr": "127.0.0.1",
            "res": {
                "rc": 1,
                "stdout": "",
                "stdout_lines": [],
                "stderr": "Shared connection to 127.0.0.1 closed.\r\n",
                "stderr_lines": ["Shared connection to 127.0.0.1 closed."],
                "changed": True,
                "msg": "non-zero return code",
                "_ansible_no_log": None,
            },
            "start": "2024-02-02T11:49:38.299511",
            "end": "2024-02-02T11:49:38.377629",
            "duration": 0.078118,
            "ignore_errors": True,
            "event_loop": None,
            "uuid": "5a29fb37-da65-4d2e-92f6-826b924ccfbf",
        },
    }


@pytest.fixture
def event_unreachable():
    """
    Return an Ansible event with "unreachable" status.

    This was collected while debugging `InspectCallback.event_callback` during an actual
    network scan. Some longer strings were replaced with <...>. In order to achieve the
    unreachable status the target VM scanned was terminated mid-scan.
    """
    return {
        "uuid": "26079e2e-6bad-46b5-a64d-feea7e0f6ab5",
        "counter": 684,
        "stdout": "fatal: [127.0.0.1]: UNREACHABLE! => <...>",
        "start_line": 1856,
        "end_line": 1861,
        "runner_ident": "84418d26-0363-4924-92f2-d9f545f2a8ef",
        "event": "runner_on_unreachable",
        "pid": 84005,
        "created": "2024-02-02T12:31:26.330981",
        "parent_uuid": "6c946626-0f07-0f23-a006-0000000000a9",
        "event_data": {
            "playbook": "<...>",
            "playbook_uuid": "470be249-5d66-43f8-a768-8bbfa7446f7b",
            "play": "group_0",
            "play_uuid": "6c946626-0f07-0f23-a006-000000000002",
            "play_pattern": " group_0 ",
            "task": "gather dmi.processor-family fact",
            "task_uuid": "6c946626-0f07-0f23-a006-0000000000a9",
            "task_action": "raw",
            "resolved_action": "ansible.builtin.raw",
            "task_args": "",
            "task_path": "<...>",
            "role": "dmi",
            "host": "127.0.0.1",
            "remote_addr": "127.0.0.1",
            "start": "2024-02-02T12:31:26.258798",
            "end": "2024-02-02T12:31:26.330843",
            "duration": 0.072045,
            "res": {
                "unreachable": True,
                "msg": "Failed to connect to the host via ssh: <...>",
                "changed": False,
            },
            "uuid": "26079e2e-6bad-46b5-a64d-feea7e0f6ab5",
        },
    }


@pytest.fixture
def fact_with_bad_bytes():
    """
    Return a collected Ansible fact that contains "bad" bytes.

    This represents a fact with not-UTF8-safe bytes like seen in a customer bug report.
    This was collected while debugging `InspectCallback._process_task_facts` during an
    actual network scan that triggered this condition.
    """
    return {
        "internal_system_user_count": {
            "rc": 0,
            "stdout": (
                "root:x:0:0:root:/root:/bin/bash\r\n"
                "ß´˜µ∫∑´®˙∆˚©ƒ∑´®¨˚˙∆ß∂ƒ∫≤“‘æ…≤≤µ˜e\udcc0\udcc0\udcf4\udcff:x:"
                "69420:69420:i am a potato:/home/potato:/bin/bash\r\n"
            ),
            "stdout_lines": [
                "root:x:0:0:root:/root:/bin/bash",
                (
                    "ß´˜µ∫∑´®˙∆˚©ƒ∑´®¨˚˙∆ß∂ƒ∫≤“‘æ…≤≤µ˜e\udcc0\udcc0\udcf4\udcff:x:"
                    "69420:69420:i am a potato:/home/potato:/bin/bash"
                ),
            ],
            "stderr": "Shared connection to 127.0.0.1 closed.\r\n",
            "stderr_lines": ["Shared connection to 127.0.0.1 closed."],
            "changed": True,
            "failed": False,
        }
    }


class TestInspectCallback:
    """TestCase for InspectCallback."""

    def test_unexpected_event(self, mocker):
        """Test how event_callback handles an unexpected event."""
        # Ideally this test should be done with caplog fixture, but TIL it
        # won't easily work with DEBUG level messages. See
        # https://github.com/pytest-dev/pytest/issues/7162
        # https://github.com/pytest-dev/pytest/issues/3697
        patched_logger = mocker.patch("scanner.network.inspect_callback.logger")
        callback = InspectCallback()
        event_data = {"some_data": "some_value"}
        assert callback.event_callback(event_data) is None
        patched_logger.debug.assert_called_with(
            TASK_UNEXPECTED_FAILURE, "event_callback", "'unknown event'", event_data
        )

    def test_task_on_ok(self, event_ok, mocker):
        """Test InspectCallback.event_callback in a successful event."""
        callback = InspectCallback()
        patched_task_on_ok = mocker.patch.object(
            InspectCallback, "task_on_ok", wraps=callback.task_on_ok
        )
        callback.event_callback(event_ok)
        patched_task_on_ok.assert_called_once_with(event_ok)
        # this host and facts are hardcoded on event_ok fixture
        assert callback._ansible_facts["127.0.0.1"] == {"internal_have_rpm_user": True}

    @pytest.mark.parametrize("ignore_errors", (True, False))
    def test_task_on_failed(  # noqa: PLR0913
        self, event_failed, mocker, caplog, ignore_errors
    ):
        """Test InspectCallback.event_callback in a failed event."""
        expected_messages = [
            "[host=127.0.0.1 role='check_dependencies' task='gather "
            "internal_have_java_cmd'] failed | reason: non-zero return code | rc: 1 | "
            "stderr: Shared connection to 127.0.0.1 closed. | stdout: N/A"
        ]
        caplog.set_level(logging.ERROR)
        callback = InspectCallback()
        patched_task_on_failed = mocker.patch.object(
            InspectCallback, "task_on_failed", wraps=callback.task_on_failed
        )
        # the fixture has this hardcoded to True. let's exercise togling it
        # (even though this seems unnecessary since our roles abuse ignore_errors)
        callback.event_callback(event_failed)
        patched_task_on_failed.assert_called_once_with(event_failed)
        # event_failed fixture don't have ansible facts - in fact, none of the
        # events produced in my local system produced facts.
        assert callback._ansible_facts == {}
        # hardcoded host+error message on event_failed fixture
        assert caplog.messages == expected_messages

    def test_task_on_failed_with_ansible_facts(self, event_failed, caplog):
        """Test InspectCallback.event_callback in a failed event."""
        caplog.set_level(logging.WARNING)
        callback = InspectCallback()
        event_failed["event_data"]["res"]["ansible_facts"] = {"watermelon": "melancia"}
        callback.event_callback(event_failed)
        assert callback._ansible_facts["127.0.0.1"] == {"watermelon": "melancia"}
        assert caplog.messages == [
            "[host=127.0.0.1 role='check_dependencies' task='gather internal_have_java_cmd'] failed | reason: non-zero return code | rc: 1 | stderr: Shared connection to 127.0.0.1 closed. | stdout: N/A",  # noqa: E501
            "[host=127.0.0.1 role='check_dependencies' task='gather internal_have_java_cmd'] FAILED and contains ansible_facts",  # noqa: E501
        ]

    def test_task_on_unreachable(self, event_unreachable, mocker):
        """Test InspectCallback.event_callback in a unreachable event."""
        callback = InspectCallback()
        patched_task_on_unreachable = mocker.patch.object(
            InspectCallback, "task_on_unreachable", wraps=callback.task_on_unreachable
        )
        callback.event_callback(event_unreachable)
        patched_task_on_unreachable.assert_called_once_with(event_unreachable)
        # this host is hardcoded on the fixture
        assert "127.0.0.1" in callback._unreachable_hosts

    @pytest.mark.parametrize(
        "facts,is_unreachable,expected_status",
        (
            ({"host_done": True}, False, InspectResult.SUCCESS),
            # maybe we should consider the next one successful
            ({"host_done": True}, True, InspectResult.UNREACHABLE),
            ({"pineapple": "abacaxi"}, True, InspectResult.UNREACHABLE),
            ({"strawberry": "morango"}, False, InspectResult.FAILED),
            ({"host_done": "some string"}, False, InspectResult.FAILED),
            ({"host_done": False}, False, InspectResult.FAILED),
        ),
    )
    def test_results(self, facts, is_unreachable, expected_status):
        """Test InspectCallback.iter_results."""
        callback = InspectCallback()
        callback._ansible_facts = {"host": facts}
        if is_unreachable:
            callback._unreachable_hosts.add("host")
        results = next(callback.iter_results())
        assert results.facts == facts
        assert results.status == expected_status

    def test_fact_sanitization_bad_byte_strings(self, caplog, fact_with_bad_bytes):
        """Test InspectCallback._process_task_facts with "bad" bytes in strings."""
        caplog.set_level(logging.WARNING)
        original_line = fact_with_bad_bytes["internal_system_user_count"][
            "stdout_lines"
        ][1]
        hostname = "buggyhost"
        callback = InspectCallback()
        callback._process_task_facts(fact_with_bad_bytes, hostname)
        modified_line = callback._ansible_facts[hostname]["internal_system_user_count"][
            "stdout_lines"
        ][1]
        assert original_line != modified_line, "bad line was not modified"
        assert "????" not in original_line
        assert "????" in modified_line
        assert caplog.record_tuples[0][1] == logging.WARNING
        assert caplog.record_tuples[0][2] == (
            f"[host={hostname}] Sanitized value for 'internal_system_user_count' "
            "changed from its original value."
        )


@pytest.fixture
def local_inventory(tmp_path):
    """Create a inventory for ansible to connect with localhost."""
    inventory = {"all": {"hosts": {"localhost": {"ansible_connection": "local"}}}}
    inventory_file = tmp_path / "inventory.yml"
    contents = yaml.dump(
        inventory, allow_unicode=True, default_flow_style=False, Dumper=AnsibleDumper
    )
    inventory_file.write_text(contents)
    return str(inventory_file)


@pytest.mark.slow
@pytest.mark.integration
def test_inspect_callback_with_inspect_playbook(settings, local_inventory):
    """Smoketest InspectCallback integration with ansible_runner."""
    playbook_path = str(settings.BASE_DIR / "scanner/network/runner/inspect.yml")
    callback = InspectCallback()

    runner_obj = ansible_runner.run(
        inventory=local_inventory,
        event_handler=callback.event_callback,
        playbook=playbook_path,
        extravars=Scan.get_default_extra_vars(),
    )
    assert runner_obj.status == "successful"
    all_results = list(callback.iter_results())
    assert len(all_results) == 1
    results = all_results[0]
    assert results.host == "localhost"
    assert results.status == InspectResult.SUCCESS
    # spot check at least one fact we expect to always work
    assert results.facts["uname_hostname"] == os.uname().nodename
