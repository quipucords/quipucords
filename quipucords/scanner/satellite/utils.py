"""Utilities used for Satellite operations."""

import logging

import requests
from django.conf import settings
from rest_framework import status as codes

from api.vault import decrypt_data_as_unicode
from scanner.satellite.exceptions import SatelliteAuthError, SatelliteError

logger = logging.getLogger(__name__)

# Disable warnings for satellite requests
requests.packages.urllib3.disable_warnings()

SATELLITE_VERSION_6 = "6"


def get_credential(scan_task):
    """Extract the credential from the scan task.

    :param scan_task: The scan tasks
    :returns: A credential
    """
    return scan_task.source.credentials.all().first()


def get_connect_data(scan_task):
    """Extract the connection information from the scan task.

    :param scan_task: The scan tasks
    :returns: A tuple of (host, port, user, password)
    """
    credential = get_credential(scan_task)
    user = credential.username
    password = decrypt_data_as_unicode(credential.password)
    host = scan_task.source.get_hosts()[0]
    port = scan_task.source.port
    return (host, port, user, password)


def construct_url(url, sat_host, port="443", org_id=None, host_id=None):
    """Create a formatted url with the given parameters.

    :param url: A url string with placeholders for parameters
    :param sat_host: The hostname or ip of Satellite to format the urls
    :param port: The port of the Satellite server (default is 443)
    :param org_id: The organization id being queried
    :param host_id: The identifier of a satellite host
    :returns: A formatted url strings
    """
    return url.format(sat_host=sat_host, port=port, org_id=org_id, host_id=host_id)


def execute_request(  # noqa: PLR0913
    scan_task, url, org_id=None, host_id=None, query_params=None, options=None
):
    """Execute a request to the Satellite server.

    :param scan_task: The scan task
    :param url: A url string with placeholders for parameters
    :param org_id: The organization id being queried
    :param host_id: The identifier of a satellite host
    :param query_params: A dictionary to use for query_params in the url
    :param options: A dictionary containing the values for ssl_cert_verify,
        host, port, user, and password.
    :returns: The response object
    :throws: Timeout
    """
    if options:
        ssl_verify = options.get("ssl_cert_verify")
        host = options.get("host")
        port = options.get("port")
        user = options.get("user")
        password = options.get("password")
    else:
        ssl_verify = scan_task.source.ssl_cert_verify
        if ssl_verify is None:
            ssl_verify = True
        host, port, user, password = get_connect_data(scan_task)
    url = construct_url(url, host, port, org_id, host_id)

    connect_timeout = settings.QUIPUCORDS_SSH_CONNECT_TIMEOUT
    inspect_timeout = settings.QUIPUCORDS_SSH_INSPECT_TIMEOUT

    response = requests.get(
        url,
        auth=(user, password),
        timeout=(connect_timeout, inspect_timeout),
        params=query_params,
        verify=ssl_verify,
    )
    return response, url


def status(scan_task):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :returns: tuple (status_code, api_version or None, satellite_version)
    """
    try:
        return _status6(scan_task)
    except SatelliteError as error:
        message = (
            "Satellite 6 status check failed with error:"
            f' "{error}". Attempting Satellite 5.'
        )
        scan_task.log_message(message)
    return None, None, None


def _status6(scan_task):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :returns: tuple (status_code, api_version or None)
    """
    status_url = "https://{sat_host}:{port}/api/status"
    response, url = execute_request(scan_task, status_url)
    status_code = response.status_code
    api_version = None

    if status_code == codes.HTTP_200_OK:
        status_data = response.json()
        api_version = status_data.get("api_version")
    elif status_code == codes.HTTP_401_UNAUTHORIZED:
        err_msg = "Unable to authenticate against " + url
        raise SatelliteAuthError(err_msg)
    else:
        err_msg = (
            "Failure while attempting Satellite 6"
            f" status check at {url} for task {scan_task.id}"
            f" with status code {status_code}."
        )
        raise SatelliteError(err_msg)
    return (status_code, api_version, SATELLITE_VERSION_6)


def data_map(mapping_dict, data):
    """Map data keys to new output.

    :param mapping_dict: dictionary of key value mappings
    :param data: Endpoint response data
    :returns: mapped data dictionary
    """
    out = {}
    if data:
        for key, mapping_key in mapping_dict.items():
            out[key] = data.get(mapping_key)
    return out


def validate_task_stats(task):
    """Map data keys to new output.

    :param task: ScanTask to evaluate
    :throws: SatelliteException if task stats are not valid
    """
    (systems_count, systems_scanned, systems_failed, systems_unreachable) = (
        task.systems_count,
        task.systems_scanned,
        task.systems_failed,
        task.systems_unreachable,
    )
    totals = systems_scanned + systems_failed + systems_unreachable
    if totals != systems_count:
        missing_sys = systems_count - totals
        error = f"Scan failed to inspect {missing_sys:d} systems."
        task.log_message(error, log_level=logging.ERROR)
        new_failed = missing_sys + systems_failed
        task.update_stats("Missed failed systems", sys_failed=new_failed)
        raise SatelliteError("hosts_facts could not scan all systems")


def raw_facts_template():
    """Results template for fact collection on Satellite scans."""
    satellite_raw_facts = (
        "architecture",
        "cores",
        "errata_out_of_date",
        "hostname",
        "ip_addresses",
        "is_virtualized",
        "katello_agent_installed",
        "kernel_version",
        "last_checkin_time",
        "location",
        "mac_addresses",
        "num_sockets",
        "os_name",
        "os_release",
        "os_version",
        "packages_out_of_date",
        "registration_time",
        "uuid",
        "virt_type",
    )
    return {fact_name: None for fact_name in satellite_raw_facts}
