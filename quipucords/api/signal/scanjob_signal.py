"""Signal manager to handle scan triggering."""

import logging

import django.dispatch

from api import messages
from scanner.job import ScanJobRunner
from scanner.manager import CeleryScanManager

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
    runner = ScanJobRunner(instance)
    instance.queue()
    CeleryScanManager.put(runner)


def scan_action(sender, instance, action, **kwargs):
    """Handle action on scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param action: The action to take on the scan (pause, cancel, resume)
    :param kwargs: Other args
    :returns: None
    """
    if action in [PAUSE, CANCEL]:
        CeleryScanManager.kill(instance)


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
    runner = ScanJobRunner(instance)
    CeleryScanManager.put(runner)


start_scan = django.dispatch.Signal()
pause_scan = django.dispatch.Signal()
cancel_scan = django.dispatch.Signal()
restart_scan = django.dispatch.Signal()

start_scan.connect(handle_scan)
pause_scan.connect(scan_pause)
cancel_scan.connect(scan_cancel)
restart_scan.connect(scan_restart)
