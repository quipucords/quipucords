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
"""Satellite 6 API handlers."""

import logging
from multiprocessing import Pool

from api.models import (ScanJob, SystemInspectionResult)

import requests

from scanner.satellite import utils
from scanner.satellite.api import (SatelliteCancelException,
                                   SatelliteException,
                                   SatelliteInterface,
                                   SatellitePauseException)


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

CONTENT_TYPE = 'content-type'
APP_JSON = 'application/json'
PER_PAGE = 'per_page'
PAGE = 'page'
THIN = 'thin'
RESULTS = 'results'
ID = 'id'
NAME = 'name'
OS_NAME = 'os_name'
OS_VERSION = 'os_version'
OS_RELEASE = 'os_release'
SUBSCRIPTION_FACET = 'subscription_facet_attributes'
CONTENT_FACET = 'content_facet_attributes'
FACTS = 'facts'
ERRATA_COUNTS = 'errata_counts'
NUM_VIRTUAL_GUESTS = 'num_virtual_guests'
VIRTUAL = 'virtual'
VIRTUAL_HOST = 'virtual_host'
VIRTUAL_GUESTS = 'virtual_guests'
HYPERVISOR = 'hypervisor'
LOCATION = 'location'
LOCATION_NAME = 'location_name'

NET_INTER_PERIOD = 'net.interface.'
NET_INTER_COLON = 'net::interface::'
NET_INTER_LO_PERIOD = 'net.interface.lo.'
NET_INTER_LO_COLON = 'net::interface::lo::'
IPV4_PERIOD = '.ipv4_address'
IPV4_COLON = '::ipv4_address'
MAC_PERIOD = '.mac_address'
MAC_COLON = '::mac_address'
IP_ADDRESSES = 'ip_addresses'
MAC_ADDRESSES = 'mac_addresses'

DERIVED_ENTITLEMENT = 'derived_entitlement'
ENTITLEMENT_DERIVED_LIST = ['ENTITLEMENT_DERIVED', 'STACK_DERIVED']
ORGANIZATION = 'organization'
PRODUCT_NAME = 'product_name'
AMOUNT = 'amount'
QUANTITY_CONSUMED = 'quantity_consumed'
ACCOUNT_NUMBER = 'account_number'
CONTRACT_NUMBER = 'contract_number'
START_DATE = 'start_date'
END_DATE = 'end_date'
ENTITLEMENT_TYPE = 'type'
ENTITLEMENTS = 'entitlements'

ORGS_V1_URL = 'https://{sat_host}:{port}/katello/api/v2/organizations'
HOSTS_V1_URL = 'https://{sat_host}:{port}/katello/api' \
    '/v2/organizations/{org_id}/systems'
HOSTS_FIELDS_V1_URL = 'https://{sat_host}:{port}/katello/api' \
    '/v2/organizations/{org_id}/systems/{host_id}'
HOSTS_SUBS_V1_URL = 'https://{sat_host}:{port}/katello/api' \
    '/v2/organizations/{org_id}/systems/{host_id}/subscriptions'
HOSTS_V2_URL = 'https://{sat_host}:{port}/api/v2/hosts'
HOSTS_FIELDS_V2_URL = 'https://{sat_host}:{port}/api/v2/hosts/{host_id}'
HOSTS_SUBS_V2_URL = 'https://{sat_host}:{port}/' \
    'api/v2/hosts/{host_id}/subscriptions'

QUERY_PARAMS_FIELDS = {'fields': 'full'}

FIELDS_MAPPING = {
    'uuid': 'uuid',
    'hostname': 'name',
    'registered_by': 'registered_by',
    'registration_time': 'created',
    'last_checkin_time': 'checkin_time',
    'katello_agent_installed': 'katello_agent_installed',
    'os_release': 'operatingsystem_name',
    'organization': 'organization_name'
}

SUBS_FACET_MAPPING = {
    'uuid': 'uuid',
    'registered_by': 'registered_by',
    'registration_time': 'registered_at',
    'last_checkin_time': 'last_checkin',
}

CONTENT_FACET_MAPPING = {
    'katello_agent_installed': 'katello_agent_installed',
}

