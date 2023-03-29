"""Test the fact engine API."""

from copy import deepcopy
from datetime import datetime
from unittest import mock
from unittest.mock import patch

from django.db import DataError
from django.test import TestCase

from api.deployments_report.model import SystemFingerprint
from api.models import DeploymentsReport, DetailsReport, ServerInformation, Source
from constants import DataSources
from fingerprinter.constants import ENTITLEMENTS_KEY, META_DATA_KEY, PRODUCTS_KEY
from fingerprinter.task import (
    FINGERPRINT_GLOBAL_ID_KEY,
    NETWORK_SATELLITE_MERGE_KEYS,
    NETWORK_VCENTER_MERGE_KEYS,
    FingerprintTaskRunner,
)
from scanner.network.utils import raw_facts_template as network_template
from scanner.satellite.utils import raw_facts_template as satellite_template
from scanner.test_util import create_scan_job
from scanner.vcenter.utils import raw_facts_template as vcenter_template

SUBMAN_CONSUMED = [{"name": "Red Hat JBoss Fuse", "entitlement_id": "ESA0009"}]
SAT_ENTITLEMENTS = [{"name": "Satellite Tools 6.3"}]

EXPECTED_FINGERPRINT_MAP_NETWORK = {
    "architecture": "uname_processor",
    "bios_uuid": "dmi_system_uuid",
    "cloud_provider": "cloud_provider",
    "cpu_core_count": "cpu_core_count",
    "cpu_core_per_socket": "cpu_core_per_socket",
    "cpu_count": "cpu_count",
    "cpu_hyperthreading": "cpu_hyperthreading",
    "cpu_socket_count": "cpu_socket_count",
    "date_anaconda_log": "date_anaconda_log",
    "date_filesystem_create": "date_filesystem_create",
    "date_machine_id": "date_machine_id",
    "date_yum_history": "date_yum_history",
    "etc_machine_id": "etc_machine_id",
    "infrastructure_type": "virt_what_type/virt_type",
    "insights_client_id": "insights_client_id",
    "ip_addresses": "ifconfig_ip_addresses",
    "is_redhat": "redhat_packages_gpg_is_redhat",
    "mac_addresses": "ifconfig_mac_addresses",
    "name": "uname_hostname",
    "os_name": "etc_release_name",
    "os_release": "etc_release_release",
    "os_version": "etc_release_version",
    "redhat_certs": "redhat_packages_certs",
    "redhat_package_count": "redhat_packages_gpg_num_rh_packages",
    "subscription_manager_id": "subscription_manager_id",
    "system_addons": "system_purpose_json__addons",
    "system_last_checkin_date": "connection_timestamp",
    "system_memory_bytes": "system_memory_bytes",
    "system_purpose": "system_purpose_json",
    "system_role": "system_purpose_json__role",
    "system_service_level_agreement": "system_purpose_json__service_level_agreement",
    "system_usage_type": "system_purpose_json__usage",
    "system_user_count": "system_user_count",
    "user_login_history": "user_login_history",
    "virtualized_type": "virt_type",
}
EXPECTED_FINGERPRINT_MAP_SATELLITE = {
    "architecture": "architecture",
    "cpu_core_count": "cores",
    "cpu_count": "cores",
    "cpu_socket_count": "num_sockets",
    "infrastructure_type": "is_virtualized",
    "ip_addresses": "ip_addresses",
    "is_redhat": "os_release",
    "mac_addresses": "mac_addresses",
    "name": "hostname",
    "os_name": "os_name",
    "os_release": "os_release",
    "os_version": "os_version",
    "registration_time": "registration_time",
    "subscription_manager_id": "uuid",
    "system_last_checkin_date": "last_checkin_time",
    "virtual_host_name": "virtual_host_name",
    "virtual_host_uuid": "virtual_host_uuid",
    "virtualized_type": "virt_type",
}
EXPECTED_FINGERPRINT_MAP_VCENTER = {
    "architecture": "uname_processor",
    "cpu_count": "vm.cpu_count",
    "infrastructure_type": "vcenter_source",
    "ip_addresses": "vm.ip_addresses",
    "is_redhat": "vm.os",
    "mac_addresses": "vm.mac_addresses",
    "name": "vm.name",
    "os_release": "vm.os",
    "system_last_checkin_date": "vm.last_check_in",
    "system_memory_bytes": "vm.memory_size",
    "virtual_host_name": "vm.host.name",
    "virtual_host_uuid": "vm.host.uuid",
    "vm_cluster": "vm.cluster",
    "vm_datacenter": "vm.datacenter",
    "vm_dns_name": "vm.dns_name",
    "vm_host_core_count": "vm.host.cpu_cores",
    "vm_host_socket_count": "vm.host.cpu_count",
    "vm_state": "vm.state",
    "vm_uuid": "vm.uuid",
}

PRODUCTS = [
    {"name": "JBoss EAP", "presence": "absent"},
    {"name": "JBoss Fuse", "presence": "absent"},
    {"name": "JBoss BRMS", "presence": "absent"},
    {"name": "JBoss Web Server", "presence": "absent", "version": []},
]


