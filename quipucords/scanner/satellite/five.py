"""Satellite 5 API handlers."""

import logging
import xmlrpc.client
from collections.abc import Iterable
from functools import partial

import celery
from more_itertools import unique_everseen

from api.models import InspectResult
from api.scantask.model import ScanTask
from scanner.satellite import utils
from scanner.satellite.api import SatelliteError, SatelliteInterface
from scanner.satellite.utils import raw_facts_template

logger = logging.getLogger(__name__)

UNKNOWN = "unknown"
ID = "id"
NAME = "name"
INTERFACE = "interface"
LOOPBACK = "lo"
LOOPBACK_MAC_ADDR = "00:00:00:00:00:00"
IP = "ip"
HARDWARE_ADDRESS = "hardware_address"
IP_ADDRESSES = "ip_addresses"
MAC_ADDRESSES = "mac_addresses"
UUID = "uuid"
HOSTNAME = "hostname"
REGISTRATION_TIME = "registration_time"
LAST_CHECKIN = "last_checkin"
LAST_CHECKIN_TIME = "last_checkin_time"
RELEASE = "release"
OS_NAME = "os_name"
OS_VERSION = "os_version"
OS_RELEASE = "os_release"
IS_VIRT = "is_virtualized"
KERNEL = "kernel_version"
ARCH = "arch"
ARCHITECTURE = "architecture"
COUNT = "count"
SOCKET_COUNT = "socket_count"
CORES = "cores"
SOCKETS = "num_sockets"
ENTITLEMENTS = "entitlements"
NUM_VIRTUAL_GUESTS = "num_virtual_guests"
VIRTUAL = "virtual"
VIRTUAL_HOST_UUID = "virtual_host_uuid"
VIRTUAL_HOST_NAME = "virtual_host_name"
HYPERVISOR = "hypervisor"


@celery.shared_task(name="request_host_details_sat_five")
def request_host_details(  # noqa: PLR0913
    host_id,
    host_name,
    last_checkin,
    scan_task: ScanTask | int,
    request_options,
    logging_options,
):
    """Wrap _request_host_details to call it as an async Celery task."""
    return _request_host_details(
        host_id, host_name, last_checkin, scan_task, request_options, logging_options
    )


def _request_host_details(  # noqa: PLR0913
    host_id,
    host_name,
    last_checkin,
    scan_task: ScanTask | int,
    request_options,
    logging_options,
):
    """Request detailed data about a specific host from the Satellite server.

    :param host_id: The identifier of the host
    :param host_name: The name of the host
    :param last_checkin: The date of last checkin
    :param scan_task: The current scan task or its ID
    :param request_options: A dictionary containing the host, port,
        user, and password for the source
    :param: logging_options: A dictionary containing the scan_task type,
        scan_task id, and source_type, and the source_name
    """
    if isinstance(scan_task, int):
        scan_task = ScanTask.objects.get(id=scan_task)
    unique_name = f"{host_name}_{host_id}"
    results = raw_facts_template()
    client, user, password = utils.get_sat5_client(scan_task, request_options)
    try:
        message = f"REQUESTING HOST DETAILS: {unique_name}%s"
        scan_task.log_message(message, logging.INFO, logging_options)

        key = client.auth.login(user, password)
        uuid = client.system.get_uuid(key, host_id)
        cpu = client.system.get_cpu(key, host_id)
        system_details = client.system.get_details(key, host_id)
        kernel = client.system.get_running_kernel(key, host_id)
        subs = client.system.get_entitlements(key, host_id)

        network_devices = client.system.get_network_devices(key, host_id)
        registration_date = client.system.get_registration_date(key, host_id)

        client.auth.logout(key)
        system_inspection_result = InspectResult.SUCCESS
        results["uuid"] = uuid
        results["cpu"] = cpu
        results["system_details"] = system_details
        results["kernel"] = kernel
        results["subs"] = subs
        results["network_devices"] = network_devices
        results["registration_date"] = registration_date

    except xmlrpc.client.Fault as xml_error:
        error_message = f"Satellite 5 fault error encountered: {xml_error}\n"
        logger.error(error_message)
        system_inspection_result = InspectResult.FAILED

    results["host_name"] = host_name
    results["host_id"] = host_id
    results["last_checkin"] = last_checkin
    results["system_inspection_result"] = system_inspection_result

    return results


