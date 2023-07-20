"""Test the inspect scanner capabilities."""
from multiprocessing import Value
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
import requests_mock
from ansible_runner.exceptions import AnsibleRunnerException
from django.forms import model_to_dict
from django.urls import reverse

from api.models import (
    Credential,
    ExtendedProductSearchOptions,
    ScanJob,
    ScanOptions,
    ScanTask,
    Source,
    SourceOptions,
    SystemConnectionResult,
)
from api.serializers import SourceSerializer
from scanner.network import InspectTaskRunner
from scanner.network.exceptions import NetworkCancelException, NetworkPauseException
from scanner.network.inspect import construct_inventory
from scanner.network.inspect_callback import InspectResultCallback
from scanner.network.utils import delete_ssh_keyfiles, is_gen_ssh_keyfile
from tests.api.credential.test_credential import generate_openssh_pkey
from tests.scanner.test_util import create_scan_job

ANSIBLE_FACTS = "ansible_facts"


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

        self.fact_endpoint = "http://testserver" + reverse("reports-list")

        self.scan_job.save()
        self.stop_states = [ScanJob.JOB_TERMINATE_CANCEL, ScanJob.JOB_TERMINATE_PAUSE]
        self.interrupt = Mock(value=ScanJob.JOB_RUN)

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

    @pytest.fixture
    def openssh_key(self, faker):
        """Return an openssh_key random OpenSSH private key."""
        return generate_openssh_pkey(faker)

    @pytest.fixture
    def cred_ssh(self, openssh_key):
        """Return a Credential with an ssh_key."""
        return Credential.objects.create(
            name="cred_ssh",
            username="username_ssh",
            ssh_key=openssh_key,
        )

    @pytest.fixture
    def source_ssh(self, cred_ssh):
        """Return a Source with an SSH Credential for scan."""
        source_ssh = Source.objects.create(
            name="source_ssh", port=22, hosts=["1.2.3.5"]
        )
        source_ssh.credentials.add(cred_ssh)
        return source_ssh

    @pytest.fixture
    def host_ssh_list(self, cred_ssh):
        """Return the Host list for the SSH Credential."""
        return [("1.2.3.5", model_to_dict(cred_ssh))]

    def test_scan_inventory_with_valid_ssh_key(self, source_ssh, host_ssh_list):
        """Test construct ansible inventory dictionary with ssh_key."""
        serializer = SourceSerializer(source_ssh)
        source_ssh = serializer.data
        connection_port = source_ssh["port"]
        _, inventory_dict = construct_inventory(host_ssh_list, connection_port, 50)

        ssh_keyfile = inventory_dict["all"]["children"]["group_0"]["hosts"]["1.2.3.5"][
            "ansible_ssh_private_key_file"
        ]
        assert is_gen_ssh_keyfile(ssh_keyfile)
        Path(ssh_keyfile).unlink()

    def test_scan_inventory_with_ssh_key_delete(self, source_ssh, host_ssh_list):
        """Test ansible inventory dictionary with ssh_key are deleted."""
        serializer = SourceSerializer(source_ssh)
        source_ssh = serializer.data
        connection_port = source_ssh["port"]
        _, inventory_dict = construct_inventory(host_ssh_list, connection_port, 50)

        ssh_keyfile = inventory_dict["all"]["children"]["group_0"]["hosts"]["1.2.3.5"][
            "ansible_ssh_private_key_file"
        ]
        assert Path(ssh_keyfile).exists()
        delete_ssh_keyfiles(inventory_dict)
        assert not Path(ssh_keyfile).exists()

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
    def test_inspect_scan_failure(self, mock_run):
        """Test scan flow with mocked manager and failure."""
        mock_run.side_effect = AnsibleRunnerException()
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        scanner.connect_scan_task = self.connect_scan_task
        with pytest.raises(AnsibleRunnerException):
            scanner._inspect_scan(Value("i", ScanJob.JOB_RUN), self.host_list)
            mock_run.assert_called()

    @patch("scanner.network.inspect.InspectTaskRunner._inspect_scan")
    def test_inspect_scan_error(self, mock_scan):
        """Test scan flow with mocked manager and failure."""
        mock_scan.side_effect = AnsibleRunnerException()
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        scan_task_status = scanner.run(Value("i", ScanJob.JOB_RUN))
        mock_scan.assert_called_with(ANY, self.host_list)
        assert scan_task_status[1] == ScanTask.FAILED

    @patch("ansible_runner.run")
    def test_inspect_scan_fail_no_facts(self, mock_run):
        """Test running a inspect scan with mocked connection."""
        mock_run.return_value.status = "successful"
        with requests_mock.Mocker() as mocker:
            mocker.post(self.fact_endpoint, status_code=201, json={"id": 1})
            scanner = InspectTaskRunner(self.scan_job, self.scan_task)
            scanner.connect_scan_task = self.connect_scan_task
            scan_task_status = scanner.run(Value("i", ScanJob.JOB_RUN))
            mock_run.assert_called()
            assert scan_task_status[1] == ScanTask.FAILED

    @pytest.mark.skip("This test is not running properly and taking a long time")
    def test_ssh_crash(self):
        """Simulate an ssh crash."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        path = Path(__file__).absolute().parent / "test_util/crash.py"

        _, result = scanner._inspect_scan(
            Value("i", ScanJob.JOB_RUN),
            self.host_list,
            base_ssh_executable=path,
        )
        assert result == ScanTask.COMPLETED

    @pytest.mark.skip("This test is not running properly and taking a long time")
    def test_ssh_hang(self):
        """Simulate an ssh hang."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        path = Path(__file__).absolute().parent / "test_util/hang.py"

        scanner._inspect_scan(
            Value("i", ScanJob.JOB_RUN),
            self.host_list,
            base_ssh_executable=path,
            ssh_timeout="0.1s",
        )

    @patch("ansible_runner.run")
    def test_scan_with_options(self, mock_run):
        """Setup second scan with scan and source options."""
        # setup source with paramiko option for scan
        source_options = SourceOptions()
        source_options.save()
        self.source = Source(
            name="source2", port=22, options=source_options, hosts=["1.2.3.4"]
        )
        self.source.save()
        self.source.credentials.add(self.cred)

        # setup scan with options
        extended = ExtendedProductSearchOptions()
        extended.save()
        scan_options = ScanOptions(enabled_extended_product_search=extended)
        scan_options.save()

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT, "scan2", scan_options=scan_options
        )

        # run scan
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)

        scanner.connect_scan_task = self.connect_scan_task
        scanner._inspect_scan(Value("i", ScanJob.JOB_RUN), self.host_list)
        mock_run.assert_called()

    def test_populate_callback(self):
        """Test the population of the callback object for inspect scan."""
        callback = InspectResultCallback(
            scan_task=self.scan_task, manager_interrupt=self.interrupt
        )
        # cleaned unused variabled from event_dict
        event_dict = {
            "runner_ident": "f2100bac-7d64-43d2-8e6a-022c6f5104ac",
            "event": "runner_on_unreachable",
            "event_data": {
                "play": "group_0",
                "play_pattern": " group_0 ",
                "task": "test if user has sudo cmd",
                "task_action": "raw",
                "role": "check_dependencies",
                "host": "1.2.3.4",
                "res": {
                    "unreachable": True,
                    "msg": "Failed to connect to the host via ssh: ",
                    "changed": False,
                },
                "pid": 2210,
            },
        }
        callback.task_on_unreachable(event_dict)

    def test_run_manager_interupt(self):
        """Test manager interupt for inspect run method."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        terminate = Value("i", ScanJob.JOB_TERMINATE_CANCEL)
        scan_task_status = scanner.run(terminate)
        assert scan_task_status[1] == ScanTask.CANCELED

    @patch("scanner.network.inspect.InspectTaskRunner._obtain_discovery_data")
    def test_no_reachable_host(self, discovery):
        """Test no reachable host."""
        discovery.return_value = [], [], [], []
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        scan_task_status = scanner.run(Value("i", ScanJob.JOB_RUN))
        assert scan_task_status[1] == ScanTask.FAILED

    def test_cancel_inspect(self):
        """Test cancel of inspect."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        with pytest.raises(NetworkCancelException):
            scanner.connect_scan_task = self.connect_scan_task
            scanner._inspect_scan(
                Value("i", ScanJob.JOB_TERMINATE_CANCEL), self.host_list
            )

    def test_pause_inspect(self):
        """Test pause of inspect."""
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        with pytest.raises(NetworkPauseException):
            scanner.connect_scan_task = self.connect_scan_task
            scanner._inspect_scan(
                Value("i", ScanJob.JOB_TERMINATE_PAUSE), self.host_list
            )

    @patch("ansible_runner.run")
    @patch("scanner.network.inspect.settings.ANSIBLE_LOG_LEVEL", "1")
    def test_modifying_log_level(self, mock_run):
        """Test modifying the log level."""
        mock_run.return_value.status = "successful"
        scanner = InspectTaskRunner(self.scan_job, self.scan_task)
        scanner._inspect_scan(Value("i", ScanJob.JOB_RUN), self.host_list)
        mock_run.assert_called()
        calls = mock_run.mock_calls
        # Check to see if the parameter was passed into the runner.run()
        assert "verbosity=1" in str(calls[0])
