"""Test the inspect scanner capabilities."""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from ansible_runner.exceptions import AnsibleRunnerException
from django.forms import model_to_dict
from django.test import override_settings

from api.inspectresult.model import RawFact
from api.models import (
    Credential,
    ScanJob,
    ScanTask,
    Source,
    SystemConnectionResult,
)
from api.serializers import SourceSerializer
from constants import GENERATED_SSH_KEYFILE, SCAN_JOB_LOG
from scanner.network import InspectTaskRunner
from scanner.network.inspect import construct_inventory, run_with_result_store
from tests.scanner.test_util import create_scan_job

ANSIBLE_FACTS = "ansible_facts"


class MockResultStore:
    """A mock ConnectResultStore."""

    def __init__(self, hosts):
        """Minimal internal variables, just to fake the state."""
        self._remaining_hosts = set(hosts)
        self.succeeded = []
        self.failed = []

    def record_result(self, name, source, credential, status):
        """Keep a list of successes and failures."""
        if status == SystemConnectionResult.SUCCESS:
            self.succeeded.append((name, source, credential, status))
        elif status == SystemConnectionResult.FAILED:
            self.failed.append((name, source, credential, status))
        else:
            raise ValueError()

        self._remaining_hosts.remove(name)

    def remaining_hosts(self):
        """Need this method because the task runner uses it."""
        return list(self._remaining_hosts)


