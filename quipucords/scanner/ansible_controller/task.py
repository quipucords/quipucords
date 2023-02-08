from abc import ABCMeta
from functools import cached_property

from api.models import ScanTask
from api.vault import decrypt_data_as_unicode
from scanner.ansible_controller.api import AnsibleControllerApi
from scanner.task import ScanTaskRunner


class AnsibleControllerTaskRunner(ScanTaskRunner, metaclass=ABCMeta):
    @cached_property
    def system_name(self):
        return self.scan_task.source.get_hosts()[0]

    @property
    def success_message(self):
        return f"Task '{self.__class__.__name__}' completed!"

    @property
    def failure_message(self):
        return f"Task '{self.__class__.__name__}' failed!"

    @classmethod
    def _get_connection_info(cls, scan_task: ScanTask):
        host = scan_task.source.get_hosts()[0]
        port = scan_task.source.port
        ssl_enabled, ssl_verify = cls._ssl_options(scan_task)
        credential = scan_task.source.single_credential
        return {
            "host": host,
            "password": decrypt_data_as_unicode(credential.password),
            "port": port,
            "protocol": "https" if ssl_enabled else "http",
            "ssl_verify": ssl_verify,
            "username": credential.username,
        }

    @classmethod
    def get_client(cls, scan_task: ScanTask) -> AnsibleControllerApi:
        """Get an OpenShiftApi properly initialized with source/credential info."""
        ocp_kwargs = cls._get_connection_info(scan_task)
        return AnsibleControllerApi.from_connection_info(**ocp_kwargs)

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