FACTS_MAPPING = {
    'virt_type': 'virt.host_type',
    'kernel_version': 'uname.release',
    'architecture': 'uname.machine',
    'is_virtualized': 'virt.is_guest',
    'cores': 'cpu.cpu(s)',
    'num_sockets': 'cpu.cpu_socket(s)',
}

FACTS_V2_MAPPING = {
    'virt_type': 'virt::host_type',
    'kernel_version': 'uname::release',
    'architecture': 'uname::machine',
    'is_virtualized': 'virt::is_guest',
    'cores': 'cpu::cpu(s)',
    'num_sockets': 'cpu::cpu_socket(s)',
}

VIRTUAL_HOST_MAPPING = {
    'virtual_host': 'uuid',
    'virtual_host_name': 'name',
}

ERRATA_MAPPING = {
    'errata_out_of_date': 'total',
    'packages_out_of_date': 'total',
}


# pylint: disable=too-many-locals,too-many-statements,too-many-branches
def host_fields(api_version, response, url):
    """Obtain the fields for a given host id.

    :param api_version: The version of the Satellite api
    :param response: The response returned from the fields
        endpoint
    :param url: The endpoint URL
    :returns: dictionary of facts created from response object.
    """
    # pylint: disable=no-member
    if response.status_code != requests.codes.ok:
        raise SatelliteException('Invalid response code %s'
                                 ' for url: %s' %
                                 (response.status_code, url))
    fields = response.json()
    host_info = {}
    sub_virt_host = None
    sub_virt_guest = None
    cf_errata_counts = None
    sub_facet_attributes = fields.get(SUBSCRIPTION_FACET)
    content_facet_attributes = fields.get(CONTENT_FACET)
    facts = fields.get(FACTS, {})
    virtual_host = fields.get(VIRTUAL_HOST, {})
    virtual_guests = fields.get(VIRTUAL_GUESTS)
    errata_counts = fields.get(ERRATA_COUNTS, {})

    if sub_facet_attributes:
        sub_virt_host = sub_facet_attributes.get(VIRTUAL_HOST)
        sub_virt_guest = sub_facet_attributes.get(VIRTUAL_GUESTS)
    if content_facet_attributes:
        cf_errata_counts = content_facet_attributes.get(ERRATA_COUNTS)

    host_info.update(utils.data_map(FIELDS_MAPPING, fields))
    host_info.update(utils.data_map(SUBS_FACET_MAPPING,
                                    sub_facet_attributes))
    host_info.update(utils.data_map(VIRTUAL_HOST_MAPPING,
                                    sub_virt_host))
    host_info.update(utils.data_map(CONTENT_FACET_MAPPING,
                                    content_facet_attributes))
    host_info.update(utils.data_map(ERRATA_MAPPING,
                                    cf_errata_counts))
    if api_version == 1:
        host_info.update(utils.data_map(FACTS_MAPPING,
                                        facts))
    else:
        host_info.update(utils.data_map(FACTS_V2_MAPPING,
                                        facts))
    host_info.update(utils.data_map(VIRTUAL_HOST_MAPPING,
                                    virtual_host))
    host_info.update(utils.data_map(ERRATA_MAPPING,
                                    errata_counts))

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
        net_interface = (key.startswith(NET_INTER_PERIOD) or
                         key.startswith(NET_INTER_COLON))
        net_interface_lo = (key.startswith(NET_INTER_LO_PERIOD) or
                            key.startswith(NET_INTER_LO_COLON))
        if net_interface and not net_interface_lo:
            ipv4_addr = (key.endswith(IPV4_PERIOD) or
                         key.endswith(IPV4_COLON))
            mac_addr = (key.endswith(MAC_PERIOD) or
                        key.endswith(MAC_COLON))
            if ipv4_addr and facts[key]:
                ipv4s.append(facts[key])
            if mac_addr and facts[key]:
                macs.append(facts[key])
    host_info[IP_ADDRESSES] = ipv4s
    host_info[MAC_ADDRESSES] = macs

    os_release = host_info.get(OS_RELEASE)
    if os_release:
        os_name = os_release.split(' ')[0]
        if os_release.lower().startswith('red hat enterprise linux'):
            os_name = 'Red Hat Enterprise Linux'
        elif os_release.lower().startswith('red hat'):
            os_name = 'Red Hat'
        host_info[OS_NAME] = os_name
        host_info[OS_VERSION] = os_release.rsplit(' ').pop()

    host_info.pop(VIRTUAL_GUESTS, None)
    return host_info


