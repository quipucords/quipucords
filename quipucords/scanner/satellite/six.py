"""Satellite 6 API handlers."""
from __future__ import annotations

import itertools
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Generator
from functools import partial

import requests
from more_itertools import unique_everseen
from requests.exceptions import Timeout

from api.models import ScanTask, SystemInspectionResult
from scanner.satellite import utils
from scanner.satellite.api import SatelliteException, SatelliteInterface
from scanner.satellite.utils import raw_facts_template

logger = logging.getLogger(__name__)

CONTENT_TYPE = "content-type"
APP_JSON = "application/json"
PER_PAGE = "per_page"
PAGE = "page"
THIN = "thin"
RESULTS = "results"
ID = "id"
NAME = "name"
OS_NAME = "os_name"
OS_VERSION = "os_version"
OS_RELEASE = "os_release"
SUBSCRIPTION_FACET = "subscription_facet_attributes"
CONTENT_FACET = "content_facet_attributes"
FACTS = "facts"
ERRATA_COUNTS = "errata_counts"
NUM_VIRTUAL_GUESTS = "num_virtual_guests"
VIRTUAL = "virtual"
VIRTUAL_HOST = "virtual_host"
VIRTUAL_GUESTS = "virtual_guests"
HYPERVISOR = "hypervisor"
LOCATION = "location"
LOCATION_NAME = "location_name"

NET_INTER_PERIOD = "net.interface."
NET_INTER_COLON = "net::interface::"
NET_INTER_LO_PERIOD = "net.interface.lo."
NET_INTER_LO_COLON = "net::interface::lo::"
IPV4_PERIOD = ".ipv4_address"
IPV4_COLON = "::ipv4_address"
MAC_PERIOD = ".mac_address"
MAC_COLON = "::mac_address"
IP_ADDRESSES = "ip_addresses"
MAC_ADDRESSES = "mac_addresses"

DERIVED_ENTITLEMENT = "derived_entitlement"
ENTITLEMENT_DERIVED_LIST = ["ENTITLEMENT_DERIVED", "STACK_DERIVED"]
ORGANIZATION = "organization"
PRODUCT_NAME = "product_name"
AMOUNT = "amount"
QUANTITY_CONSUMED = "quantity_consumed"
ACCOUNT_NUMBER = "account_number"
CONTRACT_NUMBER = "contract_number"
START_DATE = "start_date"
END_DATE = "end_date"
ENTITLEMENT_TYPE = "type"
ENTITLEMENTS = "entitlements"

ORGS_V1_URL = "https://{sat_host}:{port}/katello/api/v2/organizations"
HOSTS_V1_URL = "https://{sat_host}:{port}/katello/api/v2/organizations/{org_id}/systems"
HOSTS_FIELDS_V1_URL = (
    "https://{sat_host}:{port}/katello/api"
    "/v2/organizations/{org_id}/systems/{host_id}"
)
HOSTS_SUBS_V1_URL = (
    "https://{sat_host}:{port}/katello/api"
    "/v2/organizations/{org_id}/systems/{host_id}/subscriptions"
)
HOSTS_V2_URL = "https://{sat_host}:{port}/api/v2/hosts"
HOSTS_FIELDS_V2_URL = "https://{sat_host}:{port}/api/v2/hosts/{host_id}"
HOSTS_SUBS_V2_URL = "https://{sat_host}:{port}/api/v2/hosts/{host_id}/subscriptions"

QUERY_PARAMS_FIELDS = {"fields": "full"}

FIELDS_MAPPING = {
    "uuid": "uuid",
    "hostname": "name",
    "registered_by": "registered_by",
    "registration_time": "created",
    "last_checkin_time": "checkin_time",
    "katello_agent_installed": "katello_agent_installed",
    "os_release": "operatingsystem_name",
    "organization": "organization_name",
}

SUBS_FACET_MAPPING = {
    "uuid": "uuid",
    "registered_by": "registered_by",
    "registration_time": "registered_at",
    "last_checkin_time": "last_checkin",
}

CONTENT_FACET_MAPPING = {
    "katello_agent_installed": "katello_agent_installed",
}

