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
from scanner.satellite.api import SatelliteInterface, SatelliteException
from scanner.satellite import utils


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

UNKNOWN = 'unknown'
ID = 'id'
NAME = 'name'
INTERFACE = 'interface'
ETHERNET = 'eth'
IP = 'ip'
HARDWARE_ADDRESS = 'hardware_address'
IP_ADDRESSES = 'ip_addresses'
MAC_ADDRESSES = 'mac_addresses'
UUID = 'uuid'
HOSTNAME = 'hostname'
REGISTRATION_TIME = 'registration_time'
LAST_CHECKIN = 'last_checkin'
LAST_CHECKIN_TIME = 'last_checkin_time'
RELEASE = 'release'
OS_NAME = 'os_name'
OS_VERSION = 'os_version'
OS_RELEASE = 'os_release'
IS_VIRT = 'is_virtualized'
KERNEL = 'kernel_version'
ARCH = 'arch'
ARCHITECTURE = 'architecture'
COUNT = 'count'
SOCKET_COUNT = 'socket_count'
CORES = 'cores'
SOCKETS = 'num_sockets'
ENTITLEMENTS = 'entitlements'
NUM_VIRTUAL_GUESTS = 'num_virtual_guests'
VIRTUAL = 'virtual'
VIRTUAL_HOST = 'virtual_host'
VIRTUAL_HOST_NAME = 'virtual_host_name'
HYPERVISOR = 'hypervisor'


