# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test constants."""

from __future__ import annotations

from pathlib import Path

from tests.env import BaseURI, EnvVar, as_bool

PROJECT_ROOT_DIR = Path(__file__).absolute().parent.parent.parent

CLEANUP_DOCKER_LAYERS = False
POSTGRES_DB = "qpc-db"
POSTGRES_PASSWORD = "qpc"
POSTGRES_USER = "qpc"
QPC_ANSIBLE_LOG_LEVEL = "0"
QPC_COMMIT = "test-commit"
QPC_SERVER_PASSWORD = "test-password"
QPC_SERVER_USERNAME = "test-username"
QUIPUCORDS_LOG_LEVEL = "INFO"
QUIPUCORDS_MANAGER_HEARTBEAT = 1
READINESS_TIMEOUT_SECONDS = 60
SCAN_TARGET_PASSWORD = "super-secret-password"
SCAN_TARGET_SSH_PORT = "2222"
SCAN_TARGET_USERNAME = "non-root-user"


class ConstantsFromEnv:
    """
    Constants from env vars.

    Environment variable names match the attribute name.
    """

    TEST_OCP_AUTH_TOKEN = EnvVar("<AUTH_TOKEN>")
    TEST_OCP_SSL_VERIFY = EnvVar("true", as_bool)
    TEST_OCP_URI = EnvVar("https://fake.ocp.host:9872", BaseURI)
