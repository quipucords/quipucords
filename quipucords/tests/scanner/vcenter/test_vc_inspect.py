"""Test the vcenter inspect capabilities."""

from datetime import UTC, datetime
from socket import gaierror
from unittest.mock import ANY, Mock, patch

import pytest
from faker import Faker
from pyVmomi import vim

from api.models import Credential, ScanTask, Source
from scanner.vcenter.inspect import InspectTaskRunner, get_nics, get_vm_names
from tests.scanner.test_util import create_scan_job

_faker = Faker()


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


def unreachable_host():
    """Mock with gaierror."""
    raise gaierror("Unreachable")


def test_get_vm_names():
    """Test the get_vm_names function."""
    objects = [
        vim.ObjectContent(
            obj=vim.VirtualMachine("vm-1"),
            propSet=[vim.DynamicProperty(name="name", val="vm1")],
        ),
        vim.ObjectContent(
            obj=vim.VirtualMachine("vm-2"),
            propSet=[vim.DynamicProperty(name="name", val="vm2")],
        ),
    ]

    content = Mock()
    content.rootFolder = vim.Folder("group-d1")
    content.propertyCollector.RetrievePropertiesEx(ANY).token = None
    content.propertyCollector.RetrievePropertiesEx(ANY).objects = objects

    vm_names = get_vm_names(content)
    assert isinstance(vm_names, list) is True
    assert vm_names == ["vm1", "vm2"]


def test_get_nics():
    """Test the get_nics function."""
    guest = Mock()
    nics = []
    expected_mac_addresses = [_faker.mac_address() for _ in range(2)]
    expected_ip_addresses = [_faker.ipv4(), _faker.ipv6()]
    for k in range(0, 2):
        nic = Mock()
        network = Mock()
        nic.network = network
        nic.macAddress = expected_mac_addresses[k]
        ip_config = Mock()
        ip_addr = Mock()
        ip_addr.ipAddress = expected_ip_addresses[k]
        addresses = [ip_addr]
        ip_config.ipAddress = addresses
        nic.ipConfig = ip_config
        nics.append(nic)
    guest.net = nics
    mac_addresses, ip_addresses = get_nics(guest.net)
    assert mac_addresses == expected_mac_addresses
    assert ip_addresses == expected_ip_addresses


@pytest.mark.django_db
class TestVCenterInspectTaskRunnerTest:
    """Tests against the InspectTaskRunner class and functions."""

    runner = None

    def setup_method(self, _test_method):
        """Create test case setup."""
        self.cred = Credential.objects.create(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )

        self.source = Source.objects.create(name="source1", port=22, hosts=["1.2.3.4"])
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(self.source)
        self.scan_task.update_stats("TEST_VC.", sys_count=5)

        # Create task runner
        self.runner = InspectTaskRunner(
            scan_job=self.scan_job, scan_task=self.scan_task
        )

    def test_invalid_login_fails_connection_check(self, mocker):
        """Test the run method with invalid login."""
        mock_connect = mocker.patch.object(
            InspectTaskRunner, "connect", side_effect=invalid_login
        )
        mock_inspect = mocker.patch.object(InspectTaskRunner, "inspect")

        status = self.runner.run()
        assert ScanTask.FAILED == status[1]
        mock_connect.assert_called_once_with()
        mock_inspect.assert_not_called()

    def test_unreachable_host_fails_connection_check(self, mocker):
        """Test the run method with unreachable host."""
        mock_connect = mocker.patch.object(
            InspectTaskRunner, "connect", side_effect=unreachable_host
        )
        mock_inspect = mocker.patch.object(InspectTaskRunner, "inspect")

        status = self.runner.run()
        assert ScanTask.FAILED == status[1]
        mock_connect.assert_called_once_with()
        mock_inspect.assert_not_called()

    def test_store_connect_data(self):
        """Test the connection data method."""
        vm_names = ["vm1", "vm2"]

        self.runner._store_connect_data(vm_names, self.cred, self.source)
        assert len(self.scan_job.connection_results.task_results.all()) == 1

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
        mock_dt.now.return_value = datetime(2000, 1, 1, 4, 20, tzinfo=UTC)

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
        content.propertyCollector.ContinueRetrievePropertiesEx(
            ANY
        ).objects = objects_second_page

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

    def test_inspect(self, mocker):
        """Test the inspect method."""
        mock_vcenter_connect = mocker.patch(
            "scanner.vcenter.inspect.vcenter_connect", return_value=Mock()
        )
        mocker.patch.object(
            InspectTaskRunner,
            "check_connection",
            side_effect=[None, ScanTask.COMPLETED],
        )
        mock_retrieve_props = mocker.patch.object(
            InspectTaskRunner, "retrieve_properties"
        )

        self.runner.inspect()
        mock_vcenter_connect.assert_called_once_with(ANY)
        mock_retrieve_props.assert_called_once_with(ANY)

    def test_run_happy_path(self, mocker):
        """Test the run method."""
        mocker.patch.object(
            InspectTaskRunner,
            "check_connection",
            return_value=[None, ScanTask.COMPLETED],
        )
        mock__inspect = mocker.patch.object(InspectTaskRunner, "_inspect")

        status = self.runner.run()
        assert ScanTask.COMPLETED == status[1]
        mock__inspect.assert_called_once_with()
