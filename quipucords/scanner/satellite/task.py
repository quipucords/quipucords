"""ScanTask used for satellite connection task."""

import logging
import socket
from abc import ABCMeta, abstractmethod

from requests import exceptions

from api.models import ScanTask
from scanner.exceptions import ScanFailureError
from scanner.satellite import utils
from scanner.satellite.api import SatelliteAuthException, SatelliteException
from scanner.satellite.factory import create
from scanner.task import ScanTaskRunner


class SatelliteTaskRunner(ScanTaskRunner, metaclass=ABCMeta):
    """Genetic Satellite ScanTaskRunner."""

    EXPECTED_EXCEPTIONS = (
        SatelliteAuthException,
        SatelliteException,
        exceptions.ConnectionError,
        TimeoutError,
        socket.gaierror,
    )

    def _initialize_api_object(self):
        status_code, api_version, satellite_version = utils.status(self.scan_task)
        if status_code is None:
            error_message = self._format_error_message(
                "Unknown satellite version is not supported"
            )
            raise ScanFailureError(error_message)
        if status_code == 200:
            api = create(satellite_version, api_version, self.scan_job, self.scan_task)
            if not api:
                error_message = self._format_error_message(
                    f"Satellite version {satellite_version} with "
                    f"api version {api_version} is not supported"
                )
                raise ScanFailureError(error_message)
            return api
        raise ScanFailureError(self._format_error_message())

    def execute_task(self, manager_interrupt):
        """Scan Satellite for system connection data."""
        try:
            api = self._initialize_api_object()
            self.handle_api_calls(api, manager_interrupt)
        except self.EXPECTED_EXCEPTIONS as error:
            return self._handle_error(error)

        return None, ScanTask.COMPLETED

    @abstractmethod
    def handle_api_calls(self, api, manager_interrupt):
        """Handle specific api calls for either connect or inspect phases."""

    def _format_error_message(self, message=None):
        error_message = f"Scan failed for source {self.scan_task.source}."
        if message:
            error_message = f"{message}. {error_message}."
        return error_message

    def _handle_error(self, exception):
        self.scan_task.log_message(
            "Exception captured during task execution.",
            exception=exception,
            log_level=logging.ERROR,
        )
        error_message = self._format_error_message(
            f"Satellite error ({type(exception)}) found"
        )
        return error_message, ScanTask.FAILED
