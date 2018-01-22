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
import requests
from scanner.satellite.api import SatelliteInterface, SatelliteException
from scanner.satellite import utils


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class SatelliteSixV1(SatelliteInterface):
    """Interact with Satellite 6, API version 1."""

    def __init__(self, scan_task, conn_result):
        """Set context for Satellite Interface.

        :param scan_task: the scan task model for this task
        :param conn_result: The connection result
        """
        super().__init__(scan_task, conn_result)
        self.orgs = None

    def get_orgs(self):
        """Get the organization ids.

        :returns: List of organization ids
        """
        if self.orgs:
            return self.orgs

        orgs = []
        orgs_url = 'https://{sat_host}:{port}/katello/api/v2/organizations'
        jsonresult = {}
        page = 0
        per_page = 100
        while (page == 0 or int(jsonresult.get('per_page', 0)) ==
               len(jsonresult.get('results', []))):
            page += 1
            params = {'page': page, 'per_page': per_page, 'thin': '1'}
            response, url = utils.execute_request(self.scan_task,
                                                  orgs_url, params)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                raise SatelliteException('Invalid response code %s'
                                         ' for url: %s' %
                                         (response.status_code, url))
            jsonresult = response.json()
            for result in jsonresult.get('results', []):
                org_id = result.get('id')
                if org_id is not None:
                    orgs.append(org_id)
        self.orgs = orgs
        return self.orgs

    def host_count(self):
        """Obtain the count of managed hosts."""
        systems_count = 0
        orgs = self.get_orgs()
        for org_id in orgs:
            hosts_url = 'https://{sat_host}:{port}/katello/api' \
                '/v2/organizations/{org_id}/systems'
            params = {'page': 1, 'per_page': 10, 'thin': '1'}
            response, url = utils.execute_request(self.scan_task,
                                                  url=hosts_url,
                                                  org_id=org_id,
                                                  query_params=params)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                raise SatelliteException('Invalid response code %s'
                                         ' for url: %s' %
                                         (response.status_code, url))
            systems_count += response.json().get('total', 0)
        self.initialize_stats(systems_count)
        return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        orgs = self.get_orgs()
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        hosts = []
        for org_id in orgs:
            jsonresult = {}
            page = 0
            per_page = 100
            credential = utils.get_credential(self.scan_task)
            while (page == 0 or int(jsonresult.get('per_page', 0)) ==
                   len(jsonresult.get('results', []))):
                page += 1
                params = {'page': page, 'per_page': per_page, 'thin': '1'}
                response, url = utils.execute_request(self.scan_task,
                                                      url=hosts_url,
                                                      org_id=org_id,
                                                      query_params=params)
                # pylint: disable=no-member
                if response.status_code != requests.codes.ok:
                    raise SatelliteException('Invalid response code %s'
                                             ' for url: %s' %
                                             (response.status_code, url))
                jsonresult = response.json()
                for result in jsonresult.get('results', []):
                    name = result.get('name')
                    if name is not None:
                        hosts.append(name)
                        self.record_result(name, credential)

        return hosts


class SatelliteSixV2(SatelliteInterface):
    """Interact with Satellite 6, API version 2."""

    def host_count(self):
        """Obtain the count of managed hosts."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        params = {'page': 1, 'per_page': 10, 'thin': '1'}
        response, url = utils.execute_request(self.scan_task,
                                              url=hosts_url,
                                              query_params=params)
        # pylint: disable=no-member
        if response.status_code != requests.codes.ok:
            raise SatelliteException('Invalid response code %s for url: %s' %
                                     (response.status_code, url))
        systems_count = response.json().get('total', 0)
        self.initialize_stats(systems_count)
        return systems_count

    def hosts(self):
        """Obtain the managed hosts."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        hosts = []
        jsonresult = {}
        page = 0
        per_page = 100
        credential = utils.get_credential(self.scan_task)
        while (page == 0 or int(jsonresult.get('per_page', 0)) ==
               len(jsonresult.get('results', []))):
            page += 1
            params = {'page': page, 'per_page': per_page, 'thin': '1'}
            response, url = utils.execute_request(self.scan_task,
                                                  url=hosts_url,
                                                  query_params=params)
            # pylint: disable=no-member
            if response.status_code != requests.codes.ok:
                raise SatelliteException('Invalid response code %s'
                                         ' for url: %s' %
                                         (response.status_code, url))
            jsonresult = response.json()
            for result in jsonresult.get('results', []):
                name = result.get('name')
                if name is not None:
                    hosts.append(name)
                    self.record_result(name, credential)

        return hosts
