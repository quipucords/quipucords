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
"""Utilities used for Satellite operations."""

import logging
import ssl
import xmlrpc.client
import requests
from api.vault import decrypt_data_as_unicode
from api.models import SourceOptions
from scanner.satellite.api import SatelliteException

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Disable warnings for satellite requests
requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


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


def get_sat5_client(scan_task):
    """Create xmlrpc client and credential for Satellite 5.

    :param scan_task: The scan tasks
    :returns: A tuple of (client, user, password)
    """
    source_options = scan_task.source.options
    ssl_verify = True
    if source_options:
        ssl_verify = source_options.ssl_cert_verify
    host, port, user, password = get_connect_data(scan_task)

    ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
    if ssl_verify is False:
        ssl_context.verify_mode = ssl.CERT_NONE

    rpc_url_template = 'https://{sat_host}:{port}/rpc/api'
    rpc_url = construct_url(rpc_url_template, sat_host=host, port=port)
    client = xmlrpc.client.ServerProxy(uri=rpc_url,
                                       context=ssl_context,
                                       use_builtin_types=True,
                                       allow_none=True,
                                       use_datetime=True)
    return (client, user, password)


def construct_url(url, sat_host, port='443', org_id=None, host_id=None):
    """Create a formatted url with the given parameters.

    :param url: A url string with placeholders for parameters
    :param sat_host: The hostname or ip of Satellite to format the urls
    :param port: The port of the Satellite server (default is 443)
    :param org_id: The organization id being queried
    :param host_id: The identifier of a satellite host
    :returns: A formatted url strings
    """
    return url.format(sat_host=sat_host, port=port,
                      org_id=org_id, host_id=host_id)


def execute_request(scan_task, url, org_id=None, host_id=None,
                    query_params=None):
    """Execute a request to the Satellite server.

    :param scan_task: The scan task
    :param url: A url string with placeholders for parameters
    :param org_id: The organization id being queried
    :param host_id: The identifier of a satellite host
    :param query_params: A dictionary to use for query_params in the url
    :returns: The response object
    """
    source_options = scan_task.source.options
    ssl_verify = True
    if source_options:
        ssl_verify = source_options.ssl_cert_verify
    host, port, user, password = get_connect_data(scan_task)
    url = construct_url(url, host, port, org_id, host_id)
    response = requests.get(url, auth=(user, password),
                            params=query_params, verify=ssl_verify)
    return response, url


def status(scan_task, satellite_version):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :param satellite_version: The version of satellite
    :returns: tuple (status_code, api_version or None)
    """
    if satellite_version == SourceOptions.SATELLITE_VERSION_5:
        return _status5(scan_task)

    return _status6(scan_task)


def _status5(scan_task):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :returns: tuple (status_code, api_version or None)
    """
    client, user, password = get_sat5_client(scan_task)
    try:
        key = client.auth.login(user, password)
        client.auth.logout(key)
    except xmlrpc.client.Fault as xml_error:
        raise SatelliteException(str(xml_error))

    api_version = SourceOptions.SATELLITE_VERSION_5
    status_code = requests.codes.ok  # pylint: disable=no-member
    return (status_code, api_version)


def _status6(scan_task):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :returns: tuple (status_code, api_version or None)
    """
    status_url = 'https://{sat_host}:{port}/api/status'
    response, url = execute_request(scan_task, status_url)
    status_code = response.status_code
    api_version = None
    if status_code == requests.codes.ok:  # pylint: disable=no-member
        status_data = response.json()
        api_version = status_data.get('api_version')
    else:
        logger.error('Failure while obtaining Satellite status %s for %s. %s',
                     url, scan_task, response.json())
    return (status_code, api_version)


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