FACTS_MAPPING = {
    "virt_type": "virt.host_type",
    "kernel_version": "uname.release",
    "architecture": "uname.machine",
    "is_virtualized": "virt.is_guest",
    "cores": "cpu.cpu(s)",
    "num_sockets": "cpu.cpu_socket(s)",
}

FACTS_V2_MAPPING = {
    "virt_type": "virt::host_type",
    "kernel_version": "uname::release",
    "architecture": "uname::machine",
    "is_virtualized": "virt::is_guest",
    "cores": "cpu::cpu(s)",
    "num_sockets": "cpu::cpu_socket(s)",
}

VIRTUAL_HOST_MAPPING = {
    "virtual_host_uuid": "uuid",
    "virtual_host_name": "name",
}

ERRATA_MAPPING = {
    "errata_out_of_date": "total",
    "packages_out_of_date": "total",
}


def request_results(
    scan_task: ScanTask,
    url_template: str,
    org_id=None,
    host_id=None,
    options=None,
    per_page: int = 100,
) -> Generator[dict, None, None]:
    """
    Request and yield results for the given scan_task and url_template.

    This generator yields each result individually from the response and continues to
    execute more requests and yield their results until pagination is exhausted.
    """
    for page in itertools.count(1):
        query_params = {PAGE: page, PER_PAGE: per_page, THIN: 1}
        response, url = utils.execute_request(
            scan_task,
            url=url_template,
            org_id=org_id,
            host_id=host_id,
            query_params=query_params,
            options=options,
        )
        if response.status_code != requests.codes.ok:
            raise SatelliteException(
                f"Invalid response code {response.status_code}" f" for url: {url}"
            )
        response_body = response.json()
        results = response_body.get(RESULTS, [])
        for result in results:
            yield result
        expect_more_pages = len(results) == int(response_body.get(PER_PAGE, 0))
        if not results or not expect_more_pages:
            break


def host_fields(api_version, response):
    """Obtain the fields for a given host id.

    :param api_version: The version of the Satellite api
    :param response: The response returned from the fields
        endpoint
    :returns: dictionary of facts created from response object.
    """
    fields = response
    host_info = {}
    sub_virt_host = None
    sub_virt_guest = None
    cf_errata_counts = None
    sub_facet_attributes = fields.get(SUBSCRIPTION_FACET)
    content_facet_attributes = fields.get(CONTENT_FACET)
    facts = raw_facts_template()
    facts.update(fields.get(FACTS, {}))
    virtual_host = fields.get(VIRTUAL_HOST, {})
    virtual_guests = fields.get(VIRTUAL_GUESTS)
    errata_counts = fields.get(ERRATA_COUNTS, {})

    if sub_facet_attributes:
        sub_virt_host = sub_facet_attributes.get(VIRTUAL_HOST)
        sub_virt_guest = sub_facet_attributes.get(VIRTUAL_GUESTS)
    if content_facet_attributes:
        cf_errata_counts = content_facet_attributes.get(ERRATA_COUNTS)

    host_info.update(utils.data_map(FIELDS_MAPPING, fields))
    host_info.update(utils.data_map(SUBS_FACET_MAPPING, sub_facet_attributes))
    host_info.update(utils.data_map(VIRTUAL_HOST_MAPPING, sub_virt_host))
    host_info.update(utils.data_map(CONTENT_FACET_MAPPING, content_facet_attributes))
    host_info.update(utils.data_map(ERRATA_MAPPING, cf_errata_counts))
    if api_version == 1:
        host_info.update(utils.data_map(FACTS_MAPPING, facts))
    else:
        host_info.update(utils.data_map(FACTS_V2_MAPPING, facts))
    host_info.update(utils.data_map(VIRTUAL_HOST_MAPPING, virtual_host))
    host_info.update(utils.data_map(ERRATA_MAPPING, errata_counts))

    if sub_virt_guest:
        host_info[VIRTUAL_GUESTS] = [x[NAME] for x in sub_virt_guest]
        host_info[NUM_VIRTUAL_GUESTS] = len(sub_virt_guest)

    if virtual_guests:
        host_info[VIRTUAL_GUESTS] = [x[NAME] for x in virtual_guests]
        host_info[NUM_VIRTUAL_GUESTS] = len(virtual_guests)

    if host_info.get(VIRTUAL_GUESTS):
        host_info[VIRTUAL] = HYPERVISOR

    host_info[LOCATION] = fields.get(LOCATION_NAME)

    ipv4s = []
    macs = []
    for key in facts:
        net_interface = key.startswith(NET_INTER_PERIOD) or key.startswith(
            NET_INTER_COLON
        )
        net_interface_lo = key.startswith(NET_INTER_LO_PERIOD) or key.startswith(
            NET_INTER_LO_COLON
        )
        if net_interface and not net_interface_lo:
            ipv4_addr = key.endswith(IPV4_PERIOD) or key.endswith(IPV4_COLON)
            mac_addr = key.endswith(MAC_PERIOD) or key.endswith(MAC_COLON)
            if ipv4_addr and facts[key]:
                ipv4s.append(facts[key].lower())
            if mac_addr and facts[key]:
                macs.append(facts[key].lower())

    macs = list(set(macs))
    ipv4s = list(set(ipv4s))

    host_info[IP_ADDRESSES] = ipv4s
    host_info[MAC_ADDRESSES] = macs

    os_release = host_info.get(OS_RELEASE)
    if os_release:
        os_name = os_release.split(" ")[0]
        if os_release.lower().startswith("red hat enterprise linux"):
            os_name = "Red Hat Enterprise Linux"
        elif os_release.lower().startswith("red hat"):
            os_name = "Red Hat"
        host_info[OS_NAME] = os_name
        host_info[OS_VERSION] = os_release.rsplit(" ").pop()

    host_info.pop(VIRTUAL_GUESTS, None)
    return host_info


