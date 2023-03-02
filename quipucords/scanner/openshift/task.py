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
        ssl_enabled, ssl_verify = cls._ssl_options(scan_task)
        credential = scan_task.source.single_credential

        return {
            "host": host,
            "port": port,
            "protocol": "https" if ssl_enabled else "http",
            "auth_token": decrypt_data_as_unicode(credential.auth_token),
            "ssl_verify": ssl_verify,
        }

    @classmethod
    def get_ocp_client(cls, scan_task: ScanTask) -> OpenShiftApi:
        """Get an OpenShiftApi properly initialized with source/credential info."""
        ocp_kwargs = cls._get_connection_info(scan_task)
        return OpenShiftApi.from_auth_token(**ocp_kwargs)

    @classmethod
    def _ssl_options(cls, scan_task: ScanTask):
        """
        Get ssl related options for scan_task.

        Note: this logic should be enforced on SourceOptionsSerializer.
        Should be fixed in a subsequent PR.

        :return: ssl_enabled, ssl_verify
        :rtype: (bool, bool)
        """
        if not scan_task.source.options:
            return True, True

        ssl_enabled = not scan_task.source.options.disable_ssl
        if ssl_enabled:
            ssl_verify = getattr(scan_task.source.options, "ssl_cert_verify", True)
        else:
            ssl_verify = False
        return ssl_enabled, ssl_verify
