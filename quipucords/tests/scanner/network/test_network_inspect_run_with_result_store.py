"""
Test the scanner.network.inspect.run_with_result_store function.

These tests invoke run_with_result_store, but run_with_result_store is only called
by the network-type's InspectTaskRunner.check_connection method. When we refactor
the network task runner to flatten the "connect" and "inspect" halves into one loop,
the logic being tested here will change, and these tests should be replaced.

TODO Refactor or remove these tests when we simplify network inspection.
"""

from unittest.mock import Mock, patch

import pytest

from api.connresult.model import SystemConnectionResult
from api.models import Credential, Scan, ScanTask, Source
from scanner.network.inspect import ConnectResultStore, run_with_result_store
from scanner.network.utils import construct_inventory
from tests.scanner.test_util import create_scan_job


def build_ansible_run_inventory(
    source: Source,
    scan_job: "ScanJob",  # noqa: F821
) -> tuple[list[str], dict]:
    """Build inventory for Ansible run, simulating _connect function's inner logic."""
    group_names, inventory = construct_inventory(
        hosts=source.hosts,
        credential={},  # required dict arg, but value is irrelevant for testing
        connection_port=42069,  # required int arg, but value is irrelevant for testing
        concurrency_count=scan_job.options.get(
            "max_concurrency", Scan.DEFAULT_MAX_CONCURRENCY
        ),
        exclude_hosts=source.exclude_hosts,
    )
    return group_names, inventory


def build_ansible_run_side_effect(  # noqa: PLR0913
    source: Source,
    cred: Credential,
    result_store: ConnectResultStore,
    group_names: list[str],
    inventory: dict,
    host_statuses: dict = None,
    runner_obj_statuses: list = None,
) -> list[callable]:
    """
    Build a value to assign to a mocked `ansible_run.run`'s `side_effect`.

    The underlying logic here is surprisingly complex; so, here's an explanation:

    When we are testing `_connect` either directly or indirectly, we need to alter the
    behavior of a mocked `ansible_run.run` invoked inside `_connect`. The real `run`
    takes args (`event_handler`, `cancel_callback`) that it internally calls at certain
    stages of execution, and we rely on some of the side effects of those being called.
    For example, when the real `run` succeeds for a host, it calls `event_handler` which
    results in a `ConnectResultCallback.task_on_ok` call that writes an update to our
    database through `ConnectResultStore.record_result` to `ScanTask.increment_stats`.
    Why do we care about the value `ScanTask.increment_stats` would write to the DB?
    Moving up the stack back to the `_connect` function itself, later logic checks those
    written stats to determine if there were any successful connections, and that result
    can determine the overall status returned by `_connect` which we are testing.

    Why are we returning a generator of new functions as the `.side_effect`? When we
    test `_connect` or anything that invokes it, if the source has more than one host,
    internally the `_connect` function may split the inventory and invoke `run` several
    times. By assigning a function generator to the mocked `run.side_effect`, we get
    the appropriate and distinct database-writing side effects for each `run` call, and
    we can expect the appropriate return value from `_connect` that is derived from
    those updated database records.
    """
    if host_statuses is None:
        host_statuses = {}

    def run_side_effect(hosts: list[str], *args, **kwargs):
        """Record result as a side effect like ansible_runner.run normally would do."""
        for host in hosts:
            result_store.record_result(
                host,
                source,
                cred,
                host_statuses.get(host, SystemConnectionResult.SUCCESS),
            )
        mock_runner_obj = Mock()
        if runner_obj_statuses:
            mock_runner_obj.status = runner_obj_statuses.pop(0)
        else:
            mock_runner_obj.status = "successful"
        return mock_runner_obj

    def side_effect_generator(_group_names: list[str], _inventory: dict):
        """Generate side effects for each time `ansible_runner.run` is called."""
        for group_name in _group_names:
            hosts = _inventory["all"]["children"][group_name]["hosts"].keys()
            yield run_side_effect(hosts)

    return side_effect_generator(group_names, inventory)


@pytest.mark.django_db
@patch("ansible_runner.run")
def test_run_with_result_store_with_one_host_success(
    mock_run, network_source, network_credential
):
    """
    Test running run_with_result_store with one host.

    This simple-looking test has a lot of its setup hidden in the
    build_ansible_run_side_effect helper function. Really what we are testing here
    is that run_with_result_store behaves as expected when Ansible runner's run
    function returns the synthetic "successful" result from that we generated from
    build_ansible_run_side_effect.
    """
    # TODO replace connect_scan_task with inspect_scan_task
    scan_job, connect_scan_task = create_scan_job(network_source)
    result_store = ConnectResultStore(connect_scan_task)

    group_names, inventory = build_ansible_run_inventory(network_source, scan_job)
    assert len(group_names) == 1  # 1 not-excluded host -> 1 group

    mock_run.side_effect = build_ansible_run_side_effect(
        network_source, network_credential, result_store, group_names, inventory
    )
    _, result = run_with_result_store(connect_scan_task, scan_job, result_store)
    assert mock_run.call_count == len(group_names)
    assert result == ScanTask.COMPLETED


