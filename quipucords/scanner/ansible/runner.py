"""abc scan task runner for ansible scanner."""

from abc import ABCMeta
from functools import cached_property

from api.models import ScanJob, ScanTask
from api.vault import decrypt_data_as_unicode
from scanner.ansible.api import AnsibleControllerApi
from scanner.runner import ScanTaskRunner


class AnsibleTaskRunner(ScanTaskRunner, metaclass=ABCMeta):
    """Specialized ScanTaskRunner for Ansible Controller scanner."""

    def __init__(self, scan_job: ScanJob, scan_task: ScanTask):
        """Initialize class."""
        super().__init__(scan_job, scan_task)
        self.client = self.get_client(self.scan_task)

    @cached_property
    def system_name(self):
        """Returns the system name of the scan."""
        return self.scan_task.source.get_hosts()[0]

    @property
    def success_message(self):
        """Returns a message to be displayed when the task completes successfully."""
        return f"Task '{self.__class__.__name__}' completed!"

    @property
    def failure_message(self):
        """Return a message to be displayed in case of failure."""
        return f"Task '{self.__class__.__name__}' failed!"

    @classmethod
    def _get_connection_info(cls, scan_task: ScanTask):
        """
        Get connection info for AnsibleControllerApi.

        :param scan_task: The ScanTask with source/credentials to extract connection
         info.
        :returns: A dictionary that can be passed as kwargs to
         `AnsibleControllerApi.from_connection_info`
        """
        host = scan_task.source.get_hosts()[0]
        port = scan_task.source.port
        ssl_enabled, ssl_verify = scan_task.source.get_ssl_options()
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
        """
        Get an AnsibleControllerApi properly initialized with source/credential info.

        :param scan_task: ScanTask for which we're creating the client
        """
        ocp_kwargs = cls._get_connection_info(scan_task)
        return AnsibleControllerApi.from_connection_info(**ocp_kwargs)
