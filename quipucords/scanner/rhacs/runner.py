"""ABC scan task runner for RHACS scanner."""

from abc import ABCMeta
from functools import cached_property

from api.models import ScanJob, ScanTask
from api.vault import decrypt_data_as_unicode
from scanner.rhacs.api import RHACSApi
from scanner.runner import ScanTaskRunner


class RHACSTaskRunner(ScanTaskRunner, metaclass=ABCMeta):
    """Specialized ScanTaskRunner for RHACS scanner."""

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
        Get connection info for RHACSApi.

        :param scan_task: The ScanTask with source/credentials to extract connection
         info.
        :returns: A dictionary that can be passed as kwargs to
         `RHACSApi.from_connection_info`
        """
        host = scan_task.source.get_hosts()[0]
        port = scan_task.source.port
        ssl_enabled, ssl_verify = scan_task.source.get_ssl_options()
        credential = scan_task.source.single_credential
        proxy_url = scan_task.source.proxy_url
        return {
            "host": host,
            "auth_token": decrypt_data_as_unicode(credential.auth_token),
            "port": port,
            "protocol": "https" if ssl_enabled else "http",
            "ssl_verify": ssl_verify,
            "proxy_url": proxy_url,
        }

    @classmethod
    def get_client(cls, scan_task: ScanTask) -> RHACSApi:
        """
        Get an RHACSApi properly initialized with source/credential info.

        :param scan_task: ScanTask for which we're creating the client
        """
        ocp_kwargs = cls._get_connection_info(scan_task)
        return RHACSApi.from_connection_info(**ocp_kwargs)
