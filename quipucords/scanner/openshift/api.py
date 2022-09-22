# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Abstraction for retrieving data from OpenShift/Kubernetes API."""
from functools import cached_property, wraps
from kubernetes.client import (
    ApiClient,
    ApiException,
    Configuration,
    CoreV1Api,
)


class OpenShiftApi:
    """OpenShift interface for Quipucords."""

    def __init__(self, configuration: Configuration):
        """Initialize OpenShiftApi."""
        self._api_client = ApiClient(configuration=configuration)

    @classmethod
    def from_auth_token(cls, *, host, protocol, port, auth_token):
        """Initialize OpenShiftApi with auth token."""
        kube_config_object = Configuration(
            host=f"{protocol}://{host}:{port}",
            api_key={"authorization": f"bearer {auth_token}"},
        )
        return cls(configuration=kube_config_object)

    def can_connect(self):
        """Check if it's possible to connect to OCP host."""
        try:
            # call a lightweight endpoint just to check if we can
            # stablish a connection
            self._core_api.get_api_resources()
        except ApiException as err:
            logger.exception("Unable to connect to OCP/K8S api (status=%s)", err.status)
            return False
        return True

    @cached_property
    def _core_api(self):
        return CoreV1Api(api_client=self._api_client)