def host_subscriptions(response):
    """Obtain the subscriptions for a given host id.

    :param response: The response json returned from the subs
        endpoint
    :returns: dictionary of facts created from response object.
    """
    entitlements = response.get(RESULTS, [])
    subscriptions = []
    for entitlement in entitlements:
        sub = {
            DERIVED_ENTITLEMENT: False,
            NAME: entitlement.get(PRODUCT_NAME),
            ACCOUNT_NUMBER: entitlement.get(ACCOUNT_NUMBER),
            CONTRACT_NUMBER: entitlement.get(CONTRACT_NUMBER),
            START_DATE: entitlement.get(START_DATE),
            END_DATE: entitlement.get(END_DATE),
        }
        amount = entitlement.get(QUANTITY_CONSUMED)
        if amount is None:
            amount = entitlement.get(AMOUNT)
        sub[AMOUNT] = amount

        entitlement_type = entitlement.get(ENTITLEMENT_TYPE)
        if entitlement_type and entitlement_type in ENTITLEMENT_DERIVED_LIST:
            sub[DERIVED_ENTITLEMENT] = True
        subscriptions.append(sub)

    subs_dict = {ENTITLEMENTS: subscriptions}
    return subs_dict


def request_host_details(
    scan_task,
    logging_options,
    host_id,
    host_name,
    fields_url,
    subs_url,
    request_options,
):
    """Execute both http responses to gather satallite data.

    :param scan_task: The current scan task
    :param logging_options: The metadata for logging
    :param host_id: The id of the host we're inspecting
    :param host_name: The name of the host we're inspecting
    :param fields_url: The sat61 or sat62 fields url
    :param subs_url: The sat61 or sat62 subs url
    :param request_options: A dictionary containing host, port,
        ssl_cert_verify, user, and password
    :returns: A dictionary containing the unique name for the host,
        the response & url for host_fields request, and the
        response & url for the host_subs request.
    """
    unique_name = f"{host_name}_{host_id}"
    host_fields_json = {}
    host_subscriptions_json = {}
    results = {}
    try:
        message = f"REQUESTING HOST DETAILS: {unique_name}"
        scan_task.log_message(message, logging.INFO, logging_options)
        host_fields_response, host_fields_url = utils.execute_request(
            scan_task,
            url=fields_url,
            org_id=None,
            host_id=host_id,
            query_params=QUERY_PARAMS_FIELDS,
            options=request_options,
        )

        if host_fields_response.status_code != requests.codes.ok:
            raise SatelliteException(
                f"Invalid response code {host_fields_response.status_code}"
                f" for url: {host_fields_url}"
            )
        host_subscriptions_response, host_subscriptions_url = utils.execute_request(
            scan_task,
            url=subs_url,
            org_id=None,
            host_id=host_id,
            options=request_options,
        )

        if host_subscriptions_response.status_code in (400, 404):
            content_type = host_subscriptions_response.headers.get(CONTENT_TYPE)
            if content_type and APP_JSON in content_type:
                message = (
                    f"Invalid status code {host_subscriptions_response.status_code}"
                    f" for url: {host_subscriptions_url}."
                    f" Response: {host_subscriptions_response.json()}"
                )
                scan_task.log_message(message, logging.WARN, logging_options)
            else:
                message = (
                    f"Invalid status code {host_subscriptions_response.status_code}"
                    f" for url: {host_subscriptions_url}."
                    " Response not JSON"
                )
                scan_task.log_message(message, logging.WARN, logging_options)
        elif host_subscriptions_response.status_code != requests.codes.ok:
            raise SatelliteException(
                f"Invalid response code {host_subscriptions_response.status_code}"
                f" for url: {host_subscriptions_url}"
            )
        system_inspection_result = SystemInspectionResult.SUCCESS
        host_fields_json = host_fields_response.json()
        host_subscriptions_json = host_subscriptions_response.json()
    except SatelliteException as sat_error:
        error_message = f"Satellite 6 unknown error encountered: {sat_error}\n"
        logger.error(error_message)
        system_inspection_result = SystemInspectionResult.FAILED
    except Timeout as timeout_error:
        error_message = f"Satellite 6 timeout error encountered: {timeout_error}\n"
        logger.error(error_message)
        system_inspection_result = SystemInspectionResult.FAILED
    results["unique_name"] = unique_name
    results["system_inspection_result"] = system_inspection_result
    results["host_fields_response"] = host_fields_json
    results["host_subscriptions_response"] = host_subscriptions_json
    return results


