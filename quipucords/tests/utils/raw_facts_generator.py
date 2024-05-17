"""Utility functions to generate raw facts."""

import zoneinfo

from faker import Faker

from constants import DataSources
from scanner.openshift.entities import OCPCluster, OCPNode

_faker = Faker()

DEFAULT_RHEL_OS_NAME = "Red Hat Enterprise Linux"


def raw_facts_generator(source_type, n, as_native_types=True):
    """Generate 'n' raw facts for a given source type."""
    if source_type == DataSources.OPENSHIFT:
        # ocp gets a special treatment due to its asymmetric raw facts (cluster vs node)
        # and the choice of how to represent them as "native" python types (dict/list)
        # or their original representation as pydantic models
        yield from _openshift_raw_facts_generator(n, as_native_types=as_native_types)
    else:
        func_map = {
            DataSources.NETWORK: _network_raw_facts,
            DataSources.ANSIBLE: _ansible_raw_facts,
            DataSources.SATELLITE: _satellite_raw_facts,
            DataSources.VCENTER: _vcenter_raw_facts,
            DataSources.RHACS: _rhacs_raw_facts,
        }
        raw_fact_func = func_map[source_type]
        for _ in range(n):
            yield raw_fact_func()


def fake_rhel(name: str | None = None, version: str | None = None) -> str:
    """Return a string representing a fake etc_release for RHEL."""
    codename = _faker.slug().capitalize()
    return (
        f"{name if name else DEFAULT_RHEL_OS_NAME} "
        f"release {version if version else fake_major_minor_ver()} "
        f"({codename})"
    )


def fake_installed_products() -> list[dict]:
    """Return a list representing at least one found installed product."""
    installed_products = [
        {
            "id": str(_faker.pyint(min_value=100, max_value=999)),
            "name": f"Red Hat {_faker.name().title()} {fake_semver()}",
        }
        for _ in range(_faker.pyint(min_value=1, max_value=5))
    ]
    return installed_products


def fake_major_minor_ver():
    """Return a string representing an X.Y version."""
    major = _faker.pyint(min_value=1, max_value=99)
    minor = _faker.random_digit()
    return f"{major}.{minor}"


def fake_semver():
    """Return a string representing a semantic version."""
    patch = _faker.random_digit()
    return f"{fake_major_minor_ver()}.{patch}"


def _network_raw_facts():
    # bare minimal network scan raw facts
    facts = {
        "cloud_provider": _faker.random_element(["aws", "gcp"]),
        "cpu_core_count": _faker.pyint(min_value=1, max_value=9),
        "cpu_count": _faker.pyint(min_value=1, max_value=9),
        "cpu_hyperthreading": _faker.pybool(),
        "cpu_socket_count": _faker.pyint(min_value=1, max_value=9),
        "dmi_system_uuid": _faker.uuid4(),
        "etc_machine_id": _faker.uuid4(),
        "etc_release_release": fake_rhel(),
        "ifconfig_ip_addresses": [_faker.ipv4()],
        "ifconfig_mac_addresses": [_faker.mac_address()],
        "insights_client_id": _faker.uuid4(),
        "installed_products": fake_installed_products(),
        "subscription_manager_id": _faker.uuid4(),
        "system_memory_bytes": _faker.pyint(max_value=2**63),  # max value for bigint
        "system_purpose_json": None,
        "uname_processor": _faker.random_element(["x86_64", "ARM"]),
        "virt_type": _faker.random_element(["vmware", "xen", "kvm", None]),
    }
    # some facts that depend on others for consistency. not 100% accurate but good
    # enough for testing
    facts["virt_virt"] = "virt-guest" if facts["virt_type"] else "virt-host"
    facts["virt_what_type"] = facts["virt_type"]
    # use integer division as a float will be invalid in fingerprint validation
    facts["cpu_core_per_socket"] = facts["cpu_core_count"] // facts["cpu_socket_count"]
    return facts


def _vcenter_raw_facts():
    return {
        "vm.cluster": None,
        "vm.cpu_count": _faker.pyint(min_value=1, max_value=9),
        "vm.datacenter": None,
        "vm.dns_name": None,
        "vm.host.cpu_cores": _faker.pyint(min_value=1, max_value=9),
        "vm.host.cpu_count": _faker.pyint(min_value=1, max_value=9),
        "vm.host.cpu_threads": _faker.pyint(min_value=1, max_value=9),
        "vm.host.name": _faker.hostname(),
        "vm.host.uuid": _faker.uuid4(),
        "vm.ip_addresses": [_faker.ipv4()],
        "vm.last_check_in": None,
        "vm.mac_addresses": [_faker.mac_address()],
        "vm.memory_size": None,
        "vm.name": _faker.slug(),
        "vm.os": None,
        "vm.state": None,
        "vm.is_template": _faker.pybool(),
        "vm.uuid": _faker.uuid4(),
    }


