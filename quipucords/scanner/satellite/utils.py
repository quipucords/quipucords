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

from api.vault import decrypt_data_as_unicode

import requests

from rest_framework import status as codes

from scanner.satellite.api import (SATELLITE_VERSION_5,
                                   SATELLITE_VERSION_6,
                                   SatelliteAuthException,
                                   SatelliteException)

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


def status(scan_task):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :returns: tuple (status_code, api_version or None, satellite_version)
    """
    try:
        return _status5(scan_task)
    except SatelliteException as sat_error:
        message = 'Satellite 5 status check failed with error:' \
            ' %s.' % sat_error
        scan_task.log_message(message, log_level=logging.ERROR)
    except xmlrpc.client.ProtocolError:
        message = 'Satellite 5 status check endpoint not found. '\
            'Attempting Satellite 6.'
        scan_task.log_message(message)

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
        invalid_auth = 'Either the password or username is incorrect.'
        if invalid_auth in str(xml_error):
            raise SatelliteAuthException(str(xml_error))
        else:
            raise SatelliteException(str(xml_error))
    except xmlrpc.client.ProtocolError as protocol_error:
        if protocol_error.errcode == codes.HTTP_404_NOT_FOUND:
            raise protocol_error
        raise SatelliteException(str(protocol_error))

    api_version = SATELLITE_VERSION_5
    status_code = codes.HTTP_200_OK  # pylint: disable=no-member
    return (status_code, api_version, SATELLITE_VERSION_5)


def _status6(scan_task):
    """Check Satellite status to get api_version and connectivity.

    :param scan_task: The scan task
    :returns: tuple (status_code, api_version or None)
    """
    status_url = 'https://{sat_host}:{port}/api/status'
    response, url = execute_request(scan_task, status_url)
    status_code = response.status_code
    api_version = None

    if status_code == codes.HTTP_200_OK:
        status_data = response.json()
        api_version = status_data.get('api_version')
    elif status_code == codes.HTTP_401_UNAUTHORIZED:
        err_msg = 'Unable to authenticate against ' + url
        raise SatelliteAuthException(err_msg)
    else:
        err_msg = 'Failure while attempting Satellite 6'
        ' status check at {} for task {} with status code {}.'.format(
            url, scan_task.id, status_code)
        raise SatelliteException(err_msg)
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
    systems_count,\
        systems_scanned, \
        systems_failed, \
        systems_unreachable = task.calculate_counts()
    totals = + systems_scanned + systems_failed + systems_unreachable
    if totals != systems_count:
        missing_sys = systems_count - totals
        error = 'Scan failed to inspect %d systems.' % missing_sys
        task.log_message(error, log_level=logging.ERROR)
        new_failed = missing_sys + systems_failed
        task.update_stats(
            'Missed failed systems', sys_failed=new_failed)
        raise SatelliteException(
            'hosts_facts could not scan all systems')