@pytest.fixture
def network_source_with_three_hosts(network_credential, faker) -> Source:
    """Return a Source with a network-type Credential for scan."""
    host_addresses = [faker.ipv4(), faker.ipv4(), faker.ipv4()]
    source = Source.objects.create(
        name="network-source-name", port=faker.pyint(), hosts=host_addresses
    )
    source.credentials.add(network_credential)
    return source


@pytest.mark.django_db
@patch("ansible_runner.run")
def test_connect_runner_multiple_host_groups_success(
    mock_run, network_source_with_three_hosts, network_credential
):
    """
    Test running run_with_result_store with three hosts over two groups.

    Like test_run_with_result_store_with_one_host_success, this test relies on
    build_ansible_run_side_effect hiding a lot of mock setup complexity.
    """
    source = network_source_with_three_hosts  # just to keep lines short
    # TODO replace connect_scan_task with inspect_scan_task
    scan_job, connect_scan_task = create_scan_job(
        source, scan_options={"max_concurrency": 2}
    )
    result_store = ConnectResultStore(connect_scan_task)

    group_names, inventory = build_ansible_run_inventory(source, scan_job)
    assert len(group_names) == 2  # 3 hosts, max_concurrency 2 -> 2 groups

    mock_run.side_effect = build_ansible_run_side_effect(
        source, network_credential, result_store, group_names, inventory
    )
    _, result = run_with_result_store(connect_scan_task, scan_job, result_store)
    assert mock_run.call_count == len(group_names)
    assert result == ScanTask.COMPLETED


@pytest.mark.django_db
@patch("ansible_runner.run")
def test_connect_runner_all_hosts_unreachable(
    mock_run, network_source_with_three_hosts, network_credential
):
    """
    Test running run_with_result_store with three hosts that are all unreachable.

    Like test_run_with_result_store_with_one_host_success, this test relies on
    build_ansible_run_side_effect hiding a lot of the mock setup complexity.
    """
    source = network_source_with_three_hosts  # just to keep lines short
    # TODO replace connect_scan_task with inspect_scan_task
    scan_job, connect_scan_task = create_scan_job(
        source, scan_options={"max_concurrency": 2}
    )
    result_store = ConnectResultStore(connect_scan_task)

    group_names, inventory = build_ansible_run_inventory(source, scan_job)
    assert len(group_names) == 2  # 3 hosts, max_concurrency 2 -> 2 groups

    host_statuses = {host: SystemConnectionResult.UNREACHABLE for host in source.hosts}
    runner_obj_statuses = ["failed", "failed"]
    mock_run.side_effect = build_ansible_run_side_effect(
        source,
        network_credential,
        result_store,
        group_names,
        inventory,
        host_statuses,
        runner_obj_statuses,
    )
    _, result = run_with_result_store(connect_scan_task, scan_job, result_store)
    assert mock_run.call_count == len(group_names)
    assert result == ScanTask.FAILED


@pytest.mark.django_db
@patch("ansible_runner.run")
def test_connect_runner_some_hosts_unreachable(
    mock_run, network_source_with_three_hosts, network_credential
):
    """
    Test running run_with_result_store with three hosts when some are unreachable.

    Like test_run_with_result_store_with_one_host_success, this test relies on
    build_ansible_run_side_effect hiding a lot of the mock setup complexity.
    """
    source = network_source_with_three_hosts  # just to keep lines short
    # TODO replace connect_scan_task with inspect_scan_task
    scan_job, connect_scan_task = create_scan_job(
        source, scan_options={"max_concurrency": 2}
    )
    result_store = ConnectResultStore(connect_scan_task)

    group_names, inventory = build_ansible_run_inventory(source, scan_job)
    assert len(group_names) == 2  # 3 hosts, max_concurrency 2 -> 2 groups

    hosts = source.hosts[::]
    host_statuses = {hosts.pop(): SystemConnectionResult.SUCCESS}
    host_statuses.update({host: SystemConnectionResult.UNREACHABLE for host in hosts})
    runner_obj_statuses = ["failed", "failed"]
    # Why are both groups failed? The group with the successful host also has one
    # that fails, and Ansible runner considers that an overall failure. ¯\_(ツ)_/¯

    mock_run.side_effect = build_ansible_run_side_effect(
        source,
        network_credential,
        result_store,
        group_names,
        inventory,
        host_statuses,
        runner_obj_statuses,
    )
    _, result = run_with_result_store(connect_scan_task, scan_job, result_store)
    assert mock_run.call_count == len(group_names)
    assert result == ScanTask.COMPLETED


@pytest.mark.django_db
@patch("ansible_runner.run")
def test_run_with_result_store_unexpected_runner_response(
    mock_run, network_source_with_three_hosts, network_credential
):
    """Test handle unexpected runner response in run_with_result_store."""
    """
    Test running run_with_result_store with three hosts when some are unreachable.

    Like test_run_with_result_store_with_one_host_success, this test relies on
    build_ansible_run_side_effect hiding a lot of the mock setup complexity.
    """
    mock_run.return_value.status = "unknown"
    source = network_source_with_three_hosts  # just to keep lines short
    # TODO replace connect_scan_task with inspect_scan_task
    scan_job, connect_scan_task = create_scan_job(
        source, scan_options={"max_concurrency": 2}
    )
    result_store = ConnectResultStore(connect_scan_task)

    conn_dict = run_with_result_store(connect_scan_task, scan_job, result_store)
    assert conn_dict[1] == ScanTask.FAILED
