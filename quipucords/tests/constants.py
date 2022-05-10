# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test constants."""

from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).absolute().parent.parent.parent

POSTGRES_DB = "qpc-db"
POSTGRES_PASSWORD = "qpc"
POSTGRES_USER = "qpc"
QPC_COMMIT = "test-commit"
QPC_SERVER_PASSWORD = "test-password"
QPC_SERVER_USERNAME = "test-username"
READINESS_TIMEOUT_SECONDS = 60
SCAN_TARGET_PASSWORD = "super-secret-password"
SCAN_TARGET_SSH_PORT = "2222"
SCAN_TARGET_USERNAME = "non-root-user"
CLEANUP_DOCKER_LAYERS = False
