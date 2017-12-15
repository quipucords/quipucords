#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTask used for vcenter connection task."""
import logging
from pyVmomi import vim  # pylint: disable=no-name-in-module
from api.models import (ScanTask, ConnectionResult, SystemConnectionResult)
from scanner.task import ScanTaskRunner
from scanner.vcenter.utils import vcenter_connect

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_vm_container(vcenter):
    """Get the container for virtual machines.

    :param vcenter: The vcenter object.
    :returns: The vm container object.
    """
    content = vcenter.RetrieveContent()
    container = content.rootFolder  # starting point to look into
    view_type = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive)
    return container_view


def get_vm_names(vm_container_view):
    """Get the vm names from the container view.

    :param vm_container_view: The VM container view.
    :returns: list of vm names.
    """
    vm_names = []
    children = vm_container_view.view
    for child in children:
        summary = child.summary
        vm_names.append(summary.config.name)
    return vm_names


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner vcenter connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of available virtual systems.
    """

    def __init__(self, scan_job, scan_task, conn_results):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        super().__init__(scan_job, scan_task)
        self.conn_results = conn_results

    def _store_connect_data(self, connected, credential):
        conn_result = ConnectionResult(source=self.scan_task.source,
                                       scan_task=self.scan_task)
        conn_result.save()

        for system in connected:
            sys_result = SystemConnectionResult(
                name=system, status=SystemConnectionResult.SUCCESS,
                credential=credential)
            sys_result.save()
            conn_result.systems.add(sys_result)

        conn_result.save()
        self.conn_results.save()
        self.conn_results.results.add(conn_result)
        self.conn_results.save()

        # Update the scan counts
        if self.scan_task.systems_count is None:
            self.scan_task.systems_count = len(connected)
            self.scan_task.systems_scanned = 0
        self.scan_task.systems_scanned = len(connected)
        self.scan_task.save()

    def get_results(self):
        """Access connection results."""
        if not self.results or not self.conn_results:
            # pylint: disable=no-member
            self.results = ConnectionResult.objects.filter(
                scan_task=self.scan_task.id).first()
        return self.results

    def run(self):
        """Scan network range ang attempt connections."""
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()
        try:
            connected = self.connect()
            self._store_connect_data(connected, credential)
        except vim.fault.InvalidLogin as vm_error:
            logger.error('Unable to connect to VCenter source, %s, '
                         'with supplied credential, %s.',
                         source.name, credential.name)
            logger.error('Connect scan failed for %s. %s', self.scan_task,
                         vm_error)
            return ScanTask.FAILED

        return ScanTask.COMPLETED

    # pylint: disable=too-many-locals
    def connect(self):
        """Execute the connect scan with the initialized source.

        :returns: list of connected vm credential tuples
        """
        vm_names = []
        logger.info('Connect scan started for %s.', self.scan_task)

        vcenter = vcenter_connect(self.scan_task)
        container_view = get_vm_container(vcenter)
        vm_names = get_vm_names(container_view)

        logger.info('Connect scan completed for %s.', self.scan_task)
        return set(vm_names)
