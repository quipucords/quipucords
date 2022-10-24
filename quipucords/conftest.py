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
from contextlib import suppress
from unittest.mock import patch
from urllib.parse import urljoin

import pytest

from tests.utils.http import BaseUrlClient


def _kill_scan_manager(manager_instance):
    for job in manager_instance.scan_queue:
        with suppress(AttributeError):
            job.kill()

    manager_instance.running = False
    if manager_instance.is_alive():
        manager_instance.join()


def _return_itself(instance):
    return instance


@pytest.fixture
def scan_manager():
    """
    Scan manager fixture.

    If started, ensure its proper teardown.
    """
    from scanner import manager

    scan_manager_instance = manager.Manager()
    with (
        patch.object(manager.Manager, "__call__", _return_itself),
        patch.object(manager, "sleep"),
        patch.object(manager, "SCAN_MANAGER", scan_manager_instance),
        patch("api.signal.scanjob_signal.manager.SCAN_MANAGER", scan_manager_instance)
    ):
        yield scan_manager_instance

    _kill_scan_manager(scan_manager_instance)


@pytest.fixture(scope="session", autouse=True)
def disabled_scan_manager(session_mocker):
    """Completely disabled scan manager. Use when task manager is not required."""
    _manager = session_mocker.MagicMock()
    # session_mocker.patch("scanner.manager.Manager", _manager)
    session_mocker.patch("scanner.manager.SCAN_MANAGER", _manager)
    # session_mocker.patch("api.signal.scanjob_signal.manager.Manager", _manager)
    session_mocker.patch("api.signal.scanjob_signal.manager.SCAN_MANAGER", _manager)
    yield _manager


# @pytest.fixture(autouse=True)
# def _patch_scan_manager(scan_manager):
#     with (
#         patch.object(scan_manager.__class__, "__call__", _return_itself),
#         patch("api.signal.scanjob_signal.manager.Manager", scan_manager),
#         patch("api.signal.scanjob_signal.manager.SCAN_MANAGER", scan_manager),
#     ):
#         yield


@pytest.fixture(scope="session")
def django_client(live_server):
    """HTTP client which connects to django live server."""
    client = BaseUrlClient(
        base_url=urljoin(live_server.url, "api/v1/"),
    )
    return client
