"""Signal manager to handle scan triggering."""

import logging

import django.dispatch

from api import messages
from scanner import manager
from scanner.job import ScanJobRunner

logger = logging.getLogger(__name__)

PAUSE = "pause"
CANCEL = "cancel"
RESTART = "restart"


def handle_scan(sender, instance, **kwargs):
    """Handle incoming scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was triggered
    :param kwargs: Other args
    :returns: None
    """
    instance.log_message(messages.SIGNAL_STATE_CHANGE % "START")
    scanner = ScanJobRunner(instance)
    logger.info("Starting scan with MANAGER=%s", manager.SCAN_MANAGER)
    instance.queue()

    if not manager.SCAN_MANAGER:
        manager.reinitialize()

    if not manager.SCAN_MANAGER.is_alive():
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER.log_prefix,
            messages.SIGNAL_SCAN_MANAGER_CRASH,
        )
        manager.reinitialize()
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER.log_prefix,
            messages.SIGNAL_SCAN_MANAGER_RESTART,
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
    if action in [PAUSE, CANCEL]:
        manager.SCAN_MANAGER.kill(instance, action)


def scan_pause(sender, instance, **kwargs):
    """Pause a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    instance.log_message(messages.SIGNAL_STATE_CHANGE % "PAUSE")
    scan_action(sender, instance, PAUSE, **kwargs)


def scan_cancel(sender, instance, **kwargs):
    """Cancel a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    instance.log_message(messages.SIGNAL_STATE_CHANGE % "CANCEL")
    scan_action(sender, instance, CANCEL, **kwargs)


def scan_restart(sender, instance, **kwargs):
    """Restart a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    instance.log_message(messages.SIGNAL_STATE_CHANGE % "RESTART")
    scanner = ScanJobRunner(instance)

    if not manager.SCAN_MANAGER:
        manager.reinitialize()

    if not manager.SCAN_MANAGER.is_alive():
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER.log_prefix,
            messages.SIGNAL_SCAN_MANAGER_CRASH,
        )
        manager.reinitialize()
        logger.error(
            "%s: %s",
            manager.SCAN_MANAGER.log_prefix,
            messages.SIGNAL_SCAN_MANAGER_RESTART,
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