def process_results(self, results, api_version):
    """Process & record the responses returned from satellite requests.

    :param results: A list of responses returned from the sat endpoint.
    """
    for raw_result in results:
        name = raw_result["unique_name"]
        system_inspection_result = raw_result["system_inspection_result"]
        host_fields_response = raw_result["host_fields_response"]
        host_subscriptions_response = raw_result["host_subscriptions_response"]
        details = {}
        if system_inspection_result == SystemInspectionResult.SUCCESS:
            details.update(host_fields(api_version, host_fields_response))
            details.update(host_subscriptions(host_subscriptions_response))
            logger.debug("name=%s, host_details=%s", name, details)
        else:
            subs_dict = {ENTITLEMENTS: []}
            details.update(subs_dict)
        result = {"name": name, "details": details, "status": system_inspection_result}
        if result is not None:
            self.record_inspect_result(
                result.get("name"), result.get("details"), result.get("status")
            )


class SatelliteSix(SatelliteInterface, metaclass=ABCMeta):
    """Interact with Satellite 6."""

    HOSTS_FIELDS_URL: str
    HOSTS_SUBS_URL: str
    HOSTS_URL: str
    SATELLITE_API_VERSION: int

    def prepare_host(self, chunk):
        """Prepare each host with necessary information.

        :param chunk: A list of hosts
        :returns A list of tuples that contain information about
            each host.
        """
        host_params = [
            (
                self.inspect_scan_task,
                self._prepare_host_logging_options(),
                host.get(ID),
                host.get(NAME),
                self.HOSTS_FIELDS_URL,
                self.HOSTS_SUBS_URL,
                self._prepare_host_request_options(),
            )
            for host in chunk
        ]

        return host_params

    def _request_and_record_hosts(self, credential, org_id=None):
        """Request and record hosts for the given credential and optional org filter."""
        hosts = []
        for result in request_results(self.connect_scan_task, self.HOSTS_URL, org_id):
            host_name = result.get(NAME)
            host_id = result.get(ID)

            if host_name is not None and host_id is not None:
                unique_name = f"{host_name}_{host_id}"
                hosts.append(unique_name)
                self.record_conn_result(unique_name, credential)
        return hosts

    @abstractmethod
    def _requests_hosts_unique(self):
        """Get an iterable of all unique hosts."""

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
        systems_count = len(self.connect_scan_task.connection_result.systems.all())
        if self.inspect_scan_task is None:
            raise SatelliteException(
                "hosts_facts cannot be called for a connection scan"
            )
        self.inspect_scan_task.update_stats(
            "INITIAL SATELLITE STATS", sys_count=systems_count
        )

        hosts = self._requests_hosts_unique()

        _process_results = partial(
            process_results, self=self, api_version=self.SATELLITE_API_VERSION
        )

        self._process_hosts_using_multiprocessing(
            hosts, request_host_details, _process_results, manager_interrupt
        )

        utils.validate_task_stats(self.inspect_scan_task)