class SatelliteFive(SatelliteInterface):
    """Interact with Satellite 5."""

    def host_count(self):
        """Obtain the count of managed hosts."""
        systems_count = 0
        client, user, password = utils.get_sat5_client(self.connect_scan_task)
        try:
            key = client.auth.login(user, password)
            systems = client.system.list_user_systems(key)
            systems_count = len(systems)
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteError(str(xml_error)) from xml_error
        self.connect_scan_task.update_stats(
            "INITIAL SATELLITE STATS", sys_count=systems_count
        )
        return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        hosts = []
        credential = utils.get_credential(self.connect_scan_task)
        client, user, password = utils.get_sat5_client(self.connect_scan_task)
        try:
            key = client.auth.login(user, password)
            systems = client.system.list_user_systems(key)
            client.auth.logout(key)

            for system in systems:
                host_name = system.get(NAME)
                host_id = system.get(ID)

                if host_name is not None and host_id is not None:
                    unique_name = f"{host_name}_{host_id}"
                    hosts.append(unique_name)
                    self.record_conn_result(unique_name, credential)

        except xmlrpc.client.Fault as xml_error:
            raise SatelliteError(str(xml_error)) from xml_error

        return hosts

    def prepare_hosts(self, hosts: Iterable[dict], ids_only=False):
        """Prepare each host with necessary information.

        :param hosts: an iterable of dicts that each contain information about one host
        :param ids_only: bool to determine inclusion of ids or whole ScanTask objects
        :return: A list of tuples that contain information about each host.
        """
        host_params = [
            (
                host.get(ID),
                host.get(NAME),
                str(host.get(LAST_CHECKIN, "")),
                self.inspect_scan_task.id if ids_only else self.inspect_scan_task,
                self._prepare_host_request_options(),
                self._prepare_host_logging_options(),
            )
            for host in hosts
        ]
        return host_params

    def process_results(  # noqa: PLR0912, PLR0915, C901
        self, results, virtual_hosts, virtual_guests, physical_hosts
    ):
        """Process & record the list of responses returned from sat5 endpoint.

        :param results: A list of responses
        :param virtual_hosts: A dictionary of virtual host data
        :param virtual_guests: A dictionary of guest to host data
        :param physical_hosts: A list of physical host ids

        """
        for raw_result in results:
            host_name = raw_result["host_name"]
            host_id = raw_result["host_id"]
            unique_name = f"{host_name}_{host_id}"
            last_checkin = raw_result["last_checkin"]
            system_inspection_result = raw_result["system_inspection_result"]

            details = {}
            if system_inspection_result == InspectResult.SUCCESS:
                uuid = raw_result["uuid"]
                cpu = raw_result["cpu"]
                host_id = raw_result["host_id"]
                system_details = raw_result["system_details"]
                kernel = raw_result["kernel"]
                subs = raw_result["subs"]
                network_devices = raw_result["network_devices"]
                registration_date = raw_result["registration_date"]

                if uuid is None or uuid == "":  # noqa: PLC1901
                    uuid = host_id
                arch = cpu.get(ARCH, UNKNOWN)
                cpu_count = cpu.get(COUNT)
                cpu_core_count = cpu_count
                cpu_socket_count = cpu.get(SOCKET_COUNT)
                hostname = system_details.get(HOSTNAME)
                release = system_details.get(RELEASE)

                entitlements = []
                for sub in subs:
                    entitlement = {NAME: sub}
                    entitlements.append(entitlement)

                ip_addresses = []
                mac_addresses = []
                for device in network_devices:
                    interface = device.get(INTERFACE)
                    if interface and not interface.startswith(LOOPBACK):
                        ip_addr = device.get(IP)
                        if ip_addr:
                            ip_addresses.append(ip_addr.lower())
                        mac = device.get(HARDWARE_ADDRESS)
                        if mac and mac.lower() != LOOPBACK_MAC_ADDR:
                            mac_addresses.append(mac.lower())

                mac_addresses = list(set(mac_addresses))
                ip_addresses = list(set(ip_addresses))

                details[UUID] = uuid
                details[NAME] = host_name
                details[HOSTNAME] = hostname
                details[LAST_CHECKIN_TIME] = str(last_checkin)
                details[REGISTRATION_TIME] = str(registration_date)
                details[ARCHITECTURE] = arch
                details[KERNEL] = kernel
                details[CORES] = cpu_core_count
                details[SOCKETS] = cpu_socket_count
                details[OS_RELEASE] = release
                details[ENTITLEMENTS] = entitlements
                details[IP_ADDRESSES] = ip_addresses
                details[MAC_ADDRESSES] = mac_addresses

                if host_id in physical_hosts:
                    details[IS_VIRT] = False

                if virtual_hosts.get(host_id):
                    virtual_host = virtual_hosts.get(host_id)
                    details[VIRTUAL] = HYPERVISOR
                    guests = virtual_host.get(NUM_VIRTUAL_GUESTS, 0)
                    details[NUM_VIRTUAL_GUESTS] = guests
                    details[IS_VIRT] = False

                elif virtual_guests.get(host_id):
                    virt_host_id = virtual_guests.get(host_id)
                    virtual_host = virtual_hosts.get(virt_host_id)
                    details[IS_VIRT] = True
                    if virtual_host.get(UUID):
                        details[VIRTUAL_HOST_UUID] = virtual_host.get(UUID)
                    if virtual_host.get(NAME):
                        details[VIRTUAL_HOST_NAME] = virtual_host.get(NAME)

                logger.debug("host_id=%s, host_details=%s", host_id, details)
            result = {
                "name": unique_name,
                "details": details,
                "status": system_inspection_result,
            }

            if result is not None:
                self.record_inspect_result(
                    result.get("name"), result.get("details"), result.get("status")
                )

    def virtual_guests(self, virtual_host_id):
        """Obtain the virtual guest information for a virtual host.

        :param virtual_host_id: The identifier for a virtual host
        :returns: a tuple of a dictionary of virtual guest id, virtual_host_id
            and the number of guests
        """
        virtual_guests = {}
        virt_guests = []
        client, user, password = utils.get_sat5_client(self.connect_scan_task)
        try:
            key = client.auth.login(user, password)
            virt_guests = client.system.list_virtual_guests(key, virtual_host_id)
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteError(str(xml_error)) from xml_error

        for guest in virt_guests:
            virt_id = guest.get(ID)
            virtual_guests[virt_id] = virtual_host_id

        return (virtual_guests, len(virt_guests))

    def virtual_hosts(self):
        """Obtain the virtual host data.

        :returns: tuple of (list of virtual host ids,
            dictionary of virtual guest id to virtual_host_id)
        """
        virt_hosts = []
        virtual_hosts = {}
        virtual_guests = {}
        self.inspect_scan_task.log_message("Obtaining satellite 5 virtual hosts")
        client, user, password = utils.get_sat5_client(self.connect_scan_task)
        try:
            key = client.auth.login(user, password)
            virt_hosts = client.system.list_virtual_hosts(key)
            for virt_host in virt_hosts:
                virt_host_id = virt_host.get(ID)
                virt_host_name = virt_host.get(NAME)
                uuid = client.system.get_uuid(key, virt_host_id)
                if uuid is None or uuid == "":  # noqa: PLC1901
                    uuid = virt_host_id
                virtual_host = {ID: virt_host_id, NAME: virt_host_name, UUID: uuid}
                virtual_hosts[virt_host_id] = virtual_host
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteError(str(xml_error)) from xml_error

        for virt_host in virt_hosts:
            virt_host_id = virt_host.get(ID)
            virtual_host = virtual_hosts.get(virt_host_id)
            self.inspect_scan_task.log_message(
                "Obtaining virtual guests for virtual host"
                f" (name={virtual_host.get('name', 'unknown')},"
                f" id={virtual_host.get('id', 'unknown')})"
            )
            guests, guest_count = self.virtual_guests(virt_host_id)
            virtual_guests.update(guests)
            virtual_host[NUM_VIRTUAL_GUESTS] = guest_count

        return (virtual_hosts, virtual_guests)

    def physical_hosts(self):
        """Obtain the physical host data.

        :returns: list of phyiscal host ids
        """
        physical_hosts = []
        self.inspect_scan_task.log_message("Obtaining satellite 5 physical hosts")
        client, user, password = utils.get_sat5_client(self.connect_scan_task)
        try:
            key = client.auth.login(user, password)
            physical_systems = client.system.list_physical_systems(key)
            for system in physical_systems:
                host_id = system.get(ID)
                if host_id:
                    physical_hosts.append(host_id)
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteError(str(xml_error)) from xml_error

        return physical_hosts

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
        if self.inspect_scan_task is None:
            raise SatelliteError("hosts_facts cannot be called for a connection scan")
        systems_count = len(self.connect_scan_task.connection_result.systems.all())
        self.inspect_scan_task.update_stats(
            "INITIAL SATELLITE STATS", sys_count=systems_count
        )

        client, user, password = utils.get_sat5_client(self.inspect_scan_task)
        try:
            key = client.auth.login(user, password)
            hosts = client.system.list_user_systems(key)
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteError(str(xml_error)) from xml_error
        virtual_hosts, virtual_guests = self.virtual_hosts()
        physical_hosts = self.physical_hosts()
        hosts = unique_everseen(hosts)

        _process_results = partial(
            self.process_results,
            virtual_hosts=virtual_hosts,
            virtual_guests=virtual_guests,
            physical_hosts=physical_hosts,
        )

        self._prepare_and_process_hosts(
            hosts, request_host_details, _process_results, manager_interrupt
        )

        utils.validate_task_stats(self.inspect_scan_task)
