# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Extends pytest-docker-tools wrappers with helpers for qpc tests."""

import logging
from abc import ABCMeta, abstractmethod

from pytest_docker_tools import wrappers
from requests.exceptions import RequestException

from tests.constants import POSTGRES_USER
from tests.utils.http import BaseUrlClient

SYSTEMCTL_ACTIVE_STATUS_STRING = "Active: active (running)"


class ReadinessProbeMixin(metaclass=ABCMeta):
    """Container wrapper mixin with a readiness_probe hook."""

    @abstractmethod
    def readiness_probe(self):
        """
        Return True if the application is ready.

        Must be implemented on child classes.
        """

    def ready(self):
        """Overload docker-py ready including readiness probe."""
        if super().ready():
            return self.readiness_probe()
        return False


class ScanTargetContainer(ReadinessProbeMixin, wrappers.Container):
    """Container wrapper for scan target container."""

    def readiness_probe(self):
        """Return true if ssh daemon is up and running."""
        ssh_daemon_status = self.exec_run("systemctl status sshd")
        return SYSTEMCTL_ACTIVE_STATUS_STRING in ssh_daemon_status.output.decode()


class PostgresContainer(ReadinessProbeMixin, wrappers.Container):
    """Container wrapper for Postgres container."""

    def readiness_probe(self):
        """Return true when the database is ready to accept connections."""
        pg_isready_command = self.exec_run(f"pg_isready -U {POSTGRES_USER}")
        return pg_isready_command.exit_code == 0


class QuipucordsContainer(ReadinessProbeMixin, wrappers.Container):
    """Container wrapper for quipucords container."""

    @property
    def server_url(self):
        """Quipucords public url."""
        ip_address, port = self.get_addr("443/tcp")
        return f"https://{ip_address}:{port}"

    def readiness_probe(self):
        """Return true if quipucords api is responsive."""
        client = BaseUrlClient(base_url=self.server_url)
        try:
            response = client.get("api/v1/status/")
        except RequestException:
            logging.critical("Failed if container is ready. See container logs below.")
            logging.critical(self.logs())
            raise
        return response.ok
