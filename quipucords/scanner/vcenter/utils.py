#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Utilities used for VCenter operations."""
import atexit
import ssl

from pyVim.connect import Disconnect, SmartConnect, SmartConnectNoSSL
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from api.vault import decrypt_data_as_unicode


def vcenter_connect(scan_task):
    """Connect to VCenter.

    :param scan_task: The scan task
    :returns: VCenter connection object.
    """
    vcenter = None
    disable_ssl = None
    ssl_cert_verify = None
    ssl_protocol = None
    source = scan_task.source
    credential = source.credentials.all().first()
    user = credential.username
    host = scan_task.source.get_hosts()[0]
    password = decrypt_data_as_unicode(credential.password)
    port = scan_task.source.port
    options = source.options

    if options:
        if options.disable_ssl and options.disable_ssl is True:
            disable_ssl = True
        if options.ssl_cert_verify is not None:
            ssl_cert_verify = options.ssl_cert_verify
        ssl_protocol = options.get_ssl_protocol()

    if disable_ssl:
        vcenter = SmartConnectNoSSL(host=host, user=user, pwd=password, port=port)
    elif ssl_protocol is None and ssl_cert_verify is None:
        vcenter = SmartConnect(host=host, user=user, pwd=password, port=port)
    else:
        ssl_context = None
        if ssl_protocol is None:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
        else:
            ssl_context = ssl.SSLContext(protocol=ssl_protocol)
        if ssl_cert_verify is False:
            ssl_context.verify_mode = ssl.CERT_NONE
        vcenter = SmartConnect(
            host=host, user=user, pwd=password, port=port, sslContext=ssl_context
        )

    atexit.register(Disconnect, vcenter)

    return vcenter


def retrieve_properties(content, filter_spec_set, max_objects=None):
    """Retrieve properties from a vCenter in an efficient manner.

    :param content: Service content from vcenter.RetrieveContent() call
    :param max_objects: An optional maximum number of objects to return in
                        in a single page
    :returns: Array of Object Content
    """
    options = vmodl.query.PropertyCollector.RetrieveOptions(maxObjects=max_objects)

    retrieve_properties_ex = content.propertyCollector.RetrievePropertiesEx
    continue_retrieve_properties_ex = (
        content.propertyCollector.ContinueRetrievePropertiesEx
    )

    objects = []

    result = retrieve_properties_ex(specSet=filter_spec_set, options=options)
    while result is not None:
        objects.extend(result.objects)

        token = result.token
        if token is None:
            break

        result = continue_retrieve_properties_ex(token)

    return objects


class HostRawFacts:  # pylint: disable=too-few-public-methods
    """Constants of vcenter hosts raw facts."""

    CLUSTER = "host.cluster"
    CPU_CORES = "host.cpu_cores"
    CPU_COUNT = "host.cpu_count"
    CPU_THREADS = "host.cpu_threads"
    DATACENTER = "host.datacenter"
    NAME = "host.name"
    UUID = "host.uuid"


class VcenterRawFacts:  # pylint: disable=too-few-public-methods
    """Constants of vcenter raw facts."""

    CLUSTER = "vm.cluster"
    CPU_COUNT = "vm.cpu_count"
    DATACENTER = "vm.datacenter"
    DNS_NAME = "vm.dns_name"
    HOST_CPU_CORES = "vm.host.cpu_cores"
    HOST_CPU_COUNT = "vm.host.cpu_count"
    HOST_CPU_THREADS = "vm.host.cpu_threads"
    HOST_NAME = "vm.host.name"
    HOST_UUID = "vm.host.uuid"
    IP_ADDRESSES = "vm.ip_addresses"
    LAST_CHECK_IN = "vm.last_check_in"
    MAC_ADDRESSES = "vm.mac_addresses"
    MEMORY_SIZE = "vm.memory_size"
    NAME = "vm.name"
    OS = "vm.os"
    STATE = "vm.state"
    TEMPLATE = "vm.is_template"
    UUID = "vm.uuid"


class ClusterRawFacts:  # pylint: disable=too-few-public-methods
    """Constants of vcenter cluster raw facts."""

    DATACENTER = "cluster.datacenter"
    NAME = "cluster.name"


def raw_facts_template():
    """Results template for fact collection on Vcenter scans."""
    template = {}
    for attr_name, fact_name in VcenterRawFacts.__dict__.items():
        if not attr_name.startswith("_"):
            template[fact_name] = None
    return template