def host_subscriptions(scan_task, response, url):
    """Obtain the subscriptions for a given host id.

    :param scan_task: The scan task being executed
    :param response: The response returned from the subs
        endpoint
    :param url: The endpoint URL
    :returns: dictionary of facts created from response object.
    """
    # pylint: disable=no-member
    if response.status_code == 400 or response.status_code == 404:
        content_type = response.headers.get(CONTENT_TYPE)
        if content_type and APP_JSON in content_type:
            message = 'Invalid status code %s for url: %s. Response: %s' %\
                (response.status_code, url, response.json())
            scan_task.log_message(message, log_level=logging.WARN)
        else:
            message = 'Invalid status code %s for url: %s. '\
                'Response not JSON' %\
                (response.status_code, url)
            scan_task.log_message(message, log_level=logging.WARN)
        subs_dict = {ENTITLEMENTS: []}
        return subs_dict
    elif response.status_code != requests.codes.ok:
        raise SatelliteException('Invalid response code %s'
                                 ' for url: %s' %
                                 (response.status_code, url))
    entitlements = response.json().get(RESULTS, [])
    subscriptons = []
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
        if (entitlement_type and
                entitlement_type in ENTITLEMENT_DERIVED_LIST):
            sub[DERIVED_ENTITLEMENT] = True
        subscriptons.append(sub)

    subs_dict = {ENTITLEMENTS: subscriptons}
    return subs_dict


def log_message(message, inspect_task_id, scan_type,
                log_level=logging.INFO):
    """Log a message for the information provided.

    :param message: A string containing the message
    :param inspect_task_id: The id of the running task
    :param scan_type: The type of scan running
        (inspect, connect)
    :param log_level: The level to log at
    """
    # elapsed_time = self._compute_elapsed_time()
    actual_message = 'Job %d (%s, elapsed_time:) - ' % \
        (inspect_task_id,
         scan_type)
    actual_message += message
    logger.log(log_level, actual_message)


# pylint: disable=too-many-arguments
def get_http_responses(scan_task, inspect_task_id,
                       scan_type, host_id, host_name,
                       fields_url, subs_url, request_options):
    """Execute both http responses to gather satallite data.

    :param scan_task: The current scan task
    :param inspect_task_id: The id of the running task
    :param scan_type: The type of scan running
        (inspect, connect)
    :param host_id: The id of the host we're inspecting
    :param host_name: The name of the host we're inspecting
    :param fields_url: The sat61 or sat62 fields url
    :param subs_url: The sat61 or sat62 subs url
    :param request_options: A dictionary containing host, port,
        ssl_cert_verify, user, and password
    :returns: A list containing the unique name for the host,
        the response & url for host_fields request, and the
        response & url for the host_subs request.
    """
    unique_name = '%s_%s' % (host_name, host_id)
    host_fields_response = None
    host_fields_url = None
    host_subscriptions_response = None
    host_subscriptions_url = None
    try:
        message = 'REQUESTING HOST DETAILS: %s' % unique_name
        log_message(message, inspect_task_id, scan_type)
        host_fields_response, host_fields_url = \
            utils.execute_request(scan_task,
                                  url=fields_url,
                                  org_id=None,
                                  host_id=host_id,
                                  query_params=QUERY_PARAMS_FIELDS,
                                  options=request_options)

        host_subscriptions_response, host_subscriptions_url = \
            utils.execute_request(scan_task,
                                  url=subs_url,
                                  org_id=None,
                                  host_id=host_id,
                                  options=request_options)
        return(unique_name, SystemInspectionResult.SUCCESS,
               (host_fields_response, host_fields_url),
               (host_subscriptions_response, host_subscriptions_url))
    except SatelliteException as sat_error:
        error_message = 'Satellite unknown 6v2 error encountered: %s\n' \
            % sat_error
        logger.error(error_message)
        return (unique_name, SystemInspectionResult.FAILED,
                (host_fields_response, host_fields_url),
                (host_subscriptions_response, host_subscriptions_url))