class SatelliteFive(SatelliteInterface):
    """Interact with Satellite 5."""

    def host_count(self):
        """Obtain the count of managed hosts."""
        systems_count = 0
        client, user, password = utils.get_sat5_client(self.scan_task)
        try:
            key = client.auth.login(user, password)
            systems = client.system.list_user_systems(key)
            systems_count = len(systems)
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteException(str(xml_error))
        self.initialize_stats(systems_count)
        return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        hosts = []
        credential = utils.get_credential(self.scan_task)
        client, user, password = utils.get_sat5_client(self.scan_task)
        try:
            key = client.auth.login(user, password)
            systems = client.system.list_user_systems(key)
            client.auth.logout(key)

            for system in systems:
                name = system.get(NAME)
                if name is not None:
                    hosts.append(name)
                    self.record_conn_result(name, credential)

        except xmlrpc.client.Fault as xml_error:
            raise SatelliteException(str(xml_error))

        return hosts

    # pylint: disable=too-many-arguments, too-many-locals, too-many-statements
    def host_details(self, host_id, host_name, last_checkin,
                     virtual_hosts, virtual_guests):
        """Obtain the details for a given host id and name.

        :param host_id: The identifier of the host
        :param host_name: The name of the host
        :param last_checkin: The date of last checkin
        :param virtual_hosts: A dictionary of virtual host data
        :param virtual_guests: A dictionary of guest to host data
        :returns: dictionary of host details
        """
        details = {}
        sys_result = self.inspect_result.systems.filter(
            name=host_name).first()

        if sys_result:
            logger.debug('Results already captured for host_name=%s',
                         host_name)
            return details
        client, user, password = utils.get_sat5_client(self.scan_task)
        try:
            key = client.auth.login(user, password)
            uuid = client.system.get_uuid(key, host_id)
            if uuid is None or uuid == '':
                uuid = host_id

            cpu = client.system.get_cpu(key, host_id)
            arch = cpu.get(ARCH, UNKNOWN)
            cpu_count = cpu.get(COUNT)
            cpu_core_count = cpu_count
            cpu_socket_count = cpu.get(SOCKET_COUNT)

            system_details = client.system.get_details(key, host_id)
            hostname = system_details.get(HOSTNAME)
            release = system_details.get(RELEASE)

            kernel = client.system.get_running_kernel(key, host_id)

            entitlements = []
            subs = client.system.get_entitlements(key, host_id)
            for sub in subs:
                entitlement = {NAME: sub}
                entitlements.append(entitlement)

            network_devices = client.system.get_network_devices(key, host_id)
            ip_addresses = []
            mac_addresses = []
            for device in network_devices:
                interface = device.get(INTERFACE)
                if interface and interface.startswith(ETHERNET):
                    ip_addr = device.get(IP)
                    if ip_addr:
                        ip_addresses.append(ip_addr)
                    mac = device.get(HARDWARE_ADDRESS)
                    if mac:
                        mac_addresses.append(mac)
            registration_date = client.system.get_registration_date(key,
                                                                    host_id)

            details[UUID] = uuid
            details[NAME] = host_name
            details[HOSTNAME] = hostname
            details[LAST_CHECKIN_TIME] = last_checkin
            details[REGISTRATION_TIME] = str(registration_date)
            details[ARCHITECTURE] = arch
            details[KERNEL] = kernel
            details[CORES] = cpu_core_count
            details[SOCKETS] = cpu_socket_count
            details[OS_RELEASE] = release
            details[ENTITLEMENTS] = entitlements
            details[IP_ADDRESSES] = ip_addresses
            details[MAC_ADDRESSES] = mac_addresses

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
                    details[VIRTUAL_HOST] = virtual_host.get(UUID)
                if virtual_host.get(NAME):
                    details[VIRTUAL_HOST_NAME] = virtual_host.get(NAME)

            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteException(str(xml_error))

        self.record_inspect_result(host_name, details)
        logger.debug('host_id=%s, host_details=%s',
                     host_id, details)
        return details

    def virtual_guests(self, virtual_host_id):
        """Obtain the virtual guest information for a virtual host.

        :param virtual_host_id: The identifier for a virtual host
        :returns: a tule of a dictionary of virtual guest id, virtual_host_id
            and the number of guests
        """
        virtual_guests = {}
        virt_guests = []
        client, user, password = utils.get_sat5_client(self.scan_task)
        try:
            key = client.auth.login(user, password)
            virt_guests = client.system.list_virtual_guests(key,
                                                            virtual_host_id)
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
        client, user, password = utils.get_sat5_client(self.scan_task)
        try:
            key = client.auth.login(user, password)
            virt_hosts = client.system.list_virtual_hosts(key)
            for virt_host in virt_hosts:
                virt_host_id = virt_host.get(ID)
                virt_host_name = virt_host.get(NAME)
                uuid = client.system.get_uuid(key, virt_host_id)
                if uuid is None or uuid == '':
                    uuid = virt_host_id
                virtual_host = {ID: virt_host_id,
                                NAME: virt_host_name,
                                UUID: uuid}
                virtual_hosts[virt_host_id] = virtual_host
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteException(str(xml_error))

        for virt_host in virt_hosts:
            virt_host_id = virt_host.get(ID)
            virtual_host = virtual_hosts.get(virt_host_id)
            guests, guest_count = self.virtual_guests(virt_host_id)
            virtual_guests.update(guests)
            virtual_host[NUM_VIRTUAL_GUESTS] = guest_count

        return(virtual_hosts, virtual_guests)

    def hosts_facts(self):
        """Obtain the managed hosts detail raw facts."""
        systems_count = len(self.conn_result.systems.all())
        self.initialize_stats(systems_count)

        hosts = []
        client, user, password = utils.get_sat5_client(self.scan_task)
        try:
            key = client.auth.login(user, password)
            hosts = client.system.list_user_systems(key)
            client.auth.logout(key)
        except xmlrpc.client.Fault as xml_error:
            raise SatelliteException(str(xml_error))

        virtual_hosts, virtual_guests = self.virtual_hosts()

        for host in hosts:
            last_checkin = str(host.get(LAST_CHECKIN, ''))
            self.host_details(host.get(ID), host.get(NAME), last_checkin,
                              virtual_hosts, virtual_guests)