class SatelliteSixV1(SatelliteSix):
    """Interact with Satellite 6, API version 1."""

    HOSTS_FIELDS_URL: str = HOSTS_FIELDS_V1_URL
    HOSTS_SUBS_URL: str = HOSTS_SUBS_V1_URL
    HOSTS_URL: str = HOSTS_V1_URL
    SATELLITE_API_VERSION: int = 1

    def __init__(self, scan_job, scan_task):
        """Set context for Satellite Interface.

        :param scan_task: the scan task model for this task
        :param conn_result: The connection result
        :param inspect_result: The inspection result
        """
        super().__init__(scan_job, scan_task)
        self.orgs = None

    def get_orgs(self):
        """Get the organization ids.

        :returns: List of organization ids
        """
        if self.orgs:
            return self.orgs

        self.orgs = [
            result.get(ID)
            for result in request_results(self.connect_scan_task, ORGS_V1_URL)
            if result.get(ID) is not None
        ]
        return self.orgs

    def host_count(self):
        """Obtain the count of managed hosts."""
        systems_count = 0
        orgs = self.get_orgs()
        for org_id in orgs:
            params = {PAGE: 1, PER_PAGE: 100, THIN: 1}
            response, url = utils.execute_request(
                self.connect_scan_task,
                url=HOSTS_V1_URL,
                org_id=org_id,
                query_params=params,
            )
            if response.status_code != requests.codes.ok:
                raise SatelliteException(
                    f"Invalid response code {response.status_code} for url: {url}"
                )
            systems_count += response.json().get("total", 0)
            self.connect_scan_task.update_stats(
                "INITIAL SATELLITE STATS", sys_count=systems_count
            )
            return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        credential = utils.get_credential(self.connect_scan_task)

        hosts = list(
            itertools.chain.from_iterable(
                self._request_and_record_hosts(credential, org_id)
                for org_id in self.get_orgs()
            )
        )
        return hosts

    def _requests_hosts_unique(self):
        """Get an iterable of all unique hosts spanning all orgs."""
        hosts = unique_everseen(
            itertools.chain.from_iterable(
                request_results(self.inspect_scan_task, self.HOSTS_URL, org_id)
                for org_id in self.get_orgs()
            )
        )
        return hosts


class SatelliteSixV2(SatelliteSix):
    """Interact with Satellite 6, API version 2."""

    HOSTS_FIELDS_URL: str = HOSTS_FIELDS_V2_URL
    HOSTS_SUBS_URL: str = HOSTS_SUBS_V2_URL
    HOSTS_URL: str = HOSTS_V2_URL
    SATELLITE_API_VERSION: int = 2

    def host_count(self):
        """Obtain the count of managed hosts."""
        params = {PAGE: 1, PER_PAGE: 10, THIN: 1}
        response, url = utils.execute_request(
            self.connect_scan_task, url=HOSTS_V2_URL, query_params=params
        )
        if response.status_code != requests.codes.ok:
            raise SatelliteException(
                f"Invalid response code {response.status_code} for url: {url}"
            )
        systems_count = response.json().get("total", 0)
        self.connect_scan_task.update_stats(
            "INITIAL SATELLITE STATS", sys_count=systems_count
        )
        return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        credential = utils.get_credential(self.connect_scan_task)
        return self._request_and_record_hosts(credential)

    def _requests_hosts_unique(self):
        """Get an iterable of all unique hosts."""
        return unique_everseen(request_results(self.inspect_scan_task, self.HOSTS_URL))