def _satellite_raw_facts():
    os_version = fake_major_minor_ver()
    major_ver = os_version.split(".")[0]
    satellite_date_format = "%Y-%m-%d %H:%M:%S"
    arch = _faker.random_element(["x86_64", "ARM"])
    return {
        "architecture": _faker.random_element([arch, None]),
        "connection_timestamp": _faker.date_time().strftime(satellite_date_format),
        "cores": str(_faker.pyint(min_value=1, max_value=9)),
        "entitlements": [],
        "errata_out_of_date": _faker.pyint(min_value=0, max_value=1000),
        "hostname": _faker.hostname(),
        "ip_addresses": [_faker.ipv4()],
        "is_virtualized": str(_faker.pybool()),
        "katello_agent_installed": _faker.pybool(),
        "kernel_version": f"{fake_semver()}-{fake_semver()}.el{major_ver}.{arch}",
        "last_checkin_time": _faker.date_time().strftime(satellite_date_format),
        "location": _faker.sentence(),
        "mac_addresses": [_faker.mac_address()],
        "num_sockets": _faker.pyint(min_value=1, max_value=9),
        "num_virtual_guests": _faker.pyint(min_value=1, max_value=9),
        "organization": _faker.company(),
        "os_name": "RHEL",
        "os_release": f"RHEL {os_version}",
        "os_version": os_version,
        "packages_out_of_date": _faker.pyint(min_value=0, max_value=1000),
        "registration_time": _faker.date_time().strftime(satellite_date_format),
        "uuid": str(_faker.uuid4()),
        "virt_type": _faker.random_element(["vmware", "xen", "kvm", None]),
        "virtual": _faker.random_element(["hypervisor", None]),
        "virtual_host_name": _faker.hostname(),
    }


def _ansible_raw_facts():
    """Raw facts for ansible scans."""
    listed_host = _faker.ipv4()
    deleted_host = _faker.ipv4()
    return {
        "comparison": {
            "hosts_in_inventory": [listed_host],
            "hosts_only_in_jobs": [deleted_host],
            "number_of_hosts_in_inventory": 1,
            "number_of_hosts_only_in_jobs": 1,
        },
        "hosts": [
            {
                "created": _faker.date_time(),
                "host_id": 1,
                "last_job": None,
                "modified": _faker.date_time(),
                "name": listed_host,
            }
        ],
        "instance_details": {
            "active_node": _faker.ipv4(),
            "system_name": _faker.ipv4(),
            "version": fake_semver(),
        },
        "jobs": {
            "job_ids": [1, 2],
            "unique_hosts": [deleted_host, listed_host],
        },
    }


def _openshift_raw_facts_generator(number_of_facts, as_native_types=True):
    """Generate openshift raw facts."""
    # TODO: consider adopting a solution like polyfactory to generate factories for
    # pydantic models
    cluster = OCPCluster(
        uuid=_faker.uuid4(),
        version=fake_semver(),
    )
    yield {
        "cluster": cluster.dict() if as_native_types else cluster,
        "operators": [],
        "rhacm_metrics": [],
    }
    for _ in range(number_of_facts):
        node = OCPNode(
            name=_faker.slug(),
            errors={},
            labels={"node-role.kubernetes.io/master": ""},
            taints=[{"key": "some", "effect": "some"}],
            capacity={
                "cpu": _faker.pyint(min_value=1, max_value=50),
                "memory_in_bytes": _faker.pyint(min_value=1, max_value=2**65),
                "pods": _faker.pyint(min_value=50, max_value=500),
            },
            addresses=[{"type": "ip", "address": _faker.ipv4()}],
            machine_id=_faker.uuid4(),
            allocatable={
                "cpu": _faker.pyint(min_value=1, max_value=50),
                "memory_in_bytes": _faker.pyint(min_value=1, max_value=2**65),
                "pods": _faker.pyint(min_value=50, max_value=500),
            },
            architecture="amd64",
            kernel_version=f"{fake_semver()}-{fake_semver()}.el{_faker.random_digit()}.x86_64",
            operating_system="linux",
            creation_timestamp=_faker.date_time(
                tzinfo=zoneinfo.ZoneInfo("UTC")
            ).replace(microsecond=0),
            cluster_uuid=cluster.uuid,
        )
        yield {"node": node.dict() if as_native_types else node}


def _rhacs_raw_facts():
    """Raw facts for RHACS scans."""
    return {
        "secured_units_current": {
            "numNodes": _faker.pyint(min_value=1, max_value=1000),
            "numCpuUnits": _faker.pyint(min_value=1, max_value=1000),
        },
        "secured_units_max": {
            "maxNodesAt": _faker.date_time(),
            "maxNodes": _faker.pyint(min_value=1, max_value=1000),
            "maxCpuUnitsAt": _faker.date_time(),
            "maxCpuUnits": _faker.pyint(min_value=1, max_value=1000),
        },
    }