# pylint: disable=too-many-arguments
def post_processing_results(unique_name,
                            inspect_result_status,
                            scan_task,
                            api_version,
                            host_fields_response,
                            host_subscriptions_response):
    """Process the responses returned from the satellite requests.

    :param unique_name: The unique name for the host
    :param inspect_result_status: Whether or not the System Inspection
        result succeeded or failed
    :param scan_task: The current scan task
    :param api_version: The satellite api version
    :param host_fields_response: A tuple containing the response
        returned from the fields endpoint
    :param host_subscriptions_response: A tuple containing the response
        returned from the subs endpoint
    :returns: A dictionary containing the host name, details, and status.
    """
    details = {}
    if inspect_result_status == SystemInspectionResult.SUCCESS:
        details.update(host_fields(api_version,
                                   host_fields_response[0],
                                   host_fields_response[1]))
        details.update(host_subscriptions(scan_task,
                                          host_subscriptions_response[0],
                                          host_subscriptions_response[1]))
        logger.debug('name=%s, host_details=%s',
                     unique_name, details)
    return {'name': unique_name,
            'details': details,
            'status': inspect_result_status}


class SatelliteSixV1(SatelliteInterface):
    """Interact with Satellite 6, API version 1."""

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

        orgs = []
        jsonresult = {}
        page = 0
        per_page = 100
        while (page == 0 or int(jsonresult.get(PER_PAGE, 0)) ==
               len(jsonresult.get(RESULTS, []))):
            page += 1
            params = {PAGE: page, PER_PAGE: per_page, THIN: 1}
            response, url = utils.execute_request(self.connect_scan_task,
                                                  ORGS_V1_URL, params)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                raise SatelliteException('Invalid response code %s'
                                         ' for url: %s' %
                                         (response.status_code, url))
            jsonresult = response.json()
            for result in jsonresult.get(RESULTS, []):
                org_id = result.get(ID)
                if org_id is not None:
                    orgs.append(org_id)
        self.orgs = orgs
        return self.orgs

    def host_count(self):
        """Obtain the count of managed hosts."""
        systems_count = 0
        orgs = self.get_orgs()
        for org_id in orgs:
            params = {PAGE: 1, PER_PAGE: 100, THIN: 1}
            response, url = utils.execute_request(self.connect_scan_task,
                                                  url=HOSTS_V1_URL,
                                                  org_id=org_id,
                                                  query_params=params)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                raise SatelliteException('Invalid response code %s'
                                         ' for url: %s' %
                                         (response.status_code, url))
            systems_count += response.json().get('total', 0)
            self.connect_scan_task.update_stats(
                'INITIAL STATELLITE STATS', sys_count=systems_count)
            return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        orgs = self.get_orgs()
        hosts = []
        for org_id in orgs:
            jsonresult = {}
            page = 0
            per_page = 100
            credential = utils.get_credential(self.connect_scan_task)
            while (page == 0 or int(jsonresult.get(PER_PAGE, 0)) ==
                   len(jsonresult.get(RESULTS, []))):
                page += 1
                params = {PAGE: page, PER_PAGE: per_page, THIN: 1}
                response, url = utils.execute_request(self.connect_scan_task,
                                                      url=HOSTS_V1_URL,
                                                      org_id=org_id,
                                                      query_params=params)
                # pylint: disable=no-member
                if response.status_code != requests.codes.ok:
                    raise SatelliteException('Invalid response code %s'
                                             ' for url: %s' %
                                             (response.status_code, url))
                jsonresult = response.json()
                for result in jsonresult.get(RESULTS, []):
                    host_name = result.get(NAME)
                    host_id = result.get(ID)

                    if host_name is not None and host_id is not None:
                        unique_name = '%s_%s' % (host_name, host_id)
                        hosts.append(unique_name)
                        self.record_conn_result(unique_name, credential)

        return hosts

    def prepare_host(self, chunk):
        """Prepare each host with necessary information.

        :param chunk: A list of hosts
        :returns A list of tuples that contain information about
            each host.
        """
        if self.inspect_scan_task is None:
            raise SatelliteException(
                'host_details cannot be called for a connection scan')
        defined_host, port, user, password = utils.get_connect_data(
            self.inspect_scan_task)
        ssl_cert_verify = True
        source_options = self.inspect_scan_task.source.options
        if source_options:
            ssl_cert_verify = source_options.ssl_cert_verify
        request_options = {'host': defined_host, 'port': port, 'user': user,
                           'password': password,
                           'ssl_cert_verify': ssl_cert_verify}
        host_params = [(self.inspect_scan_task, self.inspect_scan_task.id,
                        self.inspect_scan_task.scan_type,
                        host.get(ID), host.get(NAME), HOSTS_FIELDS_V1_URL,
                        HOSTS_SUBS_V1_URL, request_options)
                       for host in chunk]

        return host_params

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
        systems_count = len(
            self.connect_scan_task.connection_result.systems.all())
        if self.inspect_scan_task is None:
            raise SatelliteException(
                'hosts_facts cannot be called for a connection scan')
        self.inspect_scan_task.update_stats(
            'INITIAL STATELLITE STATS', sys_count=systems_count)
        deduplicated_hosts = []

        # pylint: disable=too-many-nested-blocks
        with Pool(processes=self.max_concurrency) as pool:
            orgs = self.get_orgs()
            for org_id in orgs:
                jsonresult = {}
                page = 0
                per_page = 100
                while (page == 0 or int(jsonresult.get(PER_PAGE, 0)) ==
                       len(jsonresult.get(RESULTS, []))):
                    page += 1
                    params = {PAGE: page, PER_PAGE: per_page, THIN: 1}
                    response, url = \
                        utils.execute_request(self.inspect_scan_task,
                                              url=HOSTS_V1_URL,
                                              org_id=org_id,
                                              query_params=params)
                    # pylint: disable=no-member
                    if response.status_code != requests.codes.ok:
                        raise SatelliteException('Invalid response code %s'
                                                 ' for url: %s' %
                                                 (response.status_code, url))
                    jsonresult = response.json()

                    hosts_before_dedup = jsonresult.get(RESULTS, [])
                    hosts_after_dedup = []
                    for host in hosts_before_dedup:
                        if host not in deduplicated_hosts:
                            hosts_after_dedup.append(host)
                            deduplicated_hosts.append(host)
                    hosts = hosts_after_dedup
                    chunks = [hosts[i:i + self.max_concurrency]
                              for i in range(0, len(hosts),
                                             self.max_concurrency)]
                    for chunk in chunks:
                        if manager_interrupt.value == \
                                ScanJob.JOB_TERMINATE_CANCEL:
                            raise SatelliteCancelException()

                        if manager_interrupt.value == \
                                ScanJob.JOB_TERMINATE_PAUSE:
                            raise SatellitePauseException()

                        host_params = self.prepare_host(chunk)
                        results = pool.starmap(get_http_responses, host_params)
                        for each in results:
                            if each:
                                result = post_processing_results(
                                    each[0],
                                    each[1],
                                    self.inspect_scan_task,
                                    1,
                                    each[2],
                                    each[3])

                                if result is not None:
                                    self.record_inspect_result(
                                        result.get('name'),
                                        result.get('details'),
                                        result.get('status'))
        utils.validate_task_stats(self.inspect_scan_task)


