# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""
pytest config for quipucords.

IMPORTANT: Don't import aplication code on toplevel as this can influence
the proper patching.
"""
# pylint: disable=import-outside-toplevel
from urllib.parse import urljoin

import pytest

from tests.utils.http import BaseUrlClient


@pytest.fixture(autouse=True)
def scan_manager(mocker):
    """return a DummyScanManager instance."""
    # pylint: disable=protected-access
    from tests.dummy_scan_manager import DummyScanManager

    _manager = DummyScanManager()
    mocker.patch("scanner.manager.Manager", DummyScanManager)
    mocker.patch("scanner.manager.SCAN_MANAGER", _manager)
    yield _manager
    for job in _manager._queue:
        job.kill()
    _manager._queue = []


@pytest.fixture(scope="session")
def django_client(live_server):
    """HTTP client which connects to django live server."""
    client = BaseUrlClient(
        base_url=urljoin(live_server.url, "api/v1/"),
    )
    return client
