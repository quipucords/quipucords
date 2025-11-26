"""Utilities used for VCenter operations."""

import atexit
import ssl
from urllib.parse import urlparse

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vmodl

from api.vault import decrypt_data_as_unicode


def vcenter_connect(scan_task):
    """Connect to VCenter.

    :param scan_task: The scan task
    :returns: VCenter connection object.
    """
    source = scan_task.source
    credential = source.credentials.all().first()
    user = credential.username
    host = scan_task.source.get_hosts()[0]
    password = decrypt_data_as_unicode(credential.password)
    port = scan_task.source.port
    proxy_url = scan_task.source.proxy_url

    disable_ssl = source.disable_ssl
    ssl_cert_verify = source.ssl_cert_verify
    ssl_protocol = source.get_ssl_protocol()

    proxy_host, proxy_port = None, None
    if proxy_url:
        parsed = urlparse(proxy_url)
        proxy_host = parsed.hostname
        proxy_port = parsed.port

    smart_connect_kwargs = {
        "host": host,
        "user": user,
        "pwd": password,
        "port": port,
        "httpProxyHost": proxy_host,
        "httpProxyPort": proxy_port,
    }

    if disable_ssl:
        smart_connect_kwargs["disableSslCertValidation"] = True
    elif not (ssl_protocol is None and ssl_cert_verify is None):
        ssl_context = ssl.SSLContext(
            protocol=ssl_protocol if ssl_protocol else ssl.PROTOCOL_TLS_CLIENT
        )
        if ssl_cert_verify is False:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        smart_connect_kwargs["sslContext"] = ssl_context

    vcenter = SmartConnect(**smart_connect_kwargs)
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


class HostRawFacts:
    """Constants of vcenter hosts raw facts."""

    CLUSTER = "host.cluster"
    CPU_CORES = "host.cpu_cores"
    CPU_COUNT = "host.cpu_count"
    CPU_THREADS = "host.cpu_threads"
    DATACENTER = "host.datacenter"
    NAME = "host.name"
    UUID = "host.uuid"


class VcenterRawFacts:
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


class ClusterRawFacts:
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
