#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Satellite 5 API handlers."""
import logging
import xmlrpc.client
from multiprocessing import Pool

from api.models import ScanJob, SystemInspectionResult
from scanner.satellite import utils
from scanner.satellite.api import (
    SatelliteCancelException,
    SatelliteException,
    SatelliteInterface,
    SatellitePauseException,
)
from scanner.satellite.utils import raw_facts_template

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

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


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
# pylint: disable=too-many-arguments
def request_host_details(
    host_id, host_name, last_checkin, scan_task, request_options, logging_options
):
    """Execute http responses to gather satellite data.

    :param host_id: The identifier of the host
    :param host_name: The name of the host
    :param last_checkin: The date of last checkin
    :param scan_task: The current scan task
    :param request_options: A dictionary containing the host, port,
        user, and password for the source
    :param: logging_options: A dictionary containing the scan_task type,
        scan_task id, and source_type, and the source_name
    """
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
        system_inspection_result = SystemInspectionResult.SUCCESS
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
        system_inspection_result = SystemInspectionResult.FAILED

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
            raise SatelliteException(str(xml_error))
        self.connect_scan_task.update_stats(
            "INITIAL STATELLITE STATS", sys_count=systems_count
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
            raise SatelliteException(str(xml_error))

        return hosts

    def prepare_host(self, chunk):
        """Prepare each host with necessary information.

        :param chunk: A list of hosts
        :returns A list of tuples that contain information about
            each host.
        """
        if self.inspect_scan_task is None:
            raise SatelliteException(
                "host_details cannot be called for a connection scan"
            )
        ssl_cert_verify = True
        source_options = self.inspect_scan_task.source.options
        if source_options:
            ssl_cert_verify = source_options.ssl_cert_verify
        host, port, user, password = utils.get_connect_data(self.inspect_scan_task)
        logging_options = {
            "job_id": self.scan_job.id,
            "task_sequence_number": self.inspect_scan_task.sequence_number,
            "scan_type": self.inspect_scan_task.scan_type,
            "source_type": self.inspect_scan_task.source.source_type,
            "source_name": self.inspect_scan_task.source.name,
        }
        request_options = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "ssl_cert_verify": ssl_cert_verify,
        }
        host_params = [
            (
                host.get(ID),
                host.get(NAME),
                str(host.get(LAST_CHECKIN, "")),
                self.inspect_scan_task,
                request_options,
                logging_options,
            )
            for host in chunk
        ]
        return host_params

    # pylint: disable=too-many-locals
    def process_results(self, results, virtual_hosts, virtual_guests, physical_hosts):
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
            if system_inspection_result == SystemInspectionResult.SUCCESS:
                uuid = raw_result["uuid"]
                cpu = raw_result["cpu"]
                host_id = raw_result["host_id"]
                system_details = raw_result["system_details"]
                kernel = raw_result["kernel"]
                subs = raw_result["subs"]
                network_devices = raw_result["network_devices"]
                registration_date = raw_result["registration_date"]

                if uuid is None or uuid == "":
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
            raise SatelliteException(str(xml_error))

        for guest in virt_guests:
            virt_id = guest.get(ID)
            virtual_guests[virt_id] = virtual_host_id

        return (virtual_guests, len(virt_guests))

    # pylint: disable=too-many-locals
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
                if uuid is None or uuid == "":
                    uuid = virt_host_id
                virtual_host = {ID: virt_host_id, NAME: virt_host_name, UUID: uuid}
                virtual_hosts[virt_host_id] = virtual_host
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteException(str(xml_error))

        for virt_host in virt_hosts:
            virt_host_id = virt_host.get(ID)
            virtual_host = virtual_hosts.get(virt_host_id)
            self.inspect_scan_task.log_message(
                "Obtaining virtual guests for virtual host"
                f" (name={virtual_host.get('name', 'unknown')}, id={virtual_host.get('id', 'unknown')})"
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
            raise SatelliteException(str(xml_error))

        return physical_hosts

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
        if self.inspect_scan_task is None:
            raise SatelliteException(
                "hosts_facts cannot be called for a connection scan"
            )
        systems_count = len(self.connect_scan_task.connection_result.systems.all())
        self.inspect_scan_task.update_stats(
            "INITIAL STATELLITE STATS", sys_count=systems_count
        )

        hosts_before_dedup = []
        deduplicated_hosts = []
        client, user, password = utils.get_sat5_client(self.inspect_scan_task)
        with Pool(processes=self.max_concurrency) as pool:
            try:
                key = client.auth.login(user, password)
                hosts_before_dedup = client.system.list_user_systems(key)
                client.auth.logout(key)
            except xmlrpc.client.Fault as xml_error:
                raise SatelliteException(str(xml_error))
            virtual_hosts, virtual_guests = self.virtual_hosts()
            physical_hosts = self.physical_hosts()
            hosts_after_dedup = []
            for host in hosts_before_dedup:
                if host not in deduplicated_hosts:
                    hosts_after_dedup.append(host)
                    deduplicated_hosts.append(host)
            hosts = hosts_before_dedup
            chunks = [
                hosts[i : i + self.max_concurrency]
                for i in range(0, len(hosts), self.max_concurrency)
            ]
            for chunk in chunks:
                if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
                    raise SatelliteCancelException()

                if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
                    raise SatellitePauseException()
                host_params = self.prepare_host(chunk)
                results = pool.starmap(request_host_details, host_params)
                self.process_results(
                    results, virtual_hosts, virtual_guests, physical_hosts
                )

        utils.validate_task_stats(self.inspect_scan_task)
