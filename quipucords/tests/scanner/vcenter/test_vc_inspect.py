"""Test the vcenter inspect capabilities."""

from datetime import datetime
from multiprocessing import Value
from unittest.mock import ANY, Mock, patch

import pytest
from pyVmomi import vim

from api.models import Credential, ScanJob, ScanTask, Source
from scanner.vcenter.inspect import InspectTaskRunner, get_nics
from tests.scanner.test_util import create_scan_job


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


@pytest.mark.django_db
class TestVCenterInspectTaskRunnerTest:
    """Tests against the InspectTaskRunner class and functions."""

    runner = None

    def setup_method(self, _test_method):
        """Create test case setup."""
        cred = Credential(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        cred.save()

        source = Source(name="source1", port=22, hosts=["1.2.3.4"])

        source.save()
        source.credentials.add(cred)

        self.scan_job, self.scan_task = create_scan_job(
            source, ScanTask.SCAN_TYPE_INSPECT
        )

        self.connect_scan_task = self.scan_task.prerequisites.first()
        self.connect_scan_task.update_stats("TEST_VC.", sys_count=5)
        self.connect_scan_task.status_complete()

        # Create task runner
        self.runner = InspectTaskRunner(
            scan_job=self.scan_job, scan_task=self.scan_task
        )

    def test_get_nics(self):
        """Test the get_nics method."""
        guest = Mock()
        nics = []
        for k in range(0, 2):
            nic = Mock()
            network = Mock()
            nic.network = network
            nic.macAddress = "mac" + str(k)
            ip_config = Mock()
            ip_addr = Mock()
            ip_addr.ipAddress = "ip" + str(k)
            addresses = [ip_addr]
            ip_config.ipAddress = addresses
            nic.ipConfig = ip_config
            nics.append(nic)
        guest.net = nics
        mac_addresses, ip_addresses = get_nics(guest.net)
        assert mac_addresses == ["mac0", "mac1"]
        assert ip_addresses == ["ip0", "ip1"]

    def test__none(self):
        """Test get result method when no results exist."""
        results = self.scan_task.get_result().first()
        assert results is None

    def test_get_result(self):
        """Test get results method when results exist."""
        results = list(self.scan_task.get_result())
        assert results == list(self.scan_task.get_result().all())

    def test_parse_parent_props(self):
        """Test the parse_parent_props_method."""
        obj = vim.ClusterComputeResource("domain-c7")

        folder = vim.Folder("group-h1")
        props = [
            vim.DynamicProperty(name="name", val="cluster1"),
            vim.DynamicProperty(name="parent", val=folder),
        ]

        expected_facts = {
            "type": "vim.ClusterComputeResource",
            "name": "cluster1",
            "parent": str(folder),
        }
        results = self.runner.parse_parent_props(obj, props)
        assert results == expected_facts

    def test_parse_cluster_props(self):
        """Test the parse_cluster_props_method."""
        datacenter = vim.Datacenter("datacenter-1")
        folder = vim.Folder("group-h1")

        parents_dict = {}
        parents_dict[str(datacenter)] = {"type": "vim.Datacenter", "name": "dc1"}
        parents_dict[str(folder)] = {"type": "vim.Folder", "parent": str(datacenter)}

        props = [
            vim.DynamicProperty(name="name", val="cluster1"),
            vim.DynamicProperty(name="parent", val=folder),
        ]

        expected_facts = {"cluster.name": "cluster1", "cluster.datacenter": "dc1"}
        results = self.runner.parse_cluster_props(props, parents_dict)
        assert results == expected_facts

    def test_parse_host_props(self):
        """Test the parse_host_props_method."""
        facts = {
            "summary.hardware.numCpuCores": 12,
            "summary.config.name": "host1",
            "summary.hardware.numCpuPkgs": 2,
            "summary.hardware.numCpuThreads": 24,
        }

        cluster = vim.ClusterComputeResource("domain-c7")

        props = []
        prop_parent = Mock()
        prop_parent.name, prop_parent.val = "parent", cluster
        props.append(prop_parent)

        for key, value in facts.items():
            prop = Mock()
            prop.name, prop.val = key, value
            props.append(prop)

        cluster_dict = {}
        cluster_dict[str(cluster)] = {
            "cluster.name": "cluster1",
            "cluster.datacenter": "dc1",
        }

        expected_facts = {
            "host.cluster": "cluster1",
            "host.datacenter": "dc1",
            "host.name": "host1",
            "host.cpu_cores": 12,
            "host.cpu_count": 2,
            "host.cpu_threads": 24,
        }

        results = self.runner.parse_host_props(props, cluster_dict)
        assert results == expected_facts

    @patch("scanner.vcenter.inspect.datetime")
    def test_parse_vm_props(self, mock_dt):
        """Test the parse_vm_props method."""
        mock_dt.utcnow.return_value = datetime(2000, 1, 1, 4, 20)

        ip_addresses, mac_addresses = ["1.2.3.4"], ["00:50:56:9e:09:8c"]

        facts = {
            "name": "vm1",
            "guest.net": "",  # mac/ip addr returned by get_nics
            "summary.runtime.powerState": "poweredOn",
            "summary.guest.hostName": "hostname",
            "summary.config.guestFullName": "Red Hat 7",
            "summary.config.memorySizeMB": 1024,
            "summary.config.numCpu": 4,
            "summary.config.uuid": "1111",
            "runtime.host": "",
            "config.template": False,
        }  # runs through host_facts values
        host_facts = {
            "host.name": "host1",
            "host.cpu_cores": 12,
            "host.cpu_count": 2,
            "host.cpu_threads": 24,
            "host.cluster": "cluster1",
            "host.datacenter": "dc1",
        }

        host = vim.HostSystem("host-1")

        host_dict = {}
        host_dict[str(host)] = host_facts
        props = []

        for key, value in facts.items():
            prop = Mock()
            prop.name, prop.val = key, value
            if key == "runtime.host":
                prop.val = host
            props.append(prop)

        self.scan_task.update_stats(
            "TEST_VC.", sys_count=5, sys_failed=0, sys_scanned=0, sys_unreachable=0
        )

        with patch(
            "scanner.vcenter.inspect.get_nics",
            return_value=(mac_addresses, ip_addresses),
        ):
            self.runner.parse_vm_props(props, host_dict)
            sys_results = self.scan_task.get_result().all()
            expected_facts = {
                "vm.cluster": "cluster1",
                "vm.cpu_count": 4,
                "vm.datacenter": "dc1",
                "vm.dns_name": "hostname",
                "vm.host.cpu_cores": 12,
                "vm.host.cpu_count": 2,
                "vm.host.cpu_threads": 24,
                "vm.host.name": "host1",
                "vm.ip_addresses": ["1.2.3.4"],
                "vm.is_template": False,
                "vm.mac_addresses": ["00:50:56:9e:09:8c"],
                "vm.memory_size": 1,
                "vm.name": "vm1",
                "vm.os": "Red Hat 7",
                "vm.state": "poweredOn",
                "vm.last_check_in": "2000-01-01 04:20:00",
                "vm.uuid": "1111",
            }
            sys_fact = {}
            for raw_fact in sys_results.first().facts.all():
                sys_fact[raw_fact.name] = raw_fact.value

            assert 1 == len(sys_results)
            assert "vm1" == sys_results.first().name
            assert expected_facts == sys_fact

    def test_retrieve_properties(self):
        """Test the retrieve_properties method."""
        content = Mock()
        content.rootFolder = vim.Folder("group-d1")

        objects_first_page = [
            vim.ObjectContent(
                obj=vim.Folder("group-d1"),
            ),
            vim.ObjectContent(
                obj=vim.ClusterComputeResource("domain-c1"),
            ),
        ]

        objects_second_page = [
            vim.ObjectContent(
                obj=vim.HostSystem("host-1"),
            ),
            vim.ObjectContent(
                obj=vim.VirtualMachine("vm-1"),
            ),
        ]

        content.propertyCollector.RetrievePropertiesEx(ANY).token = "1"
        content.propertyCollector.RetrievePropertiesEx(ANY).objects = objects_first_page
        content.propertyCollector.ContinueRetrievePropertiesEx(ANY).token = None
        content.propertyCollector.ContinueRetrievePropertiesEx(ANY).objects = (
            objects_second_page
        )

        with (
            patch.object(
                InspectTaskRunner, "parse_parent_props"
            ) as mock_parse_parent_props,
            patch.object(
                InspectTaskRunner, "parse_cluster_props"
            ) as mock_parse_cluster_props,
            patch.object(
                InspectTaskRunner, "parse_host_props"
            ) as mock_parse_host_props,
            patch.object(InspectTaskRunner, "parse_vm_props") as mock_parse_vm_props,
        ):

            self.runner.retrieve_properties(content)
            mock_parse_parent_props.assert_called_with(ANY, ANY)
            mock_parse_cluster_props.assert_called_with(ANY, ANY)
            mock_parse_host_props.assert_called_with(ANY, ANY)
            mock_parse_vm_props.assert_called_with(ANY, ANY)

    def test_inspect(self):
        """Test the inspect method."""
        with patch(
            "scanner.vcenter.inspect.vcenter_connect", return_value=Mock()
        ) as mock_vcenter_connect:
            with patch.object(
                InspectTaskRunner, "retrieve_properties"
            ) as mock_retrieve_props:
                self.runner.connect_scan_task = self.connect_scan_task
                self.runner.inspect()
                mock_vcenter_connect.assert_called_once_with(ANY)
                mock_retrieve_props.assert_called_once_with(ANY)

    def test_failed_run(self):
        """Test the run method."""
        with patch.object(
            InspectTaskRunner, "inspect", side_effect=invalid_login
        ) as mock_connect:
            status = self.runner.run(Value("i", ScanJob.JOB_RUN))
            assert ScanTask.FAILED == status[1]
            mock_connect.assert_called_once_with()

    def test_prereq_failed(self):
        """Test the run method."""
        self.connect_scan_task.status = ScanTask.FAILED
        self.connect_scan_task.save()
        status = self.runner.run(Value("i", ScanJob.JOB_RUN))
        assert ScanTask.FAILED == status[1]

    def test_run(self):
        """Test the run method."""
        with patch.object(InspectTaskRunner, "inspect") as mock_connect:
            status = self.runner.run(Value("i", ScanJob.JOB_RUN))
            assert ScanTask.COMPLETED == status[1]
            mock_connect.assert_called_once_with()

    def test_cancel(self):
        """Test the cancel method."""
        status = self.runner.run(Value("i", ScanJob.JOB_TERMINATE_CANCEL))
        assert ScanTask.CANCELED == status[1]

    def test_pause(self):
        """Test the pause method."""
        status = self.runner.run(Value("i", ScanJob.JOB_TERMINATE_PAUSE))
        assert ScanTask.PAUSED == status[1]