class EngineTest(TestCase):
    """Tests Engine class."""

    def setUp(self):
        """Create test case setup."""
        self.server_id = ServerInformation.create_or_retrieve_server_id()
        self.source = Source(
            name="source1",
            hosts=["1.2.3.4"],
            source_type="network",
            port=22,
        )
        self.source.save()
        scan_job, _ = create_scan_job(self.source)
        self.fp_task = scan_job.tasks.last()  # pylint: disable=no-member
        self.fp_task_runner = FingerprintTaskRunner(scan_job, self.fp_task)

    # pylint: disable=too-many-arguments,too-many-lines
    # pylint: disable=too-many-locals,too-many-branches,invalid-name
    # pylint: disable=protected-access, W0102

    ################################################################
    # Helper functions
    ################################################################
    def _create_network_fc_json(
        self,
        report_id=1,
        source_name="source1",
        source_type=DataSources.NETWORK,
        cpu_count=1,
        etc_release_name="RHEL",
        etc_release_version="7.4 (Maipo)",
        etc_release_release="RHEL 7.4 (Maipo)",
        ifconfig_ip_addresses=None,
        ifconfig_mac_addresses=None,
        dmi_system_uuid=1234,
        subman_virt_uuid=4567,
        subman_consumed=SUBMAN_CONSUMED,
        subscription_manager_id=42,
        connection_uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
        connection_host="1.2.3.4",
        connection_port=22,
        cpu_socket_count=2,
        cpu_core_count=2,
        date_yum_history="2017-07-18",
        date_filesystem_create="2017-06-17",
        date_anaconda_log="2017-05-17",
        date_machine_id="2017-04-17",
        system_purpose_json=None,
        virt_virt="virt-guest",
        virt_type="vmware",
        virt_num_guests=1,
        virt_num_running_guests=1,
        virt_what_type="vt",
        is_redhat=True,
        redhat_certs="fake certs",
        redhat_package_count=100,
        architecture="x86_64",
        user_has_sudo=True,
    ):
        """Create an in memory DetailsReport for tests."""
        # pylint: disable=too-many-statements
        fact = network_template()
        if source_name:
            fact["source_name"] = source_name
        if source_type:
            fact["source_type"] = source_type
        if cpu_count:
            fact["cpu_count"] = cpu_count
        if etc_release_name:
            fact["etc_release_name"] = etc_release_name
        if etc_release_version:
            fact["etc_release_version"] = etc_release_version
        if etc_release_release:
            fact["etc_release_release"] = etc_release_release

        if ifconfig_ip_addresses:
            fact["ifconfig_ip_addresses"] = ifconfig_ip_addresses
        else:
            fact["ifconfig_ip_addresses"] = ["1.2.3.4", "2.3.4.5"]

        if ifconfig_mac_addresses:
            fact["ifconfig_mac_addresses"] = list(
                map(lambda x: x.lower(), ifconfig_mac_addresses)
            )
        else:
            fact["ifconfig_mac_addresses"] = ["mac1", "mac2"]

        if dmi_system_uuid:
            fact["dmi_system_uuid"] = dmi_system_uuid
        if subman_virt_uuid:
            fact["subman_virt_uuid"] = subman_virt_uuid
        if subman_consumed:
            fact["subman_consumed"] = subman_consumed
        fact["subscription_manager_id"] = subscription_manager_id
        if connection_uuid:
            fact["connection_uuid"] = connection_uuid
        if connection_host:
            fact["connection_host"] = connection_host
            fact["uname_hostname"] = connection_host
        if connection_port:
            fact["connection_port"] = connection_port
        if cpu_socket_count:
            fact["cpu_socket_count"] = cpu_socket_count
        if cpu_core_count:
            fact["cpu_core_count"] = cpu_core_count
        if date_anaconda_log:
            fact["date_anaconda_log"] = date_anaconda_log
        if date_yum_history:
            fact["date_yum_history"] = date_yum_history
        if date_filesystem_create:
            fact["date_filesystem_create"] = date_filesystem_create
        if date_machine_id:
            fact["date_machine_id"] = date_machine_id
        if system_purpose_json:
            fact["system_purpose_json"] = system_purpose_json
        if virt_virt:
            fact["virt_virt"] = virt_virt
        if virt_type:
            fact["virt_type"] = virt_type
        if virt_num_guests:
            fact["virt_num_guests"] = virt_num_guests
        if virt_num_running_guests:
            fact["virt_num_running_guests"] = virt_num_running_guests
        if virt_what_type:
            fact["virt_what_type"] = virt_what_type
        if is_redhat:
            fact["redhat_packages_gpg_is_redhat"] = is_redhat
        if redhat_certs:
            fact["redhat_packages_certs"] = redhat_certs
        if redhat_package_count:
            fact["redhat_packages_gpg_num_rh_packages"] = redhat_package_count
        if architecture:
            fact["uname_processor"] = architecture

        fact["user_has_sudo"] = user_has_sudo

        details_report = {"id": report_id, "facts": [fact]}
        return details_report

    def _create_vcenter_fc_json(
        self,
        report_id=1,
        source_name="source2",
        source_type=DataSources.VCENTER,
        vm_cpu_count=2,
        vm_os="RHEL 7.3",
        vm_mac_addresses=None,
        vm_ip_addresses=None,
        vm_name="TestMachine",
        vm_state="On",
        vm_uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
        vm_dns_name="site.com",
        vm_host_name="1.2.3.4",
        vm_host_cpu_count=8,
        vm_host_core_count=8,
        vm_datacenter="NY",
        vm_cluster="23sd",
        architecture="x86_64",
        is_redhat=True,
    ):
        """Create an in memory DetailsReport for tests."""
        fact = vcenter_template()
        if source_name:
            fact["source_name"] = source_name
        if source_type:
            fact["source_type"] = source_type
        if vm_cpu_count:
            fact["vm.cpu_count"] = vm_cpu_count
        if vm_os:
            fact["vm.os"] = vm_os

        if vm_ip_addresses:
            fact["vm.ip_addresses"] = vm_ip_addresses
        else:
            fact["vm.ip_addresses"] = ["1.2.3.4", "2.3.4.5"]

        if vm_mac_addresses:
            fact["vm.mac_addresses"] = list(map(lambda x: x.lower(), vm_mac_addresses))
        else:
            fact["vm.mac_addresses"] = ["mac1", "mac2"]

        if vm_name:
            fact["vm.name"] = vm_name
        if vm_state:
            fact["vm.state"] = vm_state
        if vm_uuid:
            fact["vm.uuid"] = vm_uuid
        if vm_dns_name:
            fact["vm.dns_name"] = vm_dns_name
        if vm_host_name:
            fact["vm.host.name"] = vm_host_name
        if vm_host_cpu_count:
            fact["vm.host.cpu_count"] = vm_host_cpu_count
        if vm_host_core_count:
            fact["vm.host.cpu_cores"] = vm_host_core_count
        if vm_datacenter:
            fact["vm.datacenter"] = vm_datacenter
        if vm_cluster:
            fact["vm.cluster"] = vm_cluster
        if architecture:
            fact["uname_processor"] = architecture
        if "red hat enterprise linux" in vm_os.lower() or "rhel" in vm_os.lower():
            fact["is_redhat"] = is_redhat
        details_report = {"id": report_id, "facts": [fact]}
        return details_report

    def _create_satellite_fc_json(
        self,
        report_id=1,
        source_name="source3",
        source_type=DataSources.SATELLITE,
        hostname="9.8.7.6",
        os_name="RHEL",
        os_release="RHEL 7.3",
        os_version=7.3,
        mac_addresses=None,
        ip_addresses=None,
        cores=32,
        registration_time="2017-03-18",
        uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
        virt_type="lxc",
        is_virtualized=True,
        virtual_host="9.3.4.6",
        num_sockets=8,
        entitlements=SAT_ENTITLEMENTS,
        architecture="x86_64",
        is_redhat=True,
    ):
        """Create an in memory DetailsReport for tests."""
        fact = satellite_template()
        if source_name:
            fact["source_name"] = source_name
        if source_type:
            fact["source_type"] = source_type
        if hostname:
            fact["hostname"] = hostname
        if os_name:
            fact["os_name"] = os_name
        if os_release:
            fact["os_release"] = os_release
        if os_version:
            fact["os_version"] = os_version

        if ip_addresses:
            fact["ip_addresses"] = ip_addresses
        else:
            fact["ip_addresses"] = ["1.2.3.4", "2.3.4.5"]

        if mac_addresses:
            fact["mac_addresses"] = list(map(lambda x: x.lower(), mac_addresses))
        else:
            fact["mac_addresses"] = ["mac1", "mac2"]

        if registration_time:
            fact["registration_time"] = registration_time

        if cores:
            fact["cores"] = cores
        if uuid:
            fact["uuid"] = uuid
        if virt_type:
            fact["virt_type"] = virt_type
        if is_virtualized:
            fact["is_virtualized"] = is_virtualized
        if virtual_host:
            fact["virtual_host"] = virtual_host
        if num_sockets:
            fact["num_sockets"] = num_sockets
        if entitlements:
            fact["entitlements"] = entitlements
        if architecture:
            fact["architecture"] = architecture
        if "red hat enterprise linux" in os_name.lower() or "rhel" in os_name.lower():
            fact["is_redhat"] = is_redhat

        details_report = {"id": report_id, "facts": [fact]}
        return details_report

    def _validate_network_result(self, fingerprint, fact):
        """Help to validate fields."""
        self.assertEqual(fact.get("connection_host"), fingerprint.get("name"))

        self.assertEqual(fact.get("etc_release_name"), fingerprint.get("os_name"))
        self.assertEqual(fact.get("etc_release_release"), fingerprint.get("os_release"))
        self.assertEqual(fact.get("etc_release_version"), fingerprint.get("os_version"))

        self.assertListEqual(
            fact.get("ifconfig_ip_addresses"), fingerprint.get("ip_addresses")
        )
        self.assertListEqual(
            fact.get("ifconfig_mac_addresses"), fingerprint.get("mac_addresses")
        )

        self.assertEqual(fact.get("cpu_count"), fingerprint.get("cpu_count"))

        self.assertEqual(fact.get("dmi_system_uuid"), fingerprint.get("bios_uuid"))
        self.assertEqual(
            fact.get("subscription_manager_id"),
            fingerprint.get("subscription_manager_id"),
        )

        self.assertEqual(
            fact.get("cpu_socket_count"), fingerprint.get("cpu_socket_count")
        )
        self.assertEqual(fact.get("cpu_core_count"), fingerprint.get("cpu_core_count"))

        self.assertEqual(
            fact.get("date_anaconda_log"), fingerprint.get("date_anaconda_log")
        )
        self.assertEqual(
            fact.get("date_yum_history"), fingerprint.get("date_yum_history")
        )
        self.assertEqual(
            fact.get("date_machine_id"), fingerprint.get("date_machine_id")
        )
        self.assertEqual(
            fact.get("date_filesystem_create"),
            fingerprint.get("date_filesystem_create"),
        )
        self.assertEqual("virtualized", fingerprint.get("infrastructure_type"))

        self.assertEqual(fact.get("virt_type"), fingerprint.get("virtualized_type"))
        self.assertEqual(fact.get("uname_processor"), fingerprint.get("architecture"))
        self.assertEqual(
            fact.get("redhat_packages_certs"), fingerprint.get("redhat_certs")
        )
        self.assertEqual(
            fact.get("redhat_packages_gpg_is_redhat"), fingerprint.get("is_redhat")
        )
        self.assertEqual(
            fact.get("redhat_packages_gpg_num_rh_packages"),
            fingerprint.get("redhat_package_count"),
        )
        system_purpose_json = fact.get("system_purpose_json", None)
        if system_purpose_json:
            self.assertEqual(system_purpose_json, fingerprint.get("system_purpose"))
            self.assertEqual(
                system_purpose_json.get("role", None), fingerprint.get("system_role")
            )
            self.assertEqual(
                system_purpose_json.get("addons", None),
                fingerprint.get("system_addons"),
            )
            self.assertEqual(
                system_purpose_json.get("service_level_agreement", None),
                fingerprint.get("system_service_level_agreement"),
            )
            self.assertEqual(
                system_purpose_json.get("usage", None),
                fingerprint.get("system_usage_type"),
            )
        else:
            self.assertIsNone(fingerprint.get("system_role"))
            self.assertIsNone(fingerprint.get("system_addons"))
            self.assertIsNone(fingerprint.get("system_service_level_agreement"))
            self.assertIsNone(fingerprint.get("system_usage_type"))

    def _validate_vcenter_result(self, fingerprint, fact):
        """Help to validate fields."""
        if fact.get("vm.dns_name"):
            self.assertEqual(fact.get("vm.dns_name"), fingerprint.get("name"))
        else:
            self.assertEqual(fact.get("vm.name"), fingerprint.get("name"))

        self.assertEqual(fact.get("vm.os"), fingerprint.get("os_release"))

        self.assertEqual(fact.get("vm.ip_addresses"), fingerprint.get("ip_addresses"))
        self.assertEqual(fact.get("vm.mac_addresses"), fingerprint.get("mac_addresses"))
        self.assertEqual(fact.get("vm.cpu_count"), fingerprint.get("cpu_count"))

        self.assertEqual(fact.get("vm.state"), fingerprint.get("vm_state"))

        self.assertEqual(fact.get("vm.uuid"), fingerprint.get("vm_uuid"))

        self.assertEqual(fact.get("vm.dns_name"), fingerprint.get("vm_dns_name"))
        self.assertEqual(fact.get("vm.host.name"), fingerprint.get("virtual_host_name"))

        self.assertEqual(
            fact.get("vm.host.cpu_count"), fingerprint.get("vm_host_socket_count")
        )
        self.assertEqual(
            fact.get("vm.host.cpu_cores"), fingerprint.get("vm_host_core_count")
        )
        self.assertEqual(fact.get("vm.datacenter"), fingerprint.get("vm_datacenter"))
        self.assertEqual(fact.get("vm.cluster"), fingerprint.get("vm_cluster"))
        self.assertEqual(fact.get("uname_processor"), fingerprint.get("architecture"))
        self.assertEqual(fact.get("is_redhat"), fingerprint.get("is_redhat"))

    def _validate_satellite_result(self, fingerprint, fact):
        """Help to validate fields."""
        self.assertEqual(fact.get("hostname"), fingerprint.get("name"))

        self.assertEqual(fact.get("os_name"), fingerprint.get("os_name"))
        self.assertEqual(fact.get("os_release"), fingerprint.get("os_release"))
        self.assertEqual(fact.get("os_version"), fingerprint.get("os_version"))

        self.assertEqual(fact.get("cores"), fingerprint.get("cpu_count"))
        self.assertEqual(fact.get("ip_addresses"), fingerprint.get("ip_addresses"))
        self.assertEqual(fact.get("mac_addresses"), fingerprint.get("mac_addresses"))
        self.assertEqual(
            fact.get("registration_time"), fingerprint.get("registration_time")
        )
        self.assertEqual(fact.get("uuid"), fingerprint.get("subscription_manager_id"))
        if fact.get("hostname", "").endswith(
            tuple("-" + str(num) for num in range(1, 10))
        ) and fact.get("hostname").startswith("virt-who-"):
            self.assertEqual("hypervisor", fingerprint.get("infrastructure_type"))
        else:
            self.assertEqual("virtualized", fingerprint.get("infrastructure_type"))

        self.assertEqual(fact.get("cores"), fingerprint.get("cpu_core_count"))
        self.assertEqual(fact.get("num_sockets"), fingerprint.get("cpu_socket_count"))
        self.assertEqual(fact.get("architecture"), fingerprint.get("architecture"))
        self.assertEqual(fact.get("is_redhat"), fingerprint.get("is_redhat"))

    def _create_network_fingerprint(self, *args, **kwargs):
        """Create test network fingerprint."""
        n_details_report = self._create_network_fc_json(*args, **kwargs)
        nfact = n_details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
            "facts": n_details_report["facts"],
        }
        nfingerprints = self.fp_task_runner._process_source(source)
        nfingerprint = nfingerprints[0]
        self._validate_network_result(nfingerprint, nfact)

        return nfingerprint

    def _create_vcenter_fingerprint(self, *args, **kwargs):
        """Create test network/vcenter fingerprints."""
        v_details_report = self._create_vcenter_fc_json(*args, **kwargs)
        vfact = v_details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source2",
            "source_type": DataSources.VCENTER,
            "facts": v_details_report["facts"],
        }
        vfingerprints = self.fp_task_runner._process_source(source)
        vfingerprint = vfingerprints[0]
        self._validate_vcenter_result(vfingerprint, vfact)
        return vfingerprint

    def _create_satellite_fingerprint(self, *args, **kwargs):
        """Create test network/vcenter fingerprints."""
        s_details_report = self._create_satellite_fc_json(*args, **kwargs)
        vfact = s_details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source3",
            "source_type": DataSources.SATELLITE,
            "facts": s_details_report["facts"],
        }
        sfingerprints = self.fp_task_runner._process_source(source)
        sfingerprint = sfingerprints[0]
        self._validate_satellite_result(sfingerprint, vfact)
        return sfingerprint

    ################################################################
    # Test Source functions
    ################################################################
    def test_process_network_source(self):
        """Test process network source."""
        # Note the create method runs a validate
        system_purpose_json = None
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json = {}
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["_version"] = 1
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["_version"] = 1
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["role"] = "server"
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["service_level_agreement"] = "self-service"
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["usage"] = "dev"
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["addons"] = ["ibm"]
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

        system_purpose_json["random_extra_field"] = ["redhat"]
        self._create_network_fingerprint(system_purpose_json=system_purpose_json)

    def test_process_network_system_purpose(self):
        """Test process network system_purpose."""
        system_purpose_json = {
            "_version": "1",
            "role": "server",
            "service_level_agreement": "self-support",
            "usage": "test",
            "addons": ["a", "b", "c"],
        }

        details_report = self._create_network_fc_json(
            system_purpose_json=system_purpose_json
        )
        fact = details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
            "facts": details_report["facts"],
        }
        fingerprints = self.fp_task_runner._process_source(source)
        fingerprint = fingerprints[0]
        self._validate_network_result(fingerprint, fact)

    def test_process_vcenter_source_with_dns(self):
        """Test process vcenter source that has a dns name."""
        details_report = self._create_vcenter_fc_json()
        fact = details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.VCENTER,
            "facts": details_report["facts"],
        }
        fingerprints = self.fp_task_runner._process_source(source)
        fingerprint = fingerprints[0]
        self._validate_vcenter_result(fingerprint, fact)

    def test_process_vcenter_source_no_dns_name(self):
        """Test process vcenter source with no dns name."""
        details_report = self._create_vcenter_fc_json(
            report_id=1,
            source_name="source2",
            source_type=DataSources.VCENTER,
            vm_cpu_count=2,
            vm_os="RHEL 7.3",
            vm_mac_addresses=None,
            vm_ip_addresses=None,
            vm_name="TestMachine",
            vm_state="On",
            vm_uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
            vm_dns_name=None,
        )
        fact = details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.VCENTER,
            "facts": details_report["facts"],
        }
        fingerprints = self.fp_task_runner._process_source(source)
        fingerprint = fingerprints[0]
        self._validate_vcenter_result(fingerprint, fact)

    def test_process_satellite_source(self):
        """Test process satellite source."""
        details_report = self._create_satellite_fc_json()
        fact = details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.SATELLITE,
            "facts": details_report["facts"],
        }
        fingerprints = self.fp_task_runner._process_source(source)
        fingerprint = fingerprints[0]
        self._validate_satellite_result(fingerprint, fact)

    def test_process_satellite_source_hypervisor(self):
        """Test processing sat source for hypervisor infrastructure."""
        details_report = self._create_satellite_fc_json(
            report_id=1,
            source_name="source3",
            source_type=DataSources.SATELLITE,
            hostname="virt-who-9384389442-5",
        )
        fact = details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.SATELLITE,
            "facts": details_report["facts"],
        }
        fingerprints = self.fp_task_runner._process_source(source)
        fingerprint = fingerprints[0]
        self._validate_satellite_result(fingerprint, fact)

    def test_process_satellite_source_not_hypervisor(self):
        """Test processing sat source for virtualized infrastructure."""
        details_report = self._create_satellite_fc_json(
            report_id=1,
            source_name="source3",
            source_type=DataSources.SATELLITE,
            hostname="virt-who-9384389442-0",
        )
        fact = details_report["facts"][0]
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": DataSources.SATELLITE,
            "facts": details_report["facts"],
        }
        fingerprints = self.fp_task_runner._process_source(source)
        fingerprint = fingerprints[0]
        self._validate_satellite_result(fingerprint, fact)

    ################################################################
    # Test merge functions
    ################################################################
    def test_merge_network_and_vcenter(self):
        """Test merge of two lists of fingerprints."""
        nfingerprints = [
            self._create_network_fingerprint(
                dmi_system_uuid="match", ifconfig_mac_addresses=["1"]
            ),
            self._create_network_fingerprint(
                dmi_system_uuid=1, ifconfig_mac_addresses=["2"]
            ),
        ]
        vfingerprints = [
            self._create_vcenter_fingerprint(vm_uuid="match"),
            self._create_vcenter_fingerprint(vm_uuid=2),
        ]

        n_cpu_count = nfingerprints[0]["cpu_count"]
        v_cpu_count = vfingerprints[0]["cpu_count"]
        v_name = vfingerprints[0]["name"]
        self.assertNotEqual(n_cpu_count, v_cpu_count)

        reverse_priority_keys = {"cpu_count"}
        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_VCENTER_MERGE_KEYS,
            nfingerprints,
            vfingerprints,
            reverse_priority_keys=reverse_priority_keys,
        )
        self.assertEqual(len(result_fingerprints), 3)

        for result_fingerprint in result_fingerprints:
            if result_fingerprint.get("vm_uuid") == "match":
                self.assertEqual(result_fingerprint.get("cpu_count"), v_cpu_count)
                self.assertNotEqual(result_fingerprint.get("cpu_count"), n_cpu_count)
                self.assertNotEqual(result_fingerprint.get("name"), v_name)

    def test_merge_network_and_vcenter_infrastructure_type(self):
        """Test if VCenter infrastructure_type is prefered over network."""
        nfingerprints = [
            self._create_network_fingerprint(
                dmi_system_uuid="match", ifconfig_mac_addresses=["1"]
            )
        ]
        vfingerprints = [self._create_vcenter_fingerprint(vm_uuid="match")]
        # change infrastructure_type to bypass the validation
        nfingerprints[0]["infrastructure_type"] = "unknown"
        vfingerprints[0]["infrastructure_type"] = "virtualized"
        self.assertNotEqual(
            nfingerprints[0]["infrastructure_type"],
            vfingerprints[0]["infrastructure_type"],
        )

        reverse_priority_keys = {"cpu_count", "infrastructure_type"}
        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_VCENTER_MERGE_KEYS,
            nfingerprints,
            vfingerprints,
            reverse_priority_keys=reverse_priority_keys,
        )
        for result_fingerprint in result_fingerprints:
            if result_fingerprint.get("vm_uuid") == "match":
                self.assertEqual(
                    result_fingerprint.get("infrastructure_type"), "virtualized"
                )

    def test_merge_mac_address_case_insensitive(self):
        """Test if fingerprints will be merged with mixed mac addr."""
        n_mac = ["00:50:56:A3:A2:E8", "00:50:56:c3:d2:m8"]
        v_mac = ["00:50:56:a3:a2:e8", "00:50:56:C3:D2:m8"]
        s_mac = ["00:50:56:A3:a2:E8", "00:50:56:C3:D2:M8"]
        self.assertNotEqual(v_mac, n_mac)
        self.assertNotEqual(v_mac, s_mac)
        nfingerprints = [self._create_network_fingerprint(ifconfig_mac_addresses=n_mac)]
        vfingerprints = [self._create_vcenter_fingerprint(vm_mac_addresses=v_mac)]
        sfingerprints = [self._create_satellite_fingerprint(mac_addresses=s_mac)]
        v_mac_addresses = vfingerprints[0]["mac_addresses"]
        n_mac_addresses = nfingerprints[0]["mac_addresses"]
        s_mac_addresses = sfingerprints[0]["mac_addresses"]
        self.assertEqual(v_mac_addresses, n_mac_addresses)
        self.assertEqual(v_mac_addresses, s_mac_addresses)
        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_SATELLITE_MERGE_KEYS, nfingerprints, sfingerprints
        )
        self.assertEqual(len(result_fingerprints), 1)
        reverse_priority_keys = {"cpu_count", "infrastructure_type"}
        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_VCENTER_MERGE_KEYS,
            nfingerprints,
            vfingerprints,
            reverse_priority_keys=reverse_priority_keys,
        )
        self.assertEqual(len(result_fingerprints), 1)

    def test_merge_net_sate_vcenter_infrastructure_type(self):
        """Test if VCenter infrastructure_type is prefered over the others."""
        nfingerprints = [
            self._create_network_fingerprint(
                dmi_system_uuid="match", ifconfig_mac_addresses=["1"]
            )
        ]
        vfingerprints = [self._create_vcenter_fingerprint(vm_uuid="match")]
        sfingerprints = [self._create_satellite_fingerprint(uuid="match")]
        # change infrastructure_type to bypass the validation
        nfingerprints[0]["infrastructure_type"] = "unknown"
        sfingerprints[0]["infrastructure_type"] = "test"
        vfingerprints[0]["infrastructure_type"] = "virtualized"
        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_SATELLITE_MERGE_KEYS, nfingerprints, sfingerprints
        )
        for result_fingerprint in result_fingerprints:
            if result_fingerprint.get("vm_uuid") == "match":
                self.assertEqual(result_fingerprint.get("infrastructure_type"), "test")
        reverse_priority_keys = {"cpu_count", "infrastructure_type"}
        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_VCENTER_MERGE_KEYS,
            nfingerprints,
            vfingerprints,
            reverse_priority_keys=reverse_priority_keys,
        )
        for result_fingerprint in result_fingerprints:
            if result_fingerprint.get("vm_uuid") == "match":
                self.assertEqual(
                    result_fingerprint.get("infrastructure_type"), "virtualized"
                )

    def test_merge_matching_fingerprints(self):
        """Test merge of two lists of fingerprints."""
        nmetadata = {
            "os_release": {
                "source_name": "source1",
                "source_type": DataSources.NETWORK,
                "raw_fact_key": "etc_release_release",
            },
            "bios_uuid": {
                "source_name": "source1",
                "source_type": DataSources.NETWORK,
                "raw_fact_key": "dmi_system_uuid",
            },
        }
        nsources = {
            "source1": {
                "source_name": "source1",
                "source_type": DataSources.NETWORK,
            }
        }
        nfingerprint_to_merge = {
            "id": 1,
            "os_release": "RHEL 7",
            "bios_uuid": "match",
            "metadata": nmetadata,
            "sources": nsources,
        }
        nfingerprint_no_match = {
            "id": 2,
            "os_release": "RHEL 7",
            "bios_uuid": "2345",
            "metadata": nmetadata,
            "sources": nsources,
        }
        nfingerprint_no_key = {
            "id": 3,
            "os_release": "RHEL 6",
            "metadata": nmetadata,
            "sources": nsources,
        }
        nfingerprints = [
            nfingerprint_to_merge,
            nfingerprint_no_match,
            nfingerprint_no_key,
        ]

        vmetadata = {
            "os_release": {
                "source_name": "source1",
                "source_type": DataSources.NETWORK,
                "raw_fact_key": "etc_release_release",
            },
            "vm_uuid": {
                "source_name": "source1",
                "source_type": DataSources.NETWORK,
                "raw_fact_key": "vm.uuid",
            },
        }
        vsources = {
            "source1": {
                "source_name": "source1",
                "source_type": DataSources.VCENTER,
            }
        }
        vfingerprint_to_merge = {
            "id": 5,
            "os_release": "Windows 7",
            "vm_uuid": "match",
            "metadata": vmetadata,
            "sources": vsources,
        }
        vfingerprint_no_match = {
            "id": 6,
            "os_release": "RHEL 7",
            "vm_uuid": "9876",
            "metadata": vmetadata,
            "sources": vsources,
        }
        vfingerprint_no_key = {
            "id": 7,
            "os_release": "RHEL 6",
            "metadata": vmetadata,
            "sources": vsources,
        }
        vfingerprints = [
            vfingerprint_to_merge,
            vfingerprint_no_match,
            vfingerprint_no_key,
        ]

        expected_merge_fingerprint = deepcopy(nfingerprint_to_merge)
        expected_merge_fingerprint["vm_uuid"] = "match"
        expected_merge_fingerprint["metadata"]["vm_uuid"] = vmetadata["vm_uuid"]

        (
            _,
            merge_list,
            no_match_found_list,
        ) = self.fp_task_runner._merge_matching_fingerprints(
            "bios_uuid", nfingerprints, "vm_uuid", vfingerprints
        )
        merged_sources = {
            "source1": {
                "source_name": "source1",
                "source_type": DataSources.NETWORK,
            }
        }

        # merge list should always contain all nfingerprints (base_list)
        self.assertEqual(len(merge_list), 3)
        self.assertTrue(expected_merge_fingerprint in merge_list)
        self.assertTrue(nfingerprint_no_match in merge_list)
        self.assertTrue(nfingerprint_no_key in merge_list)

        # assert VM property merged
        self.assertIsNotNone(expected_merge_fingerprint.get("vm_uuid"))

        # assert network os_release had priority
        self.assertEqual(expected_merge_fingerprint.get("os_release"), "RHEL 7")
        self.assertEqual(expected_merge_fingerprint.get("sources"), merged_sources)

        # assert those that didn't match, don't have VM properties
        self.assertIsNone(nfingerprint_no_match.get("vm_uuid"))
        self.assertIsNone(nfingerprint_no_key.get("vm_uuid"))

        # no_match_found list should only contain vfingerprints
        #  with no match
        self.assertEqual(len(no_match_found_list), 2)
        self.assertTrue(vfingerprint_no_match in no_match_found_list)
        self.assertTrue(vfingerprint_no_key in no_match_found_list)

    def test_remove_duplicate_fingerprints(self):
        """Test remove duplicate fingerprints created by index."""
        fingerprints = [
            {
                "id": 1,
                "os_release": "RHEL 7",
                "mac_addresses": ["1234", "2345"],
                "sources": [],
            },
            {
                "id": 2,
                "os_release": "RHEL 7",
                "mac_addresses": ["9876", "8765"],
                "sources": [],
            },
            {"id": 3, "os_release": "RHEL 6", "sources": []},
        ]
        index, no_key_found = self.fp_task_runner._create_index_for_fingerprints(
            "mac_addresses", fingerprints
        )

        self.assertEqual(len(no_key_found), 1)
        self.assertEqual(no_key_found[0]["id"], 3)
        self.assertIsNotNone(no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY))
        self.assertEqual(len(index.keys()), 4)
        self.assertIsNotNone(index.get("1234"))
        self.assertIsNotNone(index.get("2345"))
        self.assertIsNotNone(index.get("9876"))
        self.assertIsNotNone(index.get("8765"))

        # deplicate but leave unique key
        leave_key_list = list(index.values())
        unique_list = self.fp_task_runner._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], leave_key_list
        )
        self.assertEqual(len(unique_list), 2)
        self.assertIsNotNone(unique_list[0].get(FINGERPRINT_GLOBAL_ID_KEY))

        # same test, but add value that doesn't have key
        leave_key_list = list(index.values())
        leave_key_list.append({"id": 3, "os_release": "RHEL 6"})
        unique_list = self.fp_task_runner._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], leave_key_list
        )
        self.assertEqual(len(unique_list), 3)

        # now pass flag to strip id key
        remove_key_list = list(index.values())
        unique_list = self.fp_task_runner._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], remove_key_list, True
        )
        self.assertEqual(len(unique_list), 2)
        self.assertIsNone(unique_list[0].get(FINGERPRINT_GLOBAL_ID_KEY))

    def test_create_index_for_fingerprints(self):
        """Test create index for fingerprints."""
        fingerprints = [
            {"id": 1, "os_release": "RHEL 7", "bios_uuid": "1234"},
            {"id": 2, "os_release": "RHEL 7", "bios_uuid": "2345"},
            {"id": 3, "os_release": "RHEL 6"},
        ]

        # Test that unique id not in objects
        index, no_key_found = self.fp_task_runner._create_index_for_fingerprints(
            "bios_uuid", fingerprints, False
        )
        self.assertIsNone(no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY))

        # Tests with unique id in objects
        index, no_key_found = self.fp_task_runner._create_index_for_fingerprints(
            "bios_uuid", fingerprints
        )

        self.assertEqual(len(no_key_found), 1)
        self.assertEqual(no_key_found[0]["id"], 3)
        self.assertIsNotNone(no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY))
        self.assertEqual(len(index.keys()), 2)
        self.assertIsNotNone(index.get("1234"))
        self.assertIsNotNone(index.get("2345"))

    def test_merge_fingerprint(self):
        """Test merging a vcenter and network fingerprint."""
        nfingerprint = self._create_network_fingerprint()
        vfingerprint = self._create_vcenter_fingerprint()

        self.assertIsNone(nfingerprint.get("vm_state"))
        self.assertIsNone(nfingerprint.get("vm_uuid"))
        self.assertIsNone(nfingerprint.get("vm_dns_name"))
        self.assertIsNone(nfingerprint.get("vm_host_socket_count"))
        self.assertIsNone(nfingerprint.get("vm_datacenter"))
        self.assertIsNone(nfingerprint.get("vm_cluster"))

        self.assertIsNone(vfingerprint.get("os_name"))
        self.assertIsNone(vfingerprint.get("os_version"))
        self.assertIsNone(vfingerprint.get("bios_uuid"))
        self.assertIsNone(vfingerprint.get("subscription_manager_id"))
        self.assertIsNone(vfingerprint.get("cpu_socket_count"))
        self.assertIsNone(vfingerprint.get("cpu_core_count"))

        new_fingerprint = self.fp_task_runner._merge_fingerprint(
            nfingerprint, vfingerprint
        )

        self.assertIsNotNone(new_fingerprint.get("vm_state"))
        self.assertIsNotNone(new_fingerprint.get("vm_uuid"))
        self.assertIsNotNone(new_fingerprint.get("vm_dns_name"))
        self.assertIsNotNone(new_fingerprint.get("vm_host_socket_count"))
        self.assertIsNotNone(new_fingerprint.get("vm_datacenter"))
        self.assertIsNotNone(new_fingerprint.get("vm_cluster"))

        self.assertIsNotNone(new_fingerprint.get("name"))
        self.assertIsNotNone(new_fingerprint.get("os_name"))
        self.assertIsNotNone(new_fingerprint.get("os_version"))
        self.assertIsNotNone(new_fingerprint.get("bios_uuid"))
        self.assertIsNotNone(new_fingerprint.get("subscription_manager_id"))
        self.assertIsNotNone(new_fingerprint.get("cpu_socket_count"))
        self.assertIsNotNone(new_fingerprint.get("cpu_core_count"))

    def assert_all_fingerprints_have_sudo(self, metadata_dict):
        """
        Check if all fingerprints have 'has_sudo' set to True.

        If its not True, all offending fingerprints will appear on the error log.
        """
        # fp <<< abbreviation for fingerprint
        self.assertTrue(
            all(fp_meta["has_sudo"] for fp_meta in metadata_dict.values()),
            [
                fp_name
                for fp_name, fp_meta in metadata_dict.items()
                if not fp_meta["has_sudo"]
            ],
        )
        return True

    def test_assert_all_fingerprints_have_sudo(self):
        """Test assert_all_fingerprints_have_sudo."""
        fake_fingerprints = {"foo": {"has_sudo": True}, "bar": {"has_sudo": True}}
        self.assert_all_fingerprints_have_sudo(fake_fingerprints)
        fake_fingerprints["foo"]["has_sudo"] = False
        with self.assertRaisesMessage(AssertionError, "False is not true : ['foo']"):
            self.assert_all_fingerprints_have_sudo(fake_fingerprints)

    def test_merge_fingerprint_sudo(self):
        """Test merging two network one sudo and one without."""
        # Test that sudo is preferred when part of priority fingerprint
        sudo_fingerprint = self._create_network_fingerprint()
        sudo_fingerprint["products"] = []
        sudo_fingerprint["entitlements"] = []

        regular_fingerprint = self._create_network_fingerprint(user_has_sudo=False)
        regular_fingerprint["products"] = []
        regular_fingerprint["entitlements"] = []

        result = self.fp_task_runner._merge_fingerprint(
            sudo_fingerprint, regular_fingerprint
        )
        self.assertEqual(result, sudo_fingerprint)
        self.assert_all_fingerprints_have_sudo(result["metadata"])

        # Test that sudo is preferred when part of to merge fingerprint
        sudo_fingerprint = self._create_network_fingerprint()
        sudo_fingerprint["products"] = []
        sudo_fingerprint["entitlements"] = []

        regular_fingerprint = self._create_network_fingerprint(user_has_sudo=False)
        regular_fingerprint["products"] = []
        regular_fingerprint["entitlements"] = []

        result = self.fp_task_runner._merge_fingerprint(
            regular_fingerprint, sudo_fingerprint
        )
        self.assert_all_fingerprints_have_sudo(result["metadata"])

    def test_merge_fingerprint_network_win(self):
        """Test merge of fingerprint prioritizes network values."""
        nfingerprint = self._create_network_fingerprint()
        vfingerprint = self._create_vcenter_fingerprint()

        nfingerprint["os_release"] = "Fedora"
        self.assertNotEqual(vfingerprint.get("os_release"), nfingerprint["os_release"])

        new_fingerprint = self.fp_task_runner._merge_fingerprint(
            nfingerprint, vfingerprint
        )

        self.assertEqual(new_fingerprint.get("os_release"), nfingerprint["os_release"])

    def test_source_name_in_metadata(self):
        """Test that adding facts includes source_name in metadata."""
        sourcetopass = {
            "server_id": self.server_id,
            "source_name": self.source.name,
            "source_type": self.source.source_type,
        }
        fingerprint = {"metadata": {}}
        result = self.fp_task_runner._process_network_fact(sourcetopass, fingerprint)
        self.assertEqual(
            result["metadata"]["infrastructure_type"]["source_name"], "source1"
        )

    def test_all_facts_with_null_value_in_process_network_scan(self):
        """Test fingerprinting method with all facts set to null value."""
        source_dict = {
            "server_id": self.server_id,
            "source_name": self.source.name,
            "source_type": self.source.source_type,
        }
        facts_dict = network_template()
        result = self.fp_task_runner._process_network_fact(source_dict, facts_dict)
        metadata_dict = result.pop(META_DATA_KEY)
        self.assertEqual(
            set(metadata_dict.keys()), set(EXPECTED_FINGERPRINT_MAP_NETWORK.keys())
        )
        assert {
            fingerprint_name: {
                "server_id": self.server_id,
                "source_name": self.source.name,
                "source_type": self.source.source_type,
                "has_sudo": None,
                "raw_fact_key": fact_name,
            }
            for fingerprint_name, fact_name in EXPECTED_FINGERPRINT_MAP_NETWORK.items()
        } == metadata_dict

        expected_fingerprints = {
            fingerprint_name: None
            for fingerprint_name in EXPECTED_FINGERPRINT_MAP_NETWORK
        }
        expected_fingerprints[PRODUCTS_KEY] = mock.ANY
        expected_fingerprints[ENTITLEMENTS_KEY] = []
        expected_fingerprints["infrastructure_type"] = SystemFingerprint.UNKNOWN
        self.assertDictEqual(result, expected_fingerprints)

    def test_scan_all_facts_with_null_value_in_process_vcenter_scan(self):
        """Test fingerprinting method with all facts set to null value."""
        source_dict = {
            "server_id": self.server_id,
            "source_name": "source2",
            "source_type": DataSources.VCENTER,
        }
        facts_dict = vcenter_template()
        result = self.fp_task_runner._process_vcenter_fact(source_dict, facts_dict)
        metadata_dict = result.pop(META_DATA_KEY)
        self.assertEqual(
            set(metadata_dict.keys()), set(EXPECTED_FINGERPRINT_MAP_VCENTER.keys())
        )
        assert {
            fingerprint_name: {
                "server_id": self.server_id,
                "source_name": "source2",
                "source_type": DataSources.VCENTER,
                "has_sudo": False,
                "raw_fact_key": fact_name,
            }
            for fingerprint_name, fact_name in EXPECTED_FINGERPRINT_MAP_VCENTER.items()
        } == metadata_dict

        expected_fingerprints = {
            fingerprint_name: None
            for fingerprint_name in EXPECTED_FINGERPRINT_MAP_VCENTER
        }
        expected_fingerprints["is_redhat"] = False
        expected_fingerprints["infrastructure_type"] = SystemFingerprint.VIRTUALIZED
        expected_fingerprints[PRODUCTS_KEY] = []
        expected_fingerprints[ENTITLEMENTS_KEY] = []
        self.assertDictEqual(result, expected_fingerprints)

    def test_scan_all_facts_with_null_value_in_process_satellite_scan(self):
        """Test fingerprinting method with all facts set to null value."""
        source_dict = {
            "server_id": self.server_id,
            "source_name": "source3",
            "source_type": DataSources.SATELLITE,
        }
        facts_dict = satellite_template()
        result = self.fp_task_runner._process_satellite_fact(source_dict, facts_dict)
        metadata_dict = result.pop(META_DATA_KEY)

        self.assertEqual(
            set(metadata_dict.keys()), set(EXPECTED_FINGERPRINT_MAP_SATELLITE.keys())
        )

        self.assertDictEqual(
            {
                fingerprint_name: {
                    "server_id": self.server_id,
                    "source_name": "source3",
                    "source_type": DataSources.SATELLITE,
                    "has_sudo": False,
                    "raw_fact_key": fact_name,
                }
                for fingerprint_name, fact_name in EXPECTED_FINGERPRINT_MAP_SATELLITE.items()  # noqa E501
            },
            metadata_dict,
        )
        expected_fingerprints = {
            fingerprint_name: None
            for fingerprint_name in EXPECTED_FINGERPRINT_MAP_SATELLITE
        }
        expected_fingerprints["is_redhat"] = False
        expected_fingerprints["infrastructure_type"] = SystemFingerprint.UNKNOWN
        expected_fingerprints[ENTITLEMENTS_KEY] = []

        copy_products_list = deepcopy(PRODUCTS)
        for product in copy_products_list:
            product["metadata"] = {
                "server_id": self.server_id,
                "source_name": "source3",
                "source_type": "satellite",
                "raw_fact_key": None,
            }
        expected_fingerprints[PRODUCTS_KEY] = copy_products_list

        assert result == expected_fingerprints

    ################################################################
    # Test post processing
    ################################################################
    def test_compute_system_creation_time(self):
        """Test merge of two lists of fingerprints."""
        nfingerprints = [
            self._create_network_fingerprint(
                ifconfig_mac_addresses=["1"], date_machine_id="2018-3-7"
            )
        ]
        sfingerprints = [self._create_satellite_fingerprint(mac_addresses=["1"])]

        (
            _,
            result_fingerprints,
        ) = self.fp_task_runner._merge_fingerprints_from_source_types(
            NETWORK_SATELLITE_MERGE_KEYS, nfingerprints, sfingerprints
        )
        self.assertEqual(len(result_fingerprints), 1)
        fp = result_fingerprints[0]
        fp["date_yum_history"] = "2018-1-7"
        fp["date_filesystem_create"] = None
        fp["date_anaconda_log"] = "201837"
        fp["registration_time"] = "2018-4-7 12:45:02"
        fp["date_machine_id"] = None
        self.fp_task_runner._compute_system_creation_time(fp)
        test_date = datetime.strptime("2018-4-7", "%Y-%m-%d").date()

        self.assertEqual(fp["system_creation_date"], test_date)
        metadata = fp["metadata"]["system_creation_date"]["raw_fact_key"]
        self.assertEqual("registration_time", metadata)

    ################################################################
    # Test multi_format_dateparse
    ################################################################
    def test_multi_format_dateparse(self):
        """Test multi_format_dateparse with various formats."""
        source = {"source_type": "network", "source_name": "test_source"}
        test_date = datetime.strptime("2018-4-7", "%Y-%m-%d").date()
        date_value = self.fp_task_runner._multi_format_dateparse(
            source,
            "fake_key",
            "2018-4-7 12:45:02",
            ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"],
        )
        self.assertEqual(date_value, test_date)

        date_value = self.fp_task_runner._multi_format_dateparse(
            source,
            "fake_key",
            "2018-4-7 12:45:02 -0400",
            ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"],
        )
        self.assertEqual(date_value, test_date)

        date_value = self.fp_task_runner._multi_format_dateparse(
            source, "fake_key", "2018-4-7 12:45:02 -0400", ["%Y-%m-%d %H:%M:%S"]
        )
        self.assertIsNone(date_value)

    def test_process_details_report_failed(self):
        """Test processing a details report no valid fps."""
        fact_collection = {}
        deployments_report = DeploymentsReport(report_id=1)
        details_report = DetailsReport(deployment_report=deployments_report)
        with patch(
            "fingerprinter.task.FingerprintTaskRunner._process_sources",
            return_value=fact_collection,
        ):
            status_message, status = self.fp_task_runner._process_details_report(
                "", details_report
            )

            self.assertIn("failed", status_message.lower())
            self.assertEqual(status, "failed")

    def test_process_details_report_success(self):
        """Test processing a details report success."""
        fact_collection = {
            "name": "dhcp181-3.gsslab.rdu2.redhat.com",
            "metadata": {},
            "etc_machine_id": "3f01b55457674041b75e41829bcee1dc",
            "insights_client_id": "3f01b55457674041b75e41829bcee1dc",
            "ip_addresses": ["1.2.3.4"],
            "sources": [],
        }
        deployments_report = DeploymentsReport(report_id=1, id=1)
        deployments_report.save()
        details_report = DetailsReport(id=1, deployment_report=deployments_report)
        with patch(
            "fingerprinter.task.FingerprintTaskRunner._process_sources",
            return_value=[fact_collection],
        ):
            status_message, status = self.fp_task_runner._process_details_report(
                "", details_report
            )
        self.assertIn("success", status_message.lower())
        self.assertEqual(status, "completed")

    def test_process_details_report_exception(self):
        """Test processing a details report with an exception."""
        fact_collection = {
            "name": "dhcp181-3.gsslab.rdu2.redhat.com",
            "metadata": {},
            "sources": [],
        }
        deployments_report = DeploymentsReport(report_id=1, id=1)
        deployments_report.save()
        details_report = DetailsReport(id=1, deployment_report=deployments_report)
        with patch(
            "fingerprinter.task.FingerprintTaskRunner._process_sources",
            return_value=[fact_collection],
        ):
            with patch(
                "fingerprinter.task.SystemFingerprintSerializer.save",
                side_effect=DataError,
            ):
                status_message, status = self.fp_task_runner._process_details_report(
                    "", details_report
                )

                self.assertIn("failed", status_message.lower())
                self.assertEqual(status, "failed")

    def test_format_certs(self):
        """Testing the format_certs function."""
        certs = ["69.pem", "67.pem", ""]
        formatted_certs = FingerprintTaskRunner.format_certs(certs)
        self.assertEqual([69, 67], formatted_certs)
        # assert empty list stays empty
        certs = []
        formatted_certs = FingerprintTaskRunner.format_certs(certs)
        self.assertEqual([], formatted_certs)
        # assert exception returns empty
        certs = ["notint.pem"]
        formatted_certs = FingerprintTaskRunner.format_certs(certs)
        self.assertEqual([], formatted_certs)
