"""Test the discovery scanner capabilities."""

# pylint: disable=ungrouped-imports
from multiprocessing import Value
from unittest.mock import Mock, patch

from ansible_runner.exceptions import AnsibleRunnerException
from django.forms import model_to_dict
from django.test import TestCase

from api.connresult.model import SystemConnectionResult
from api.models import Credential, ScanJob, ScanOptions, ScanTask, Source, SourceOptions
from api.serializers import SourceSerializer
from scanner.network import ConnectTaskRunner
from scanner.network.connect import ConnectResultStore, _connect, construct_inventory
from scanner.network.exceptions import NetworkCancelException, NetworkPauseException
from scanner.network.utils import _construct_vars
from scanner.test_util import create_scan_job


def mock_handle_ssh(cred):  # pylint: disable=unused-argument
    """Mock for handling ssh passphrase setting."""


class MockResultStore:
    """A mock ConnectResultStore."""

    def __init__(self, hosts):
        """Minimal internal variables, just to fake the state."""
        self._remaining_hosts = set(hosts)
        self.succeeded = []
        self.failed = []

    def record_result(self, name, source, credential, status):
        """Keep a list of succeeses and failures."""
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


# pylint: disable=too-many-instance-attributes
class NetworkConnectTaskRunnerTest(TestCase):
    """Tests against the ConnectTaskRunner class and functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            ssh_keyfile="keyfile",
            become_method="sudo",
            become_user="root",
            become_password="become",
        )
        self.cred.save()

        # Source with excluded hosts
        self.source = Source(
            name="source1",
            hosts=["1.2.3.4", "1.2.3.5"],
            exclude_hosts=["1.2.3.5", "1.2.3.6"],
            source_type="network",
            port=22,
        )
        self.source.save()
        self.source.credentials.add(self.cred)
        self.source.save()

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT
        )

        self.scan_task.update_stats("TEST NETWORK CONNECT.", sys_failed=0)

        # Source without excluded hosts
        self.source2 = Source(
            name="source2", hosts=["1.2.3.4"], source_type="network", port=22
        )
        self.source2.save()
        self.source2.credentials.add(self.cred)
        self.source2.save()

        self.scan_job2, self.scan_task2 = create_scan_job(
            self.source2,
            ScanTask.SCAN_TYPE_CONNECT,
            "source2",
        )

        self.scan_task2.update_stats("TEST NETWORK CONNECT.", sys_failed=0)

        # Scans with options & no excluded hosts
        source_options = SourceOptions(use_paramiko=True)
        source_options.save()
        self.source3 = Source(
            name="source3",
            hosts=["1.2.3.4", "1.2.3.5", "1.2.3.6"],
            source_type="network",
            port=22,
            options=source_options,
        )
        self.source3.save()
        self.source3.credentials.add(self.cred)
        self.source3.save()

        scan_options = ScanOptions(max_concurrency=2)
        scan_options.save()

        self.scan_job3, self.scan_task3 = create_scan_job(
            self.source3, ScanTask.SCAN_TYPE_CONNECT, "source3", scan_options
        )
        self.scan_task3.update_stats("TEST NETWORK CONNECT.", sys_failed=0)
        self.concurrency = ScanOptions.get_default_forks()

    def test_construct_vars(self):
        """Test constructing ansible vars dictionary."""
        cred = model_to_dict(self.cred)
        vars_dict = _construct_vars(22, cred)
        expected = {
            "ansible_become_pass": "become",
            "ansible_port": 22,
            "ansible_ssh_pass": "password",
            "ansible_ssh_private_key_file": "keyfile",
            "ansible_user": "username",
            "ansible_become_method": "sudo",
            "ansible_become_user": "root",
        }
        self.assertEqual(vars_dict, expected)

    def test_get_exclude_host(self):
        """Test get_exclude_hosts() method."""
        assert self.source.get_exclude_hosts() != []
        assert self.source3.get_exclude_hosts() == []

    # Tests for source1 (has hosts and excluded host)
    def test_result_store(self):
        """Test ConnectResultStore."""
        result_store = ConnectResultStore(self.scan_task)

        self.assertEqual(result_store.remaining_hosts(), ["1.2.3.4"])
        self.assertEqual(result_store.scan_task.systems_count, 1)
        self.assertEqual(result_store.scan_task.systems_scanned, 0)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

        result_store.record_result(
            "1.2.3.4", self.source, self.cred, SystemConnectionResult.UNREACHABLE
        )

        self.assertEqual(result_store.remaining_hosts(), [])
        self.assertEqual(result_store.scan_task.systems_count, 1)
        self.assertEqual(result_store.scan_task.systems_scanned, 0)
        self.assertEqual(result_store.scan_task.systems_unreachable, 1)

    def test_connect_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source["hosts"]
        exclude_hosts = source["exclude_hosts"]
        connection_port = source["port"]
        cred = model_to_dict(self.cred)
        _, inventory_dict = construct_inventory(
            hosts=hosts,
            credential=cred,
            connection_port=connection_port,
            concurrency_count=1,
            exclude_hosts=exclude_hosts,
        )
        # pylint: disable=line-too-long
        expected = {
            "all": {
                "children": {
                    "group_0": {
                        "hosts": {
                            "1.2.3.4": {
                                "ansible_host": "1.2.3.4",
                            }
                        }
                    }
                },
                "vars": {
                    "ansible_port": 22,
                    "ansible_user": "username",
                    "ansible_ssh_pass": "password",
                    "ansible_ssh_private_key_file": "keyfile",
                    "ansible_become_pass": "become",
                    "ansible_become_method": "sudo",
                    "ansible_become_user": "root",
                },
            }
        }
        assert inventory_dict == expected

    @patch("ansible_runner.run")
    @patch(
        "scanner.network.connect._handle_ssh_passphrase", side_effect=mock_handle_ssh
    )
    def test_connect_failure(self, mock_run, mock_ssh_pass):
        """Test connect flow with mocked manager and failure."""
        mock_run.side_effect = AnsibleRunnerException("Fail")
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source["hosts"]
        exclude_hosts = source["exclude_hosts"]
        connection_port = source["port"]
        with self.assertRaises(AnsibleRunnerException):
            _connect(
                Value("i", ScanJob.JOB_RUN),
                self.scan_task,
                hosts,
                Mock(),
                self.cred,
                connection_port,
                self.concurrency,
                exclude_hosts,
            )
            mock_run.assert_called()
            mock_ssh_pass.assert_called()

    @patch("ansible_runner.run")
    def test_connect(self, mock_run):
        """Test connect flow with mocked manager."""
        mock_run.return_value.status = "successful"
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source["hosts"]
        exclude_hosts = source["exclude_hosts"]
        connection_port = source["port"]
        _connect(
            Value("i", ScanJob.JOB_RUN),
            self.scan_task,
            hosts,
            Mock(),
            self.cred,
            connection_port,
            self.concurrency,
            exclude_hosts,
        )
        mock_run.assert_called()

    @patch("ansible_runner.run")
    def test_connect_ssh_crash(self, mock_run):
        """Simulate an ssh crash."""
        mock_run.return_value.status = "successful"
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source["hosts"]
        exclude_hosts = source["exclude_hosts"]
        connection_port = source["port"]
        _connect(
            Value("i", ScanJob.JOB_RUN),
            self.scan_task,
            hosts,
            Mock(),
            self.cred,
            connection_port,
            self.concurrency,
            exclude_hosts,
        )
        mock_run.assert_called()

    @patch("ansible_runner.run")
    def test_connect_ssh_hang(self, mock_run):
        """Simulate an ssh hang."""
        mock_run.return_value.status = "successful"
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source["hosts"]
        exclude_hosts = source["exclude_hosts"]
        connection_port = source["port"]
        _connect(
            Value("i", ScanJob.JOB_RUN),
            self.scan_task,
            hosts,
            Mock(),
            self.cred,
            connection_port,
            self.concurrency,
            exclude_hosts,
        )
        mock_run.assert_called()

    @patch("ansible_runner.run")
    def test_connect_runner(self, mock_run):
        """Test running a connect scan with mocked connection."""
        mock_run.return_value.status = "successful"
        scanner = ConnectTaskRunner(self.scan_job, self.scan_task)
        result_store = MockResultStore(["1.2.3.4"])
        _, result = scanner.run_with_result_store(
            Value("i", ScanJob.JOB_RUN), result_store
        )
        self.assertEqual(result, ScanTask.COMPLETED)

    # Similar tests as above modified for source2 (Does not have exclude hosts)
    def test_result_store_src2(self):
        """Test ConnectResultStore."""
        result_store = ConnectResultStore(self.scan_task3)
        hosts = ["1.2.3.4", "1.2.3.5", "1.2.3.6"]
        self.assertCountEqual(result_store.remaining_hosts(), hosts)
        self.assertEqual(result_store.scan_task.systems_count, 3)
        self.assertEqual(result_store.scan_task.systems_scanned, 0)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

        host = hosts.pop()
        result_store.record_result(
            host, self.source2, self.cred, SystemConnectionResult.SUCCESS
        )

        self.assertCountEqual(result_store.remaining_hosts(), hosts)
        self.assertEqual(result_store.scan_task.systems_count, 3)
        self.assertEqual(result_store.scan_task.systems_scanned, 1)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

        host = hosts.pop()
        # Check failure without cred
        result_store.record_result(
            host, self.source2, None, SystemConnectionResult.FAILED
        )
        self.assertCountEqual(result_store.remaining_hosts(), hosts)
        self.assertEqual(result_store.scan_task.systems_count, 3)
        self.assertEqual(result_store.scan_task.systems_scanned, 1)
        self.assertEqual(result_store.scan_task.systems_failed, 1)

        host = hosts.pop()
        # Check failure with cred
        result_store.record_result(
            host, self.source2, self.cred, SystemConnectionResult.FAILED
        )
        self.assertCountEqual(result_store.remaining_hosts(), hosts)
        self.assertEqual(result_store.scan_task.systems_count, 3)
        self.assertEqual(result_store.scan_task.systems_scanned, 1)
        self.assertEqual(result_store.scan_task.systems_failed, 2)

    def test_connect_inventory_src2(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        cred = model_to_dict(self.cred)
        _, inventory_dict = construct_inventory(
            hosts=hosts,
            credential=cred,
            connection_port=connection_port,
            concurrency_count=1,
        )
        expected = {
            "all": {
                "children": {
                    "group_0": {"hosts": {"1.2.3.4": {"ansible_host": "1.2.3.4"}}}
                },
                "vars": {
                    "ansible_port": 22,
                    "ansible_user": "username",
                    "ansible_ssh_pass": "password",
                    "ansible_ssh_private_key_file": "keyfile",
                    "ansible_become_pass": "become",
                    "ansible_become_method": "sudo",
                    "ansible_become_user": "root",
                },
            }
        }
        self.assertEqual(inventory_dict, expected)

    @patch("ansible_runner.run")
    @patch(
        "scanner.network.connect._handle_ssh_passphrase", side_effect=mock_handle_ssh
    )
    def test_connect_failure_src2(self, mock_run, mock_ssh_pass):
        """Test connect flow with mocked manager and failure."""
        mock_run.side_effect = AnsibleRunnerException("Fail")
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        with self.assertRaises(AnsibleRunnerException):
            _connect(
                Value("i", ScanJob.JOB_RUN),
                self.scan_task,
                hosts,
                Mock(),
                self.cred,
                connection_port,
                self.concurrency,
            )
            mock_run.assert_called()
            mock_ssh_pass.assert_called()

    @patch("ansible_runner.run")
    def test_connect_src2(self, mock_run):
        """Test connect flow with mocked manager."""
        mock_run.return_value.status = "successful"
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        _connect(
            Value("i", ScanJob.JOB_RUN),
            self.scan_task,
            hosts,
            Mock(),
            self.cred,
            connection_port,
            self.concurrency,
        )
        mock_run.assert_called()

    @patch("ansible_runner.run")
    def test_connect_runner_error(self, mock_run):
        """Test connect flow with mocked manager."""
        mock_run.side_effect = AnsibleRunnerException("Fail")
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        with self.assertRaises(AnsibleRunnerException):
            _connect(
                Value("i", ScanJob.JOB_RUN),
                self.scan_task,
                hosts,
                Mock(),
                self.cred,
                connection_port,
                self.concurrency,
            )
            mock_run.assert_called()

    @patch("ansible_runner.run")
    def test_connect_runner_src2(self, mock_run):
        """Test running a connect scan with mocked connection."""
        mock_run.return_value.status = "successful"
        scanner = ConnectTaskRunner(self.scan_job3, self.scan_task3)
        result_store = MockResultStore(["1.2.3.4"])
        _, result = scanner.run_with_result_store(
            Value("i", ScanJob.JOB_RUN), result_store
        )
        self.assertEqual(result, ScanTask.COMPLETED)

    @patch("ansible_runner.run")
    def test_connect_paramiko(self, mock_run):
        """Test connect with paramiko."""
        mock_run.return_value.status = "successful"
        serializer = SourceSerializer(self.source3)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        _connect(
            Value("i", ScanJob.JOB_RUN),
            self.scan_task,
            hosts,
            Mock(),
            self.cred,
            connection_port,
            self.concurrency,
        )
        mock_run.assert_called()

    @patch("ansible_runner.run")
    @patch("scanner.network.connect.settings.ANSIBLE_LOG_LEVEL", "1")
    def test_modifying_log_level(self, mock_run):
        """Test modifying the log level."""
        mock_run.return_value.status = "successful"
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        _connect(
            Value("i", ScanJob.JOB_RUN),
            self.scan_task,
            hosts,
            Mock(),
            self.cred,
            connection_port,
            self.concurrency,
        )
        mock_run.assert_called()
        calls = mock_run.mock_calls
        # Check to see if the parameter was passed into the runner.run()
        self.assertIn("verbosity=1", str(calls[0]))

    @patch("ansible_runner.run")
    @patch("scanner.network.connect.settings.DJANGO_SECRET_PATH", "None")
    def test_secret_file_fail(self, mock_run):
        """Test modifying the log level."""
        mock_run.side_effect = AnsibleRunnerException()
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        with self.assertRaises(AnsibleRunnerException):
            _connect(
                Value("i", ScanJob.JOB_RUN),
                self.scan_task,
                hosts,
                Mock(),
                self.cred,
                connection_port,
                self.concurrency,
            )
            mock_run.assert_called()

    @patch("ansible_runner.run")
    def test_unexpected_runner_response(self, mock_run):
        """Test unexpected runner response."""
        mock_run.return_value.status = "unknown"
        scanner = ConnectTaskRunner(self.scan_job, self.scan_task)
        result_store = MockResultStore(["1.2.3.4"])
        conn_dict = scanner.run_with_result_store(
            Value("i", ScanJob.JOB_RUN), result_store
        )
        self.assertEqual(conn_dict[1], ScanTask.FAILED)

    @patch("scanner.network.connect.ConnectTaskRunner.run_with_result_store")
    def test_cancel_connect(self, mock_run):
        """Test cancel of connect."""
        # Test cancel at _connect level
        serializer = SourceSerializer(self.source3)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        with self.assertRaises(NetworkCancelException):
            _connect(
                Value("i", ScanJob.JOB_TERMINATE_CANCEL),
                self.scan_task,
                hosts,
                Mock(),
                self.cred,
                connection_port,
                self.concurrency,
            )
        # Test cancel at run() level
        mock_run.side_effect = NetworkCancelException()
        scanner = ConnectTaskRunner(self.scan_job3, self.scan_task3)
        _, scan_result = scanner.run(Value("i", ScanJob.JOB_RUN))
        self.assertEqual(scan_result, ScanTask.CANCELED)

    @patch("scanner.network.connect.ConnectTaskRunner.run_with_result_store")
    def test_pause_connect(self, mock_run):
        """Test pause of connect."""
        # Test cancel at _connect level
        serializer = SourceSerializer(self.source3)
        source = serializer.data
        hosts = source["hosts"]
        connection_port = source["port"]
        with self.assertRaises(NetworkPauseException):
            _connect(
                Value("i", ScanJob.JOB_TERMINATE_PAUSE),
                self.scan_task,
                hosts,
                Mock(),
                self.cred,
                connection_port,
                self.concurrency,
            )
        # Test cancel at run() level
        mock_run.side_effect = NetworkPauseException()
        scanner = ConnectTaskRunner(self.scan_job3, self.scan_task3)
        _, scan_result = scanner.run(Value("i", ScanJob.JOB_RUN))
        self.assertEqual(scan_result, ScanTask.PAUSED)

    def test_run_manager_interupt(self):
        """Test manager interupt for run method."""
        scanner = ConnectTaskRunner(self.scan_job, self.scan_task)
        conn_dict = scanner.run(Value("i", ScanJob.JOB_TERMINATE_CANCEL))
        self.assertEqual(conn_dict[1], ScanTask.CANCELED)

    @patch("scanner.network.connect.ConnectTaskRunner.run_with_result_store")
    def test_run_success_return_connect(self, mock_run):
        """Test pause of connect."""
        # Test cancel at run() level
        mock_run.side_effect = [[None, ScanTask.COMPLETED]]
        scanner = ConnectTaskRunner(self.scan_job3, self.scan_task3)
        _, scan_result = scanner.run(Value("i", ScanJob.JOB_RUN))
        self.assertEqual(scan_result, ScanTask.COMPLETED)

    @patch("scanner.network.connect._connect")
    def test_connect_exception(self, mock_run):
        """Test pause of connect."""
        # Test cancel at run() level
        mock_run.side_effect = AnsibleRunnerException("fail")
        scanner = ConnectTaskRunner(self.scan_job3, self.scan_task3)
        _, scan_result = scanner.run(Value("i", ScanJob.JOB_RUN))
        self.assertEqual(scan_result, ScanTask.FAILED)

    @patch("ansible_runner.run")
    def test_empty_hosts(self, mock_run):
        """Test running a connect scan with mocked connection."""
        mock_run.return_value.status = "successful"
        scanner = ConnectTaskRunner(self.scan_job, self.scan_task)
        result_store = MockResultStore([])
        _, result = scanner.run_with_result_store(
            Value("i", ScanJob.JOB_RUN), result_store
        )
        self.assertEqual(result, ScanTask.COMPLETED)
