"""Signal manager to handle scan triggering."""

import logging

import django.dispatch
from django.utils.translation import gettext as _

from api import messages
from scanner.job import ScanJobRunner

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PAUSE = "pause"
CANCEL = "cancel"
RESTART = "restart"

# pylint: disable=W0613


def handle_scan(sender, instance, **kwargs):
    """Handle incoming scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was triggered
    :param kwargs: Other args
    :returns: None
    """
    from scanner import manager  # pylint: disable=import-outside-toplevel

    instance.log_message(_(messages.SIGNAL_STATE_CHANGE) % ("START"))
    scanner = ScanJobRunner(instance)
    instance.queue()
    if not manager.SCAN_MANAGER.is_alive():
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER_LOG_PREFIX,
            _(messages.SIGNAL_SCAN_MANAGER_CRASH),
        )
        manager.reinitialize()
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER_LOG_PREFIX,
            _(messages.SIGNAL_SCAN_MANAGER_RESTART),
        )
        manager.SCAN_MANAGER.start()
        # Don't add the scan as it will be picked up
        # by the manager startup, looking for pending/running scans.
    else:
        manager.SCAN_MANAGER.put(scanner)


def scan_action(sender, instance, action, **kwargs):
    """Handle action on scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param action: The action to take on the scan (pause, cancel, resume)
    :param kwargs: Other args
    :returns: None
    """
    from scanner import manager  # pylint: disable=import-outside-toplevel

    if action in [PAUSE, CANCEL]:
        manager.SCAN_MANAGER.kill(instance, action)


def scan_pause(sender, instance, **kwargs):
    """Pause a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    instance.log_message(_(messages.SIGNAL_STATE_CHANGE) % ("PAUSE"))
    scan_action(sender, instance, PAUSE, **kwargs)


def scan_cancel(sender, instance, **kwargs):
    """Cancel a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    instance.log_message(_(messages.SIGNAL_STATE_CHANGE) % ("CANCEL"))
    scan_action(sender, instance, CANCEL, **kwargs)


def scan_restart(sender, instance, **kwargs):
    """Restart a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    from scanner import manager  # pylint: disable=import-outside-toplevel

    instance.log_message(_(messages.SIGNAL_STATE_CHANGE) % ("RESTART"))
    scanner = ScanJobRunner(instance)

    if not manager.SCAN_MANAGER:
        manager.reinitialize()

    if not manager.SCAN_MANAGER.is_alive():
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER_LOG_PREFIX,
            _(messages.SIGNAL_SCAN_MANAGER_CRASH),
        )
        manager.reinitialize()
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER_LOG_PREFIX,
            _(messages.SIGNAL_SCAN_MANAGER_RESTART),
        )
        manager.SCAN_MANAGER.start()
        # Don't add the scan as it will be picked up
        # by the manager startup, looking for pending/running scans.
    else:
        manager.SCAN_MANAGER.put(scanner)


start_scan = django.dispatch.Signal()
pause_scan = django.dispatch.Signal()
cancel_scan = django.dispatch.Signal()
restart_scan = django.dispatch.Signal()

start_scan.connect(handle_scan)
pause_scan.connect(scan_pause)
cancel_scan.connect(scan_cancel)
restart_scan.connect(scan_restart)