class SatelliteSixV2(SatelliteInterface):
    """Interact with Satellite 6, API version 2."""

    def host_count(self):
        """Obtain the count of managed hosts."""
        params = {PAGE: 1, PER_PAGE: 10, THIN: 1}
        response, url = utils.execute_request(self.connect_scan_task,
                                              url=HOSTS_V2_URL,
                                              query_params=params)
        # pylint: disable=no-member
        if response.status_code != requests.codes.ok:
            raise SatelliteException('Invalid response code %s for url: %s' %
                                     (response.status_code, url))
        systems_count = response.json().get('total', 0)
        self.connect_scan_task.update_stats(
            'INITIAL STATELLITE STATS', sys_count=systems_count)
        return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        hosts = []
        jsonresult = {}
        page = 0
        per_page = 100
        credential = utils.get_credential(self.connect_scan_task)
        while (page == 0 or int(jsonresult.get(PER_PAGE, 0)) ==
               len(jsonresult.get(RESULTS, []))):
            page += 1
            params = {PAGE: page, PER_PAGE: per_page, THIN: 1}
            response, url = utils.execute_request(self.connect_scan_task,
                                                  url=HOSTS_V2_URL,
                                                  query_params=params)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                raise SatelliteException('Invalid response code %s'
                                         ' for url: %s' %
                                         (response.status_code, url))
            jsonresult = response.json()
            for result in jsonresult.get(RESULTS, []):
                host_name = result.get(NAME)
                host_id = result.get(ID)

                if host_name is not None and host_id is not None:
                    unique_name = '%s_%s' % (host_name, host_id)
                    hosts.append(unique_name)
                    self.record_conn_result(unique_name, credential)

        return hosts

    def prepare_host(self, chunk):
        """Prepare each host with necessary information.

        :param chunk: A list of hosts
        :returns A list of tuples that contain information about
            each host.
        """
        if self.inspect_scan_task is None:
            raise SatelliteException(
                'host_details cannot be called for a connection scan')
        defined_host, port, user, password = utils.get_connect_data(
            self.inspect_scan_task)
        ssl_cert_verify = True
        source_options = self.inspect_scan_task.source.options
        if source_options:
            ssl_cert_verify = source_options.ssl_cert_verify
        request_options = {'host': defined_host, 'port': port, 'user': user,
                           'password': password,
                           'ssl_cert_verify': ssl_cert_verify}
        host_params = [(self.inspect_scan_task, self.inspect_scan_task.id,
                        self.inspect_scan_task.scan_type,
                        host.get(ID), host.get(NAME), HOSTS_FIELDS_V2_URL,
                        HOSTS_SUBS_V2_URL, request_options)
                       for host in chunk]

        return host_params

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
        systems_count = len(
            self.connect_scan_task.connection_result.systems.all())
        if self.inspect_scan_task is None:
            raise SatelliteException(
                'hosts_facts cannot be called for a connection scan')
        self.inspect_scan_task.update_stats(
            'INITIAL STATELLITE STATS', sys_count=systems_count)
        deduplicated_hosts = []

        with Pool(processes=self.max_concurrency) as pool:
            jsonresult = {}
            page = 0
            per_page = 100
            while (page == 0 or int(jsonresult.get(PER_PAGE, 0)) ==
                   len(jsonresult.get(RESULTS, []))):
                page += 1
                params = {PAGE: page, PER_PAGE: per_page, THIN: 1}
                response, url = utils.execute_request(self.inspect_scan_task,
                                                      url=HOSTS_V2_URL,
                                                      query_params=params)
                # pylint: disable=no-member
                if response.status_code != requests.codes.ok:
                    raise SatelliteException('Invalid response code %s'
                                             ' for url: %s' %
                                             (response.status_code, url))
                jsonresult = response.json()

                hosts_before_dedup = jsonresult.get(RESULTS, [])
                hosts_after_dedup = []
                for host in hosts_before_dedup:
                    if host not in deduplicated_hosts:
                        hosts_after_dedup.append(host)
                        deduplicated_hosts.append(host)
                hosts = hosts_after_dedup
                chunks = [hosts[i:i + self.max_concurrency]
                          for i in range(0, len(hosts), self.max_concurrency)]
                for chunk in chunks:
                    if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
                        raise SatelliteCancelException()

                    if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
                        raise SatellitePauseException()
                    host_params = self.prepare_host(chunk)
                    results = pool.starmap(get_http_responses,
                                           host_params)
                    for each in results:
                        if each:
                            result = post_processing_results(
                                each[0],
                                each[1],
                                self.inspect_scan_task,
                                2,
                                each[2],
                                each[3])

                            if result is not None:
                                self.record_inspect_result(
                                    result.get('name'),
                                    result.get('details'),
                                    result.get('status'))
        utils.validate_task_stats(self.inspect_scan_task)
