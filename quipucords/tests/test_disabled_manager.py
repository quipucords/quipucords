"""Test the DisabledManager class and its QPC_DISABLE_THREADED_SCAN_MANAGER setting."""

from unittest.mock import Mock

import pytest
from django.test import override_settings

from scanner import manager


@pytest.fixture(scope="module")
def scan_manager():
    """
    Override conftest.scan_manager pytest fixture to do nothing in this test module.

    This is necessary because conftest.scan_manager is set to autouse=True, which means
    it patches *all* tests, but we specifically *do not want* its patches applied here.
    """


def test_default_setting():
    """Assert the default manager class has not changed."""
    with override_settings(QPC_DISABLE_THREADED_SCAN_MANAGER=False):
        manager.reinitialize()
        assert isinstance(manager.SCAN_MANAGER, manager.Manager)
        assert manager.SCAN_MANAGER.__class__.__name__ == "Manager"


def test_disabled_setting():
    """Assert QPC_DISABLE_THREADED_SCAN_MANAGER replaces the default manager."""
    with override_settings(QPC_DISABLE_THREADED_SCAN_MANAGER=True):
        manager.reinitialize()
        assert isinstance(manager.SCAN_MANAGER, manager.DisabledManager)
        assert manager.SCAN_MANAGER.__class__.__name__ == "DisabledManager"


def test_disabled_manager_interface():
    """Assert DisabledManager implements a Manager-like interface."""
    disabled_manager = manager.DisabledManager()
    assert disabled_manager.is_alive()
    assert disabled_manager.kill(Mock(), Mock()) is None
    assert disabled_manager.start() is None
    assert disabled_manager.put(Mock()) is None