@pytest.mark.django_db
class TestNetworkInspectScanner:
    """Tests network inspect scan task class."""

    def setup_method(self, _test_method):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            ssh_keyfile=None,
            become_method=None,
            become_user=None,
            become_password=None,
        )
        self.cred.save()

        self.cred_data = model_to_dict(self.cred)
        self.cred_data[GENERATED_SSH_KEYFILE] = None

        # setup source for scan
        self.source = Source(name="source1", port=22, hosts=["1.2.3.4"])
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host_list = [("1.2.3.4", self.cred_data)]

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT
        )

        self.connect_scan_task = self.scan_task.prerequisites.first()
        self.connect_scan_task.update_stats("TEST NETWORK CONNECT.", sys_failed=0)

        conn_result = self.connect_scan_task.connection_result
        success_sys = SystemConnectionResult(
            name="1.2.3.4",
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        success_sys.save()
        failed_sys = SystemConnectionResult(
            name="1.1.1.2",
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        failed_sys.save()
        conn_result.save()

        self.connect_scan_task.update_stats(
            "TEST_VC.", sys_count=2, sys_failed=1, sys_scanned=1
        )
        self.connect_scan_task.status_complete()
        self.scan_task.update_stats("TEST NETWORK INSPECT.", sys_failed=0)
        self.scan_job.save()
        self.stop_states = [ScanJob.JOB_TERMINATE_CANCEL, ScanJob.JOB_TERMINATE_PAUSE]

    @patch("scanner.network.inspect.run_with_result_store")
    def test_check_connection_basic_happy_path(self, mock_run, mocker):
        """Test expected output of successful initial check_connection."""
        mock_run.side_effect = [[None, ScanTask.COMPLETED]]
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mock_inspect = mocker.patch.object(
            scanner, "inspect", return_value=[None, ScanTask.COMPLETED]
        )
        _, scan_result = scanner.run()
        assert scan_result == ScanTask.COMPLETED
        mock_inspect.assert_called()

    @patch("scanner.network.inspect._connect")
    def test_handle_ansible_exception_during_check_connection(self, mock_run, mocker):
        """Test early return due to Ansible exception."""
        mock_run.side_effect = AnsibleRunnerException("fail")
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mock_inspect = mocker.patch.object(scanner, "inspect")
        _, scan_result = scanner.run()
        assert scan_result == ScanTask.FAILED
        mock_inspect.assert_not_called()

    @patch("ansible_runner.run")
    def test_check_connection_run_with_result_store_empty_hosts(self, mock_run):
        """Test happy path with initial check_connection via run_with_result_store."""
        mock_run.return_value.status = "successful"
        result_store = MockResultStore([])
        _, result = run_with_result_store(
            self.connect_scan_task, self.scan_job, result_store
        )
        assert result == ScanTask.COMPLETED

    def test_scan_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        connection_port = source["port"]
        inventory_dict = construct_inventory(self.host_list, connection_port, 50)
        expected = {
            "all": {
                "children": {
                    "group_0": {
                        "hosts": {
                            "1.2.3.4": {
                                "ansible_user": "username",
                                "ansible_ssh_pass": "password",
                                "ansible_host": "1.2.3.4",
                            }
                        }
                    }
                },
                "vars": {"ansible_port": 22},
            }
        }

        assert inventory_dict[1] == expected

    def test_scan_inventory_grouping(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        connection_port = source["port"]
        inventory_dict = construct_inventory(
            [
                ("1.2.3.1", self.cred_data),
                ("1.2.3.2", self.cred_data),
                ("1.2.3.3", self.cred_data),
                ("1.2.3.4", self.cred_data),
            ],
            connection_port,
            1,
        )
        expected = {
            "all": {
                "children": {
                    "group_0": {
                        "hosts": {
                            "1.2.3.1": {
                                "ansible_user": "username",
                                "ansible_ssh_pass": "password",
                                "ansible_host": "1.2.3.1",
                            }
                        }
                    },
                    "group_1": {
                        "hosts": {
                            "1.2.3.2": {
                                "ansible_user": "username",
                                "ansible_ssh_pass": "password",
                                "ansible_host": "1.2.3.2",
                            }
                        }
                    },
                    "group_2": {
                        "hosts": {
                            "1.2.3.3": {
                                "ansible_user": "username",
                                "ansible_ssh_pass": "password",
                                "ansible_host": "1.2.3.3",
                            }
                        }
                    },
                    "group_3": {
                        "hosts": {
                            "1.2.3.4": {
                                "ansible_user": "username",
                                "ansible_ssh_pass": "password",
                                "ansible_host": "1.2.3.4",
                            }
                        }
                    },
                },
                "vars": {"ansible_port": 22},
            }
        }

        assert inventory_dict[1] == expected

    @patch("ansible_runner.run")
    def test_inspect_scan_failure(self, mock_run, caplog, mocker):
        """Test scan flow with mocked manager and failure."""
        mock_run.side_effect = AnsibleRunnerException()
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        scanner.connect_scan_task = self.connect_scan_task
        caplog.set_level(logging.ERROR)
        _, scan_result = scanner._inspect_scan(self.host_list)
        # an error should not prevent scan completion
        assert scan_result == "completed"
        # no raw fact produced, given the errors
        assert RawFact.objects.count() == 0

    @patch("scanner.network.inspect.InspectTaskRunner._inspect_scan")
    def test_inspect_scan_error(self, mock_scan, mocker):
        """Test scan flow with mocked manager and failure."""
        mock_scan.side_effect = AnsibleRunnerException()
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        scan_task_status = scanner.run()
        mock_scan.assert_called_with(self.host_list)
        assert scan_task_status[1] == ScanTask.FAILED

    @patch("ansible_runner.run")
    def test_inspect_scan_fail_no_facts(self, mock_run, mocker):
        """Test running a inspect scan with mocked connection."""
        mock_run.return_value.status = "successful"
        mocker.patch.object(InspectTaskRunner, "_persist_ansible_logs")
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        scanner.connect_scan_task = self.connect_scan_task
        scan_task_status = scanner.run()
        mock_run.assert_called()
        assert scan_task_status[1] == ScanTask.FAILED

    @pytest.mark.skip("This test is not running properly and taking a long time")
    def test_ssh_crash(self, mocker):
        """Simulate an ssh crash."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        path = Path(__file__).absolute().parent / "test_util/crash.py"

        _, result = scanner._inspect_scan(self.host_list, base_ssh_executable=path)
        assert result == ScanTask.COMPLETED

    @pytest.mark.skip("This test is not running properly and taking a long time")
    def test_ssh_hang(self, mocker):
        """Simulate an ssh hang."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        path = Path(__file__).absolute().parent / "test_util/hang.py"

        scanner._inspect_scan(
            self.host_list, base_ssh_executable=path, ssh_timeout="0.1s"
        )

    @patch("ansible_runner.run")
    def test_scan_with_options(self, mock_run, mocker):
        """Setup second scan with scan and source options."""
        # setup source with paramiko option for scan
        self.source = Source(
            name="source2", port=22, hosts=["1.2.3.4"], use_paramiko=True
        )
        self.source.save()
        self.source.credentials.add(self.cred)

        # setup scan with options
        scan_options = {"enabled_extended_product_search": {"search_directories": []}}

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT, "scan2", scan_options=scan_options
        )

        # run scan
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )

        scanner.connect_scan_task = self.connect_scan_task
        with patch.object(InspectTaskRunner, "_persist_ansible_logs"):
            scanner._inspect_scan(self.host_list)
        mock_run.assert_called()

    @patch("scanner.network.inspect.InspectTaskRunner._obtain_discovery_data")
    def test_no_reachable_host_after_check_connection(self, discovery, mocker):
        """Test FAILED end state when no reachable hosts exist."""
        discovery.return_value = [], [], [], []
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        scan_task_status = scanner.run()
        assert scan_task_status[1] == ScanTask.FAILED

    @patch("ansible_runner.run")
    @override_settings(ANSIBLE_LOG_LEVEL=1)
    def test__inspect_scan_with_modified_ansible_log_level(self, mock_run, mocker):
        """Test modifying ANSIBLE_LOG_LEVEL (from default 3 to 1) sends arg to run."""
        mock_run.return_value.status = "successful"
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        mocker.patch.object(
            scanner, "check_connection", return_value=[None, ScanTask.COMPLETED]
        )
        mocker.patch.object(scanner, "_persist_ansible_logs")
        scanner._inspect_scan(self.host_list)
        mock_run.assert_called_once()
        run_call = mock_run.mock_calls[0]
        # Check to see if the parameter was passed into the runner.run()
        assert "verbosity" in run_call.kwargs
        assert run_call.kwargs["verbosity"] == 1


def test_inspect_scan_with_multiple_inspection_groups_stdout_logs(mocker, settings):
    """Ensure all logs are collected when inspection have multiple groups."""
    # mock functions with side effects writing to files or db - we don't need those
    # for this test purpose because they generate input for the main functions we
    # will patch later
    mocker.patch("scanner.network.inspect.write_to_yaml")
    mocker.patch("scanner.network.inspect.InspectCallback")
    # this is ESSENTIAL: "group1" and "group2" are the multiple inspection groups
    # this test requires
    mocker.patch(
        "scanner.network.inspect.construct_inventory",
        Mock(return_value=(("group1", "group2"), Mock())),
    )
    # mock representing the output of ansible_runner.run
    ansible_runner_obj = Mock()
    ansible_runner_obj.stdout.read.side_effect = lambda: "ansible stdout"
    ansible_runner_obj.stderr.read.side_effect = lambda: "ansible stderr"
    ansible_runner_obj.status = "successful"
    mocker.patch(
        "scanner.network.inspect.ansible_runner.run",
        Mock(return_value=ansible_runner_obj),
    )
    # we should be using a scanjob from db, but that would make the test
    # unnecessarily slow (just by initializing db in a test we "lose" 2 seconds
    # while this unit test alone takes less than half a second)
    scanjob = Mock(id=999)
    scanjob.get_extra_vars.side_effect = lambda: {}
    # InspectTaskRunner requires scanjob and scan_task
    inspect_runner = InspectTaskRunner(scanjob, Mock())
    # sanity check expected files
    stdout_log: Path = settings.LOG_DIRECTORY / SCAN_JOB_LOG.format(
        scan_job_id=scanjob.id, output_type="ansible-stdout"
    )
    assert not stdout_log.exists()
    stderr_log: Path = settings.LOG_DIRECTORY / SCAN_JOB_LOG.format(
        scan_job_id=scanjob.id, output_type="ansible-stderr"
    )
    assert not stderr_log.exists()
    # finally, call the method that will "execute" the inspection scan
    # and persist logs
    inspect_runner._inspect_scan(Mock())
    assert stdout_log.exists()
    assert stderr_log.exists()
    # rationale: since we have 2 inspection groups, content from ansible runner
    # output shall be saved twice
    assert stdout_log.read_text().splitlines() == 2 * ["ansible stdout"]
    assert stderr_log.read_text().splitlines() == 2 * ["ansible stderr"]
