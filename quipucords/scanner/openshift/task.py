# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""OpenShift Base task runner."""

from abc import ABCMeta

from api.models import ScanTask
from api.vault import decrypt_data_as_unicode
from scanner.openshift.api import OpenShiftApi
from scanner.task import ScanTaskRunner


class OpenShiftTaskRunner(ScanTaskRunner, metaclass=ABCMeta):
    """Base OpenShift task runner."""

    @classmethod
    def _get_connection_info(cls, scan_task: ScanTask):
        host = scan_task.source.get_hosts()[0]
        port = scan_task.source.port
        ssl_verify = getattr(scan_task.source.options, "ssl_cert_verify", True)
        credential = scan_task.source.single_credential
        return {
            "host": host,
            "port": port,
            "protocol": "https" if ssl_verify else "http",
            "auth_token": decrypt_data_as_unicode(credential.auth_token),
        }

    @classmethod
    def get_ocp_client(cls, scan_task: ScanTask) -> OpenShiftApi:
        """Get an OpenShiftApi properly initialized with source/credential info."""
        ocp_kwargs = cls._get_connection_info(scan_task)
        return OpenShiftApi.from_auth_token(**ocp_kwargs)
