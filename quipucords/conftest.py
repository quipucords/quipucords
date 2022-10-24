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
def scan_manager(mocker):
    """
    Scan manager fixture.

    If started, ensure its proper teardown.
    """
    from scanner import manager

    # mocker.patch.object(manager.Manager, "__call__", _return_itself),
    mocker.patch.object(manager, "sleep"),
    mocker.patch.object(manager, "Timer")
    _instance = manager.Manager()
    mocker.patch.object(manager, "SCAN_MANAGER", _instance),
    mocker.patch("api.signal.scanjob_signal.manager.SCAN_MANAGER", _instance)
    yield _instance

    _instance.stop()
    _kill_scan_manager(_instance)


@pytest.fixture(scope="class", autouse=True)
def disabled_scan_manager(class_mocker):
    """Completely disabled scan manager. Use when task manager is not required."""
    _manager = class_mocker.MagicMock()
    class_mocker.patch("scanner.manager.Manager", _manager)
    class_mocker.patch("scanner.manager.SCAN_MANAGER", _manager)
    class_mocker.patch("api.signal.scanjob_signal.manager.Manager", _manager)
    class_mocker.patch("api.signal.scanjob_signal.manager.SCAN_MANAGER", _manager)
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
