#
# Copyright (c) 2017-2018 Red Hat, Inc.
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
from socket import gaierror
from pyVmomi import vim  # pylint: disable=no-name-in-module
from api.models import (ScanTask, SystemConnectionResult)
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

    def _store_connect_data(self, connected, credential):
        # Update the scan counts
        self.scan_task.update_stats(
            'INITIAL VCENTER CONNECT STATS.', sys_count=len(connected))

        for system in connected:
            sys_result = SystemConnectionResult(
                name=system, status=SystemConnectionResult.SUCCESS,
                credential=credential)
            sys_result.save()
            self.scan_task.connection_result.systems.add(sys_result)
            self.scan_task.increment_stats(
                sys_result.name, increment_sys_scanned=True)

        self.scan_task.connection_result.save()

    def run(self):
        """Scan network range ang attempt connections."""
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()
        try:
            connected = self.connect()
            self._store_connect_data(connected, credential)
        except vim.fault.InvalidLogin as vm_error:
            error_message = 'Unable to connect to VCenter source, %s,'\
                ' with supplied credential, %s.\n' % \
                (source.name, credential.name)
            error_message += 'Connect scan failed for %s. %s' %\
                (self.scan_task, vm_error)
            return error_message, ScanTask.FAILED
        except gaierror as error:
            error_message = 'Unable to connect to VCenter source %s.\n' %\
                source.name
            error_message += 'Reason for failure: %s' % error
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED

    # pylint: disable=too-many-locals
    def connect(self):
        """Execute the connect scan with the initialized source.

        :returns: list of connected vm credential tuples
        """
        vm_names = []

        vcenter = vcenter_connect(self.scan_task)
        container_view = get_vm_container(vcenter)
        vm_names = get_vm_names(container_view)

        return set(vm_names)
